import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(authorization: str) -> str:
    value = authorization.strip()
    if not value:
        return ""

    if value.lower().startswith("bearer "):
        return value[7:].strip()

    return value


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    token = credentials.credentials
    if not token or not hmac.compare_digest(token, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
