# Dify Vertex AI Nano Banana Image Tool Plugin Design

## Goal

Build a custom Dify plugin in `tkosht/dify_plugins` that generates/edits images with Google Vertex AI Gemini image models, especially Nano Banana Pro.

Primary target:

- Model: `gemini-3-pro-image`
- Secondary model: `gemini-3.1-flash-image`
- Product name: Gemini 3 Pro Image / Nano Banana Pro
- Runtime: self-hosted Dify on Linux with Docker Compose
- Auth mode 1: existing Gemini API key flow, matching Dify `tools/gemini_image`
- Auth mode 2: Vertex AI flow, matching Dify `models/vertex_ai`

The user has already verified a direct Python SDK call against Google image generation. If that test used an older preview endpoint, treat it as environment evidence only and rerun the minimum test with `gemini-3-pro-image`.

## Recommended Plugin Shape

Use a **Dify Tool plugin**, not primarily a Dify model-provider plugin.

Reason:

- Dify's official `models/vertex_ai` plugin has some image-generation handling inside its LLM provider implementation, but it is still exposed as `supported_model_types: llm, text-embedding`.
- Dify workflows usually handle image generation more naturally as a tool that returns image blobs/files.
- Dify official repo already has `tools/gemini_image`, which returns generated images via `create_blob_message()`, but that tool uses Gemini API key / Developer API style, not Vertex AI service account / ADC style.

Recommended implementation pattern:

- Copy the structural idea from `tools/gemini_image`.
- Keep the existing Gemini API key authentication from `tools/gemini_image`.
- Add the Vertex AI authentication design from `models/vertex_ai` with the same credential field names and behavior.
- Implement calls through `google-genai` with `vertexai=True`.

## Official References To Inspect

Use these as starting points:

- Dify official Vertex AI provider:
  - `https://github.com/langgenius/dify-official-plugins/tree/main/models/vertex_ai`
  - Provider schema: `models/vertex_ai/provider/vertex_ai.yaml`
  - LLM implementation: `models/vertex_ai/models/llm/llm.py`
- Dify official Gemini image tool:
  - `https://github.com/langgenius/dify-official-plugins/tree/main/tools/gemini_image`
  - Tool implementation: `tools/gemini_image/tools/image_generate.py`
  - Tool schema: `tools/gemini_image/tools/image_generate.yaml`
- Google model docs:
  - `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-pro-image`
  - `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-image`
  - `https://ai.google.dev/gemini-api/docs/changelog`
  - `https://ai.google.dev/gemini-api/docs/deprecations`

## Models To Support

Expose these current GA model IDs:

| Label | Model ID | Status | Location |
| --- | --- | --- | --- |
| Nano Banana Pro | `gemini-3-pro-image` | GA | `global` |
| Nano Banana 2 | `gemini-3.1-flash-image` | GA | `global` |

Important model-ID note:

- Google Cloud docs list `gemini-3-pro-image` and `gemini-3.1-flash-image` as GA models released on 2026-05-28.
- Google AI for Developers changelog says the GA IDs replaced the older preview endpoints.
- If Dify official plugin definitions still show preview IDs, treat those definitions as lagging compatibility examples, not as the desired default for this plugin.
- Do not expose preview model IDs unless a separate compatibility requirement is explicitly opened.

## Authentication Requirements

Support both existing API key auth and the Dify Vertex AI provider auth pattern.

### Mode A: Existing Gemini API Key

This matches Dify official `tools/gemini_image`.

Dify provider credentials:

- `api_key`, required secret input when Vertex AI credentials are not configured

Behavior:

- Use the Gemini API key request style for this mode.
- Keep compatibility with the current `tools/gemini_image` behavior for generated image blobs and text parts.
- Treat the key as a secret. Do not print it, log it, or include it in errors.

### Mode B: Vertex AI Service Account Key

This matches Dify official `models/vertex_ai` credential behavior.

Dify provider credentials, using the same field names:

- `vertex_project_id`
- `vertex_location`
- `vertex_service_account_key`, optional secret input, base64-encoded service account key JSON

If `vertex_service_account_key` is provided:

- base64 decode it
- parse JSON
- create credentials with `google.oauth2.service_account.Credentials.from_service_account_info(...)`
- pass credentials into `genai.Client(...)`

Important:

- This is key-based auth.
- Follow Dify Vertex AI's pattern: service account key is a secret input in base64 format.
- Do not log the decoded JSON, base64 value, access token, or credential object.
- Use a dedicated, limited service account, not Owner/Editor.

### Mode C: Vertex AI ADC / WIF

This is the target long-term shape.

If `vertex_service_account_key` is empty:

- do not load any key JSON
- construct `genai.Client(vertexai=True, project=..., location=...)` without explicit credentials
- let Google Application Default Credentials resolve auth from the plugin runtime environment

For WIF later, Dify `plugin_daemon` should get:

```yaml
services:
  plugin_daemon:
    environment:
      GOOGLE_APPLICATION_CREDENTIALS: /var/run/google/wif.json
    volumes:
      - ./secrets/wif.json:/var/run/google/wif.json:ro
```

Do not put WIF credential configuration JSON into the `Service Account Key` field unless you intentionally implement `google.auth.load_credentials_from_dict()`. The Dify official Vertex AI plugin's key field is for service account key JSON, not WIF config JSON.

## Minimal Python Call Pattern

Use this shape inside the tool after adapting to Dify plugin APIs:

```python
import base64
import json
from google import genai
from google.genai import types
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]


def make_client(credentials: dict) -> genai.Client:
    api_key = (credentials.get("api_key") or "").strip()
    project_id = (credentials.get("vertex_project_id") or "").strip()
    location = credentials.get("vertex_location") or "global"
    key_b64 = credentials.get("vertex_service_account_key") or ""

    if not project_id:
        return genai.Client(api_key=api_key)

    if key_b64:
        info = json.loads(base64.b64decode(key_b64))
        google_credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES,
        )
        return genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=google_credentials,
        )

    return genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )


def generate_image(client: genai.Client, prompt: str, model: str, aspect_ratio: str, image_size: str):
    return client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                image_size=image_size,
                aspect_ratio=aspect_ratio,
            ),
        ),
    )
```

## Dify Tool Behavior

Expected tool parameters:

- `prompt`: string, required
- `model`: select, default `gemini-3-pro-image`
- `aspect_ratio`: select, default `1:1`
- `resolution`: select, default `1K`
- `images`: optional files input, for image editing / reference images

Suggested options:

- `aspect_ratio`: `1:1`, `3:2`, `2:3`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- `resolution`: `1K`, `2K`, `4K`

Output:

- return text parts as text messages
- return image `inline_data` parts as Dify blob/file messages, probably PNG
- use `create_blob_message(...)` similar to Dify official `tools/gemini_image`

Implementation hint:

- Prefer returning a blob/file tool output over representing the image as an LLM message content part.
- This makes the workflow easier to chain into downstream image/file nodes.

## Pricing Notes

Nano Banana Pro standard PayGo:

- image output:
  - 1K / 2K: 1120 output image tokens, about `$0.134` per image
  - 4K: 2000 output image tokens, about `$0.24` per image
- input reference image:
  - 560 input image tokens, about `$0.0011` per image

Add text input/output and reasoning charges where applicable.

Start tests at 1K.

## User-Reported Direct Test Evidence

This section is evidence to guide implementation, not a claim that Dify is already working.

The user already ran a Python script outside Dify and successfully generated an image. If the older test used a preview ID, rerun a small direct or Dify-side test with the GA ID:

- `nano-banana-pro-test.png`
- model: `gemini-3-pro-image`
- location: `global`
- output: 1K image

If confirmed, this means:

- Google Cloud project billing is working
- Vertex AI API is enabled
- service account authentication works
- IAM is sufficient for the tested call
- the tested model ID is usable from the project

## Development Plan

1. Create plugin skeleton in `tkosht/dify_plugins`.
2. Use tool plugin structure, likely named `vertex_nano_banana_image` or similar.
3. Add provider credential schema for both auth families:
   - `api_key` for existing Gemini Developer API key mode
   - `vertex_project_id`
   - `vertex_location`
   - `vertex_service_account_key`, optional secret input
4. Add tool schema:
   - `prompt`
   - `model`
   - `aspect_ratio`
   - `resolution`
   - optional image files
5. Implement client creation:
   - Gemini API key mode, matching Dify `tools/gemini_image`
   - service account key if provided
   - ADC otherwise for Vertex AI mode
6. Implement text-to-image first.
7. Add image/reference input support second.
8. Package `.difypkg`.
9. Install in self-hosted Dify.
10. Test first with `gemini-3-pro-image`, `global`, `1K`, `1:1`.
11. Test `gemini-3.1-flash-image` separately if Nano Banana 2 support is required.
12. After plugin works, test ADC/WIF mode by leaving key empty and configuring `plugin_daemon`.

## Items That Must Be Explicitly Reported

These items still need investigation during implementation. Report each one explicitly in the implementation or completion report instead of leaving it implicit.

1. Exact Dify SDK version in the user's self-hosted Dify and plugin daemon.
   - The official Vertex plugin currently depends on `dify_plugin>=0.9.0`.
   - Confirm compatibility with the target Dify version.

2. Exact Dify tool file-output API shape.
   - Confirm whether `create_blob_message(...)` is still the best output for image files in the installed Dify version.
   - Use official `tools/gemini_image` as the first reference.

3. Exact model IDs that work in the target project.
   - Test `gemini-3-pro-image` as the primary GA endpoint.
   - Test `gemini-3.1-flash-image` if Nano Banana 2 support is required.
   - Do not use preview endpoints for new implementation.

4. Image editing / reference image support in Vertex AI SDK.
   - Text-to-image is already proven.
   - Need to map Dify file inputs into `inline_data` parts for image editing/reference-image use.

5. Whether the selected model supports all desired `aspect_ratio` / `resolution` values through the exact installed `google-genai` version.
   - The direct test worked for 1K.
   - Validate 2K and 4K separately.

6. Dify UI behavior for tool outputs.
   - Confirm how generated image blobs appear in workflow outputs and whether downstream nodes can consume them directly.

7. Packaging/signature constraints for self-hosted Dify.
   - Confirm whether plugin signature verification is enabled.
   - If enabled, document the install path or signing/trust-key process.

8. Validation strategy.
   - Do not reuse Dify official Vertex AI plugin's old validation model `gemini-1.0-pro-002`.
   - Use a current image model, or avoid expensive image generation during provider validation and validate lazily in the tool call.

9. WIF final design.
   - If Workload Identity Federation support is added later, document the validated trust boundary and token-source design without environment-specific infrastructure details.
   - Keep deployment-specific network or authentication notes in private operations documentation rather than this public plugin design.

10. Safety/error handling.
   - Handle responses where Google returns a text `finish_message` and no image.
   - Surface that message to Dify rather than treating it as a transport/auth failure.

## Error Handling Hints

If Google returns:

```text
Unable to show the generated image. The model could not generate the image based on the prompt provided. You will not be charged for this request.
```

Treat it as:

- API/auth/model call succeeded
- image candidate was not generated for that prompt
- not necessarily billable
- return a clear text message to the workflow user

It should not be reported as IAM/API/key failure.

## Security Hints

- Treat `api_key` and `vertex_service_account_key` as Dify secret inputs.
- Never log the Gemini API key, service account key JSON, base64 value, access tokens, or full credential object.
- Keep service account role limited; initial tested role was `roles/aiplatform.user`.
- Plan to revoke the service account key after WIF/ADC mode is working.
- If the tool supports arbitrary installed Dify users, remember that credentials configured at plugin provider level can become a shared operational boundary.
