from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from models.user import User


class Post(Base):
    """게시글 정보를 저장하는 테이블 모델입니다."""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 작성자(회원) 테이블과 연결하는 외래키 설정입니다.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # 작성자 정보로 바로 접근할 수 있는 역참조 설정입니다.
    owner: Mapped["User"] = relationship("User", back_populates="posts")
