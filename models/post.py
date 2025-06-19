from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostIn(BaseModel):
    body: str


class Post(PostIn):
    id: int
    user_id: int
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostWithLikes(Post):
    likes: int


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class PostWithComments(BaseModel):
    post: PostWithLikes
    comments: list[Comment]

    model_config = ConfigDict(from_attributes=True)


class LikeIn(BaseModel):
    post_id: int


class Like(LikeIn):
    id: int
    user_id: int
