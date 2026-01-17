from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .schemas import OwnerCreate, OwnerResponse, OwnerLogin, Token
from .service import AuthService
from .dependencies import get_current_owner
from .models import Owner


router = APIRouter()


@router.post("/register", response_model=OwnerResponse)
async def register(
    owner_data: OwnerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new owner"""
    service = AuthService(db)
    owner = await service.create_owner(owner_data)
    return owner


@router.post("/login", response_model=Token)
async def login(
    credentials: OwnerLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token"""
    service = AuthService(db)
    token = await service.authenticate(credentials.email, credentials.password)
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token"""
    service = AuthService(db)
    token = await service.refresh_tokens(refresh_token)
    return token


@router.get("/me", response_model=OwnerResponse)
async def get_me(
    current_owner: Owner = Depends(get_current_owner),
):
    """Get current owner info"""
    return current_owner
