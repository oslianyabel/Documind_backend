from functools import wraps

from fastapi import APIRouter, HTTPException
from models.post import Comment, CommentIn, Post, PostIn, PostWithComments

router = APIRouter()
post_table = {}
comment_table = {}


def check_post(func):
    @wraps(func)
    async def wrapper(post_id: int, *args, **kwargs):
        post = find_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        return await func(post_id, *args, **kwargs)

    return wrapper


def find_post(post_id: int):
    return post_table.get(post_id)


@router.post("/", response_model=Post, status_code=201)
async def create_post(post: PostIn):
    data = post.model_dump()
    id = len(post_table)
    data["id"] = id
    post_table[id] = data
    return data


@router.get("/", response_model=list[Post])
async def get_all_post():
    return list(post_table.values())


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn):
    if not find_post(comment.post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    data = comment.model_dump()
    id = len(comment_table)
    data["id"] = id
    comment_table[id] = data
    return data


@router.get("/{post_id}/comment", response_model=list[Comment])
@check_post
async def get_comments_on_post(post_id: int):
    return [
        comment for comment in comment_table.values() if comment["post_id"] == post_id
    ]


@router.get("/{post_id}", response_model=PostWithComments)
@check_post
async def get_post_with_comments(post_id: int):
    return {"post": find_post(post_id), "comments": await get_comments_on_post(post_id)}
