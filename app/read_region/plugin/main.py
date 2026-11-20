import logging

from dify_plugin import DifyPluginEnv, Plugin

# Suppress SDK TCP payload logging; errors returned by this plugin are sanitized.
logging.getLogger("dify_plugin.core.server.tcp.request_reader").disabled = True

plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120, MAX_WORKER=4))
if __name__ == "__main__":
    plugin.run()
