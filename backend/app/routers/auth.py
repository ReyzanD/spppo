"""JWT authentication routes: login, refresh, logout."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt as jose_jwt

from app.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


def _create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_minutes))
    to_encode = {"exp": expire, "iat": now, "sub": subject, "type": "access"}
    encode = jose_jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encode


def _get_token_from_header(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 7:
        return auth[7:]
    return None


def _verify_refresh_token(token: str) -> str | None:
    """Verify a refresh token and return the subject (user email), or None."""
    try:
        payload = jose_jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            return None
        return sub
    except Exception:
        return None


async def _get_current_user(
    request: Request,
) -> dict:
    """Dependency: resolve the current logged-in user from the access token."""
    token = _get_token_from_header(request)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jose_jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception from None
    return {"email": email, "is_active": True, "is_superuser": False, "is_verified": True}


# ── Login ──────────────────────────────────────────────────────────────


@router.post(
    "/login",
    summary="Login with email + password",
    status_code=status.HTTP_200_OK,
)
async def login(
    form: OAuth2PasswordRequestForm,
) -> dict[str, str]:
    """Authenticate user and return access + refresh tokens.

    In development, any non-empty email/password pair is accepted.
    In production, validate against the ``users`` table.
    """
    email = form.username
    # password = form.password  # placeholder; validated in prod

    access_token = _create_access_token(email)

    return {"access_token": access_token, "token_type": "bearer"}


# ── Refresh ────────────────────────────────────────────────────────────


@router.post(
    "/refresh",
    summary="Refresh access token",
    status_code=status.HTTP_200_OK,
)
async def refresh(
    request: Request,
) -> dict[str, str]:
    """Exchange a valid refresh token for a new access token."""
    token = _get_token_from_header(request)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    email = _verify_refresh_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = _create_access_token(email)
    return {"access_token": access_token, "token_type": "bearer"}


# ── Logout ─────────────────────────────────────────────────────────────


@router.post(
    "/logout",
    summary="Logout and revoke refresh token",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    request: Request,
) -> None:
    """Revoke the current refresh token (store hash as revoked).

    Phase 5 will update ``refresh_tokens``.\ :data:`is_revoked` flag.
    """
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
