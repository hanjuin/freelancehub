from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import Freelancer, PasswordResetToken, RefreshToken  # noqa: E402

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.crud.base import CRUDBase
from app.schemas.auth import RegisterRequest
from app.schemas.freelancer import FreelancerUpdate


class CRUDFreelancer(CRUDBase[Freelancer, RegisterRequest, FreelancerUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Freelancer | None:
        result = await db.execute(
            select(Freelancer).where(Freelancer.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Freelancer | None:
        result = await db.execute(
            select(Freelancer).where(Freelancer.username == username.lower())
        )
        return result.scalar_one_or_none()

    async def create_with_password(
        self, db: AsyncSession, *, obj_in: RegisterRequest
    ) -> Freelancer:
        freelancer = Freelancer(
            email=obj_in.email.lower(),
            hashed_password=hash_password(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            username=obj_in.username.lower(),
        )
        db.add(freelancer)
        await db.commit()
        await db.refresh(freelancer)
        return freelancer

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Freelancer | None:
        freelancer = await self.get_by_email(db, email)
        if not freelancer:
            return None
        if not verify_password(password, freelancer.hashed_password):
            return None
        return freelancer

    async def create_refresh_token(
        self,
        db: AsyncSession,
        *,
        freelancer_id: uuid.UUID,
        token: str,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshToken:
        from app.core.security import hash_token

        rt = RefreshToken(
            freelancer_id=freelancer_id,
            token_hash=hash_token(token),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(rt)
        await db.commit()
        await db.refresh(rt)
        return rt

    async def get_refresh_token_by_hash(
        self, db: AsyncSession, token_hash: str
    ) -> RefreshToken | None:
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.is_used.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self, db: AsyncSession, *, token: RefreshToken
    ) -> None:
        token.is_revoked = True
        db.add(token)
        await db.commit()

    async def revoke_all_refresh_tokens(
        self, db: AsyncSession, *, freelancer_id: uuid.UUID
    ) -> None:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.freelancer_id == freelancer_id)
            .values(is_revoked=True)
        )
        await db.commit()

    async def create_password_reset_token(
        self,
        db: AsyncSession,
        *,
        freelancer_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        prt = PasswordResetToken(
            freelancer_id=freelancer_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(prt)
        await db.commit()
        await db.refresh(prt)
        return prt

    async def get_valid_password_reset_token(
        self, db: AsyncSession, token_hash: str
    ) -> PasswordResetToken | None:
        from datetime import timezone

        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.is_used.is_(False),
                PasswordResetToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def use_password_reset_token(
        self,
        db: AsyncSession,
        *,
        token: PasswordResetToken,
        new_hashed_password: str,
    ) -> None:
        token.is_used = True
        db.add(token)
        # Update freelancer's password
        await db.execute(
            update(Freelancer)
            .where(Freelancer.id == token.freelancer_id)
            .values(hashed_password=new_hashed_password)
        )
        await db.commit()

    async def verify_email(
        self, db: AsyncSession, *, freelancer: Freelancer
    ) -> None:
        from datetime import timezone

        freelancer.is_verified = True
        freelancer.email_verified_at = datetime.now(timezone.utc)
        db.add(freelancer)
        await db.commit()


crud_freelancer = CRUDFreelancer(Freelancer)
