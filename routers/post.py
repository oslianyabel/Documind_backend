from functools import wraps
from typing import Annotated
from enum import Enum

import sqlalchemy

from config import logger
from database import comments_table, database, like_table, post_table
from fastapi import APIRouter, Depends, HTTPException
from models.post import Comment, CommentIn, Like, LikeIn, Post, PostIn, PostWithComments, PostWithLikes
from models.user import UserOut
from security import get_current_user

router = APIRouter()
UserDep = Annotated[UserOut, Depends(get_current_user)]

select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


def check_post(func):
    @wraps(func)
    async def wrapper(post_id: int, *args, **kwargs):
        if not await find_post(post_id):
            raise HTTPException(status_code=404, detail="Post not found")

        return await func(post_id, *args, **kwargs)

    return wrapper


async def find_post(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    return await database.fetch_one(query)


@router.post("/", status_code=201)
async def create_post(post: PostIn, current_user: UserDep) -> Post:
    logger.info("Create post")

    data = post.model_dump()
    data["user_id"] = current_user.id

    query = post_table.insert().values(data)

    data["id"] = await database.execute(query)

    return Post(**data)


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/", response_model=list[PostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("Get all posts")

    if sorting == PostSorting.new:
        query = select_post_and_likes.order_by(post_table.c.id.desc())

    elif sorting == PostSorting.old:
        query = select_post_and_likes.order_by(post_table.c.id.asc()) 

    elif sorting == PostSorting.most_likes:
        query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    return await database.fetch_all(query)


@router.post("/comment", status_code=201)
async def create_comment(comment: CommentIn, current_user: UserDep) -> Comment:
    logger.info("Create comment")

    if not await find_post(comment.post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    data = comment.model_dump()
    data["user_id"] = current_user.id

    query = comments_table.insert().values(data)

    data["id"] = await database.execute(query)

    return Comment(**data)


@router.get("/{post_id}/comment", response_model=list[Comment])
@check_post
async def get_comments_on_post(post_id: int):
    logger.info("Get comments on post")

    query = comments_table.select().where(comments_table.c.post_id == post_id)

    return await database.fetch_all(query)


@router.get("/{post_id}", response_model=PostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Get post with comments")

    query = select_post_and_likes.where(post_table.c.id == post_id)

    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }


@router.post("/like", status_code=201)
async def like_post(like: LikeIn, current_user: UserDep) -> Like:
    logger.info("Liking post")

    if not await find_post(like.post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    data = like.model_dump()
    data["user_id"] = current_user.id

    query = like_table.insert().values(data)

    data["id"] = await database.execute(query)

    return Like(**data)
