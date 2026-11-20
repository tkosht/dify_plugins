# Region OCR tools — guarded transport

This independent Tool package is non-operational on unsupported stock tool transports: the context resolver raises `CONTEXT_REQUIRED` before network I/O. It never substitutes a session/conversation/message ID for a workflow run. Package/schema validity does not establish this transport integration.

The separately generated `read_region_agent` package supplies a dedicated Agent strategy integration. It reuses the same HTTP adapter and strict six-argument contract; it does not relax this Tool package's guard. Preparation/cleanup in that strategy are fixed programmatic steps outside model choices.

No URL, credential or execution context is accepted as a model argument. Approved HTTPS origins/IP pins, TLS verification and file-path constraints remain enforced. No crop image is returned as model visual input. See the parent project guide and validation report for scope, setup and rollback.
