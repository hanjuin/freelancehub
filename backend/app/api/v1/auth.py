from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_freelancer
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.crud.crud_freelancer import crud_freelancer
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _make_token_response(freelancer_id: str, raw_refresh: str) -> TokenResponse:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(subject=freelancer_id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        refresh_token=raw_refresh,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    obj_in: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Check email uniqueness
    existing = await crud_freelancer.get_by_email(db, obj_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    # Check username uniqueness
    existing_username = await crud_freelancer.get_by_username(db, obj_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    freelancer = await crud_freelancer.create_with_password(db, obj_in=obj_in)

    # Issue refresh token
    raw_refresh = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await crud_freelancer.create_refresh_token(
        db,
        freelancer_id=freelancer.id,
        token=raw_refresh,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    return _make_token_response(str(freelancer.id), raw_refresh)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    freelancer = await crud_freelancer.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not freelancer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not freelancer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Issue refresh token
    raw_refresh = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await crud_freelancer.create_refresh_token(
        db,
        freelancer_id=freelancer.id,
        token=raw_refresh,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=request.client.host if request and request.client else None,
    )

    return _make_token_response(str(freelancer.id), raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token_hash = hash_token(body.refresh_token)
    rt = await crud_freelancer.get_refresh_token_by_hash(db, token_hash)
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    now = datetime.now(timezone.utc)
    if rt.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Revoke old token (rotation)
    await crud_freelancer.revoke_refresh_token(db, token=rt)

    # Issue new refresh token
    raw_refresh = create_refresh_token()
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await crud_freelancer.create_refresh_token(
        db,
        freelancer_id=rt.freelancer_id,
        token=raw_refresh,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    return _make_token_response(str(rt.freelancer_id), raw_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    token_hash = hash_token(body.refresh_token)
    rt = await crud_freelancer.get_refresh_token_by_hash(db, token_hash)
    if rt and rt.freelancer_id == current_freelancer.id:
        await crud_freelancer.revoke_refresh_token(db, token=rt)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    await crud_freelancer.revoke_all_refresh_tokens(db, freelancer_id=current_freelancer.id)
    return MessageResponse(message="All sessions revoked")


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    import secrets

    freelancer = await crud_freelancer.get_by_email(db, body.email)
    if freelancer:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await crud_freelancer.create_password_reset_token(
            db,
            freelancer_id=freelancer.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        # In production: send email with raw_token link
        # e.g. f"{settings.APP_BASE_URL}/reset-password?token={raw_token}"
    # Always return OK to prevent email enumeration
    return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    token_hash = hash_token(body.token)
    prt = await crud_freelancer.get_valid_password_reset_token(db, token_hash)
    if not prt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    new_hashed = hash_password(body.new_password)
    await crud_freelancer.use_password_reset_token(
        db, token=prt, new_hashed_password=new_hashed
    )
    return MessageResponse(message="Password reset successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_freelancer: Freelancer = Depends(get_current_active_freelancer),
) -> MessageResponse:
    if not verify_password(body.current_password, current_freelancer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    new_hashed = hash_password(body.new_password)
    current_freelancer.hashed_password = new_hashed
    db.add(current_freelancer)
    await db.commit()
    return MessageResponse(message="Password changed successfully")
