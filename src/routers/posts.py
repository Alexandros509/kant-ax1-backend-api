import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_db
from models.post import Post
from models.user import User
from schemas.post import PostCreate, PostUpdate, PostResponse
from security import get_current_user

logger = logging.getLogger("board_api.posts")

router = APIRouter(prefix="/posts", tags=["Posts"])


async def find_post(post_id: int, db: AsyncSession) -> Post:
    """게시글 1건을 찾고, 없으면 404를 발생시킵니다."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="게시글 작성")
async def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """로그인한 회원이 새 게시글을 작성합니다."""
    new_post = Post(title=payload.title, content=payload.content, owner_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    logger.info(f"게시글 작성 완료: id={new_post.id}, 작성자={current_user.username}")
    return new_post


@router.get("", response_model=List[PostResponse], summary="게시글 목록 조회")
async def read_posts(db: AsyncSession = Depends(get_async_db)):
    """전체 게시글을 최신순으로 조회합니다."""
    result = await db.execute(select(Post).order_by(Post.id.desc()))
    return result.scalars().all()


@router.get("/{post_id}", response_model=PostResponse, summary="게시글 상세 조회")
async def read_post(post_id: int, db: AsyncSession = Depends(get_async_db)):
    """게시글 1건을 조회합니다."""
    return await find_post(post_id, db)


@router.put("/{post_id}", response_model=PostResponse, summary="게시글 수정")
async def update_post(
    post_id: int,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """작성자 본인만 게시글을 수정할 수 있습니다."""
    post = await find_post(post_id, db)

    # 작성자 검증: 다른 회원의 글이면 403
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="작성자만 수정할 수 있습니다.")

    post.title = payload.title
    post.content = payload.content
    await db.commit()
    await db.refresh(post)
    logger.info(f"게시글 수정 완료: id={post_id}")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="게시글 삭제")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """작성자 본인만 게시글을 삭제할 수 있습니다."""
    post = await find_post(post_id, db)

    # 작성자 검증: 다른 회원의 글이면 403
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="작성자만 삭제할 수 있습니다.")

    await db.delete(post)
    await db.commit()
    logger.info(f"게시글 삭제 완료: id={post_id}")
