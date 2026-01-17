from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.common.exceptions import UnauthorizedException, NotACarException
from .models import Owner
from .schemas import OwnerCreate, Token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(owner_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {"sub": str(owner_id), "exp": expire, "type": "access"}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def create_refresh_token(owner_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        payload = {"sub": str(owner_id), "exp": expire, "type": "refresh"}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            raise UnauthorizedException("Invalid token")

    async def get_owner_by_email(self, email: str) -> Optional[Owner]:
        result = await self.db.execute(select(Owner).where(Owner.email == email))
        return result.scalar_one_or_none()

    async def get_owner_by_id(self, owner_id: int) -> Optional[Owner]:
        result = await self.db.execute(select(Owner).where(Owner.id == owner_id))
        return result.scalar_one_or_none()

    async def create_owner(self, owner_data: OwnerCreate) -> Owner:
        existing = await self.get_owner_by_email(owner_data.email)
        if existing:
            raise NotACarException("Email already registered")

        owner = Owner(
            email=owner_data.email,
            hashed_password=self.hash_password(owner_data.password),
            full_name=owner_data.full_name,
            phone=owner_data.phone,
        )
        self.db.add(owner)
        await self.db.commit()
        await self.db.refresh(owner)
        return owner

    async def authenticate(self, email: str, password: str) -> Token:
        owner = await self.get_owner_by_email(email)
        if not owner or not self.verify_password(password, owner.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not owner.is_active:
            raise UnauthorizedException("Account is inactive")

        return Token(
            access_token=self.create_access_token(owner.id),
            refresh_token=self.create_refresh_token(owner.id),
        )

    async def refresh_tokens(self, refresh_token: str) -> Token:
        payload = self.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        owner_id = int(payload.get("sub"))
        owner = await self.get_owner_by_id(owner_id)
        if not owner or not owner.is_active:
            raise UnauthorizedException("Owner not found or inactive")

        return Token(
            access_token=self.create_access_token(owner.id),
            refresh_token=self.create_refresh_token(owner.id),
        )
