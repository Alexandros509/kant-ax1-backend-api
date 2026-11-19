from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="게시글 제목")
    content: str = Field(..., min_length=1, description="게시글 본문")


class PostUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="수정할 게시글 제목")
    content: str = Field(..., min_length=1, description="수정할 게시글 본문")


class PostResponse(BaseModel):
    id: int = Field(..., description="게시글 고유 식별자 (ID)")
    title: str = Field(..., description="게시글 제목")
    content: str = Field(..., description="게시글 본문")
    owner_id: int = Field(..., description="작성자 고유 식별자 (ID)")

    class Config:
        from_attributes = True
