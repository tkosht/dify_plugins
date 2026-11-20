Development environment observed 2026-11-13:

- Repository base: 2388e1b94dada49286e28b468e5e15dec473efb8.
- Python test runtime: CPython 3.12.16 (uv managed); container Python 3.12.12.
- Runtime dependencies: uv.lock and requirements.lock.txt; plugin has its own lock.
- OCR: Tesseract 5.3.0 Debian package 5.3.0-2; CPU LSTM; jpn+eng, tessdata_fast 4.1.0 commit and SHA256 in models.lock.json; Apache-2.0.
- Geometry: Pillow 13.0.0, EXIF-normalized RGB, white alpha composite, LANCZOS, no generated image content. Coordinates refer to the normalized original.
- Tesseract psm6/oem1: no OSD/orientation correction; TSV word rectangles in input pixels. Full transformed input dimensions are in real_ocr.json. Native internal sampling/resolution behavior is not instrumented; scale alone is not claimed to improve resolution or quality. Empty detected word boxes are retained with needs_review.
- Docker daemon 29.9.2. Cgroup memory/pids flags failed because this environment uses a threaded cgroup domain. The executed offline smoke used network none, read-only root, cap-drop ALL, no-new-privileges, tmpfs and child RLIMIT_AS/CPU/FSIZE. This is not a production resource acceptance.
- Packaging CLI: official dify-plugin-daemon 0.6.10 linux-amd64. Expected binary SHA256 0cef74bcae375a4337c2ff7d42e4787717981a795e1c23cf56bb27ec07ec8304. Package built by actual CLI; target daemon installation remains unperformed.
- Real Dify/API/worker/web/plugin daemon, Agent strategy, provider/model, credentials and file endpoints: not accessed or verified. Dify 1.18.0 is the intended target, not an observed deployment version. No DSL export or image-to-model claim is provided.
