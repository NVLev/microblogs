from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from typing import List, Optional

from pydantic import BaseModel, validator


class ResultBase(BaseModel):
    result: bool

class UserBase(BaseModel):
    id: int
    name: str
    # api_key: str

class UserData(BaseModel):
    id: int
    name: str
    followers: List[UserBase]
    following: List[UserBase]


class UserRead(BaseModel):
    result: bool
    user: UserData

class UserCreate(UserBase):
    api_key: str

class LikeBase(BaseModel):
    id: int
    user_id: int
    
class ImageBase(BaseModel):
    url: str

class TweetBase(BaseModel):
    id: int
    content: str
    attachments: Optional[List[str]| None] = None
    author: UserBase
    likes: List[LikeBase]


class TweetRead(BaseModel):
    result: bool
    tweets: List[TweetBase]


class TweetCreate(BaseModel):
    tweet_data: str
    image_ids: Optional[list[int] | None] = None

class TweetResponse(BaseModel):
    result: bool
    tweet_id: int



class FollowingCreate(BaseModel):
    following_id: int

class LikeAdd(BaseModel):
    user_id: int
    tweet_id: int


class FollowBase(BaseModel):
    follower_id: int
    following_id: int





