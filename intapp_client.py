import time
import httpx


class IntappClient:
    """HTTP client for Intapp Open APIs with automatic OAuth token refresh."""

    def __init__(self, token_url: str, client_id: str, client_secret: str, base_url: str):
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in
        return self._access_token

    async def get(self, path: str, params: dict | None = None) -> dict:
        token = await self._ensure_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/{path.lstrip('/')}",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, body: dict) -> dict:
        token = await self._ensure_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/{path.lstrip('/')}",
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def patch(self, path: str, body: dict) -> dict:
        token = await self._ensure_token()
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self._base_url}/{path.lstrip('/')}",
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()
