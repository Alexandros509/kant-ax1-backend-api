import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, Base
# 테이블 생성 전에 모델을 불러와 Base에 등록합니다.
from models.user import User  # noqa: F401
from models.post import Post  # noqa: F401
from routers.auth import router as auth_router
from routers.posts import router as posts_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
logger = logging.getLogger("board_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("서버가 시작됩니다. 테이블 생성을 시작합니다.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("서버가 종료됩니다. 연결 통로를 모두 닫습니다.")
    await engine.dispose()


app = FastAPI(
    title="RESTful 게시판 API",
    description="회원가입·로그인(JWT)과 게시글 CRUD를 제공하는 게시판 API입니다.",
    version="1.0.0",
    lifespan=lifespan,
)

# 도메인별 라우터 등록
app.include_router(auth_router)
app.include_router(posts_router)
