# Region OCR Agent — validation candidate

This strategy-only package is generated from shared canonical source by `scripts/build_plugin.py`. Identity: `tkosht/read_region_agent`; provider: `tkosht/read_region_agent/region_ocr`; strategy: `region_ocr`. The separate `tkosht/read_region` Tool package retains its unsupported-context guard. The daemon permits one category per package.

Bind `workflow_run_id` directly to `sys.workflow_run_id`. Supply the intended query, authorized image files and a normal Dify tool-calling model selector. App identity comes only from the SDK session. Private `READ_REGION_STRATEGY_CONFIG_FILE` maps that app to fixed HTTPS OCR/file origins, literal IP pins, file prefix and service credential. It contains no model endpoint/key. Use the runtime's approved CA trust without disabling TLS checks.

Preparation and cleanup execute deterministically inside this strategy, outside model choices. They are not separate Chatflow pre/post nodes. The model sees only the six `read_region` arguments. Returned JSON includes bounded non-content overview/region references, including the zero-region-call case. Errors preserve a primary failure and explicitly flag cleanup failure.

Validation used standard Dify1.18.0 and SDK model-provider calls with a deterministic local fake provider and real OCR. This demonstrates orchestration only. No Dify core/SDK patch or paid model API was used. Production managed-runtime configuration, compatibility with another deployment, confidential-data security and representative quality remain unaccepted. OCR text is sent to the selected model; native run metadata and Dify/provider retention must be accounted for separately.

See the parent project guide for service startup, remote-runtime configuration, packaging and rollback. No private environment file, credential, signed URL or real deployment ID is included in this package.
