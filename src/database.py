import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# .env 파일의 값을 환경변수로 불러옵니다.
load_dotenv()

# 데이터베이스 접속 정보 주소를 설정합니다.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
)

# 비동기 엔진을 만들고 커넥션 풀 설정을 주입합니다.
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,            # 평소에 유지할 기본 연결 통로 개수
    max_overflow=20,         # 사용자가 몰릴 때 임시로 늘릴 수 있는 최대 연결 개수
    pool_timeout=30.0,       # 연결 통로가 비기를 기다리는 최대 시간(초)
    pool_recycle=1800,       # 오래된 연결을 새것으로 교체하는 주기(30분)
    pool_pre_ping=True,      # 사용하기 전에 연결이 살아있는지 확인
)

# 비동기 데이터베이스 세션을 만들어주는 생성기를 정의합니다.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # 저장 후 데이터가 사라지는 에러를 막아줍니다.
)


# 데이터베이스 테이블의 기준이 되는 베이스 클래스입니다.
class Base(DeclarativeBase):
    pass


# FastAPI에서 각 요청마다 데이터베이스 세션을 안전하게 제공하는 함수입니다.
async def get_async_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        try:
            yield session    # 실물 기능(라우터)에 세션을 전달합니다.
        except Exception:
            await session.rollback() # 오류가 발생하면 작업을 모두 취소합니다.
            raise
        finally:
            await session.close()    # 작업이 끝나면 세션을 안전하게 닫고 풀에 반납합니다.
