from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from adapter import Destination


class ReadRegionProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            Destination.parse(
                credentials["service_origin"], credentials["service_ips"]
            )
            Destination.parse(
                credentials["file_origin"], credentials["file_ips"]
            )
            if (
                len(credentials["service_token"]) < 32
                or not credentials["app_id"]
                or not credentials["file_prefix"].startswith("/files/")
            ):
                raise ValueError("credentials")
        except Exception:
            raise ToolProviderCredentialValidationError(
                "INVALID_CONFIGURATION"
            ) from None
