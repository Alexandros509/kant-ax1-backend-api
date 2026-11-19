from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    """회원 정보를 저장하는 테이블 모델입니다."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)

    # 일대다 관계 설정: 회원이 삭제되면 작성한 게시글도 함께 삭제되도록 설정합니다.
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
