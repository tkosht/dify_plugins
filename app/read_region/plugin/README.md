# Region OCR tool candidate

This plugin is non-operational on stock Dify: its context resolver always raises CONTEXT_REQUIRED before any network request. Installation/manifest validity does not establish functional integration. Do not use production documents.

Only read_region belongs in an Agent tool list. prepare_images and cleanup_images are fixed pre/post node tools. No execution ID, credential, URL, engine or destination is accepted as an LLM argument. All file/service HTTP requests use configured pinned HTTPS destinations. No crop image is returned to a model.

See the parent app/read_region/README.md for service setup, limitations, evidence and rollback. A reviewed transport extension and actual P0 checks are required before making this plugin operational; there is no environment/form bypass.
