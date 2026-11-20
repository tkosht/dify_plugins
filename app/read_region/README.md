# Read Region: OCR service, guarded tools and dedicated Agent strategy

A reusable internal PNG/JPEG OCR service with two separately installable Dify packages. Only the dedicated Agent strategy has an execution-context integration path. The independent tool package retains its fail-closed guard on unsupported transports.

| Package | Purpose | Context boundary |
|---|---|---|
| `read_region-0.2.0.difypkg` | Independent `prepare_images`, `read_region`, `cleanup_images` tools | Stock tool invocations return `CONTEXT_REQUIRED`; no conversation/session substitution |
| `read_region_agent-0.2.0.difypkg` | Dedicated `region_ocr` Agent strategy | SDK application identity plus the workflow's system run binding; only six region arguments reach model tool calls |

Validation used a task-owned Dify1.18.0 installation, the standard SDK model-provider path, a deterministic local fake provider and real Tesseract OCR. This proves the tested orchestration path, not real-model reasoning, representative accuracy or production rollout. No Dify core/SDK patch, external OCR or paid model API is required by that path. See [verification/results.md](verification/results.md) for acceptance scope and current evidence. The [Chatflow template](verification/verified-chatflow.template.json) is a modified projection of an authenticated draft, **not an import-tested official export**: the export call returned400, while draft retrieval returned200.

## Build and local checks

From repository root:

```sh
uv sync --project app/read_region --frozen
uv run --project app/read_region pytest app/read_region/tests -c app/read_region/pyproject.toml
uv run --project app/read_region ruff check app/read_region
uv run --project app/read_region black --check --config pyproject.toml app/read_region
```

With the official CLI0.6.10 at `app/read_region/.local-bin/dify`, generate fresh, category-exclusive overlays from the single canonical `plugin/` source tree. Destination directories must not already exist:

```sh
uv run --project app/read_region python app/read_region/scripts/build_plugin.py \
  --kind tool --destination app/read_region/.package-build/tool-release \
  --package app/read_region/read_region-0.2.0.difypkg
uv run --project app/read_region python app/read_region/scripts/build_plugin.py \
  --kind agent --destination app/read_region/.package-build/agent-release \
  --package app/read_region/read_region_agent-0.2.0.difypkg
uv run --project app/read_region python app/read_region/scripts/check_package.py \
  app/read_region/read_region-0.2.0.difypkg
uv run --project app/read_region python app/read_region/scripts/check_package.py \
  app/read_region/read_region_agent-0.2.0.difypkg
```

The daemon requires a single plugin category. Shared adapter/validation/strategy code is copied by the builder, never maintained as a second implementation. The old0.1 package and dated evidence are historical candidates.

## Service and private runtime setup

Build the OCR service with `docker build -t read-region-ocr app/read_region`. Models are fetched only at build time and checked against `models.lock.json`; missing/mismatched runtime models fail closed. Run one service worker, with a private credential-file mount, persistent state mount, private temporary storage, appropriate resource limits and an approved internal TLS frontend. The service's Dockerfile exposes container port8000; do not publish it publicly. Apply egress restrictions to this service without changing shared Dify networking.

Service credentials are a private JSON mapping from application scope to distinct random tokens of at least32 characters, supplied through `READ_REGION_CREDENTIALS_FILE`. Keep state across restarts: durable revocation prevents old executions resetting their TTL/budget. `Limits` in `service/core.py` owns the service defaults.

The Agent process requires `READ_REGION_STRATEGY_CONFIG_FILE` pointing to a private JSON file matching [config/strategy-config.schema.json](config/strategy-config.schema.json). Each application entry contains only adapter configuration: matching app ID, fixed HTTPS OCR/file origins, approved literal IP pins, file path prefix and service token. Keep it outside Git/packages, readable only by the runtime. No model endpoint or model key belongs in that file.

Trust the organization's approved CA in this process, for example through `SSL_CERT_FILE`. The adapter preserves certificate/hostname verification, pins approved IPs, restricts file paths and follows no redirects. Dify must supply file URLs matching that approved HTTPS file origin; the validation environment used its own `INTERNAL_FILES_URL` configuration. Do not infer or change another deployment's settings.

The tested remote-runtime launch uses the generated Agent overlay and the standard SDK. Supply remote SDK settings through a separate private environment file, never shell `source`, prompts or node inputs:

```sh
cd app/read_region/.package-build/agent-release
uv run --env-file /approved/private/agent-runtime.env --project ../../plugin python -m main
```

That private environment selects remote installation and supplies the approved daemon address/debug key, `READ_REGION_STRATEGY_CONFIG_FILE` and CA path. Remote debug registration is temporary and ends with the process. A packaged install into a daemon-managed runtime still needs an operator-supported private-config mount/environment mechanism; that production deployment is not established by the sandbox test.

## Dify Agent configuration and rollback

Choose provider `tkosht/read_region_agent/region_ocr`, strategy `region_ocr`. Configure `workflow_run_id` directly from `sys.workflow_run_id`, `query` from the intended query, authorized image files, and the normal Dify model selector for a tool-calling model. App identity comes from the SDK session, not a parameter. User/model values must never replace the system run binding. Model credentials remain in Dify's configured provider path.

Preparation and cleanup run as fixed strategy code before and after the model loop, rather than as separate Chatflow nodes. The model can choose only `read_region(image_id,x_min,y_min,x_max,y_max,scale)`. Strict validation occurs before dispatch; finally-cleanup covers failures. This placement differs from the original separate-node proposal. The JSON result retains bounded non-content overview/region source references alongside the answer.

Use a duplicated validation app first. Roll back by restoring its prior workflow/strategy and stopping only the owned remote Agent/OCR processes. Remove a package only after checking its consumers. Retire private configuration/state under the operator's retention policy after continuations end. Service deletion does not delete Dify attachments, conversations, execution logs, provider or observability copies.

The sandbox's native execution IDs can appear in Dify execution metadata. Service/model credentials and private assertions must not enter model prompts or normal node values. OCR text is sent to the selected Dify model and may be retained by Dify/provider logs. Production retention, target compatibility and representative B0/B1/T quality remain separate acceptance work; no accuracy improvement or confidential-data safety guarantee is claimed.
