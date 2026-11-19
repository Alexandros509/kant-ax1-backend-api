import os
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from models.user import User

# .env 파일의 값을 환경변수로 불러옵니다.
load_dotenv()

# 비밀번호 해시 암호화 엔진 초기화 (Bcrypt 적용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 서명용 비밀 설정 값 (코드에 적지 않고 .env에서 읽습니다.)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 토큰 수거기 지정 (/login 경로 주입)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    """평문 비밀번호를 강력한 단방향 해시 코드로 변환합니다."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력받은 평문 비밀번호가 저장된 해시값과 일치하는지 대조합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """단기 유효 기간(30분)을 가진 JWT 액세스 토큰을 발행합니다."""
    to_encode = data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire_time, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Authorization 헤더의 토큰으로 현재 로그인한 회원을 찾습니다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 올바르지 않거나 로그인이 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Authorization 헤더를 통해 들어온 토큰 복호화
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (ExpiredSignatureError, InvalidTokenError):
        raise credentials_exception

    # 데이터베이스에서 해당 사용자 탐색 후 인가 승인
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
