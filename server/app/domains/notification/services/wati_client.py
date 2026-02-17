"""
WATI API client for sending WhatsApp template messages.

Uses WATI v1 API: POST /api/v1/sendTemplateMessages
- template_name, broadcast_name, channel_number, receivers (whatsappNumber + customParams)
"""

import httpx
from typing import Any

from app.shared.logging import get_logger
from app.shared.utils.phone import normalize_phone_to_e164

logger = get_logger(__name__)


class WATIClient:
    """
    Client for WATI Business API (WhatsApp template messages).
    """

    def __init__(
        self,
        base_url: str,
        bearer_token: str,
        channel_number: str,
        default_phone_country_code: str = "91",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.channel_number = normalize_phone_to_e164(
            channel_number, default_country_code=default_phone_country_code
        ) or channel_number
        self.default_phone_country_code = default_phone_country_code

    def _headers(self) -> dict[str, str]:
        token = self.bearer_token
        if token and not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        return {
            "Authorization": token,
            "Content-Type": "application/json",
        }

    async def send_template(
        self,
        template_name: str,
        whatsapp_number: str,
        parameters: list[dict[str, str]],
        broadcast_name: str = "notification",
    ) -> dict[str, Any] | None:
        """
        Send a template message to one recipient.

        Args:
            template_name: WATI template name (elementName), e.g. "welcome"
            whatsapp_number: Recipient phone in E.164 (e.g. 919876543210)
            parameters: List of {"name": "var_name", "value": "value"} for template variables
            broadcast_name: Optional label for WATI analytics

        Returns:
            Response JSON or None on failure
        """
        url = f"{self.base_url}/api/v1/sendTemplateMessages"
        body = {
            "template_name": template_name,
            "broadcast_name": broadcast_name,
            "channel_number": self.channel_number,
            "receivers": [
                {
                    "whatsappNumber": normalize_phone_to_e164(
                        whatsapp_number,
                        default_country_code=self.default_phone_country_code,
                    ) or "".join(c for c in whatsapp_number if c.isdigit()),
                    "customParams": [{"name": p["name"], "value": str(p["value"])} for p in parameters],
                }
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=body, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                logger.info(
                    "WATI template sent",
                    extra={
                        "template": template_name,
                        "to": whatsapp_number[:6] + "***",
                        "result": data.get("result"),
                    },
                )
                return data
        except httpx.HTTPStatusError as e:
            logger.error(
                f"WATI API error: {e.response.status_code}",
                extra={
                    "template": template_name,
                    "status": e.response.status_code,
                    "body": (e.response.text or "")[:500],
                },
            )
            return None
        except Exception as e:
            logger.exception("WATI send failed", extra={"template": template_name, "error": str(e)})
            return None
