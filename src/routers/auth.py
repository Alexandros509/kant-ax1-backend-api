import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from models.user import User
from schemas.auth import UserRegister, UserResponse, Token
from security import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger("board_api.auth")

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="회원가입")
async def register(payload: UserRegister, db: AsyncSession = Depends(get_async_db)):
    """새 회원을 등록합니다. 비밀번호는 해시로 바꿔 저장합니다."""
    # 같은 아이디가 이미 있는지 확인
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        nickname=payload.nickname,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"신규 가입 완료: {payload.username}")
    return new_user


@router.post("/login", response_model=Token, summary="로그인 (토큰 발급)")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """아이디·비밀번호를 확인하고 액세스 토큰을 발급합니다."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    matched_user = result.scalar_one_or_none()

    if not matched_user or not verify_password(form_data.password, matched_user.hashed_password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    access_token = create_access_token(data={"sub": matched_user.username})
    logger.info(f"토큰 로그인 성공 및 발급 완료: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, summary="내 정보 조회")
async def read_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 회원 정보를 돌려줍니다."""
    return current_user
