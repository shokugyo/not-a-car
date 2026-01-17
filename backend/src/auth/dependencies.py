from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.common.exceptions import UnauthorizedException
from .models import Owner
from .service import AuthService


security = HTTPBearer()


async def get_current_owner(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Owner:
    token = credentials.credentials
    service = AuthService(db)

    try:
        payload = service.decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid access token")

        owner_id = int(payload.get("sub"))
        owner = await service.get_owner_by_id(owner_id)

        if not owner:
            raise UnauthorizedException("Owner not found")

        if not owner.is_active:
            raise UnauthorizedException("Account is inactive")

        return owner

    except Exception as e:
        raise UnauthorizedException(str(e))
