import hmac

from fastapi import Header, HTTPException, status

from src.config import settings


def _extract_token(authorization: str) -> str:
    value = authorization.strip()
    if not value:
        return ""

    if value.lower().startswith("bearer "):
        return value[7:].strip()

    return value


async def verify_api_key(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    token = _extract_token(authorization)
    if not token or not hmac.compare_digest(token, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
