import os
import sys
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, MetaData, String, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, backref

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )

class User(Base):
    """Модель, описывающая пользователей"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # one-to-many с моделью Tweet (твиты пользователя)
    tweets = relationship(
        "Tweet", back_populates="author", cascade="all, delete-orphan"
    )

    # юзер подписан на, фолловеры - many-to-many
    following = relationship(
        'User',
        secondary='follow',
        primaryjoin='User.id == Follow.follower_id',
        secondaryjoin='User.id == Follow.following_id',
        backref=backref('followers')
    )


    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.name}>"


class Follow(Base):
    """Модель, описывающая подписку"""
    __tablename__ = "follow"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #id пользователя, который подписался
    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # id пользователя, на которого подписались
    following_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_follow_relationship'),
    )

    def __repr__(self):
        return f"<Follow follower_id={self.follower_id} followed_id={self.following_id}>"


class Tweet(Base):
    """Модель, описывающая твиты"""
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # текст коммента
    content: Mapped[str] = mapped_column(String(280), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # пользователь, поставивший лайк
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    author = relationship("User", back_populates="tweets")
    # Отношение "один ко многим" с моделью Like (лайки твита)
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan, delete")
    image = relationship("Image", back_populates="tweet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tweet {self.content[:20]}>"


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id: Mapped[int] = mapped_column(Integer, ForeignKey("tweets.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")

    def __repr__(self):
        return f"<Like user_id={self.user_id} tweet_id={self.tweet_id}>"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    tweet_id: Mapped[int] = mapped_column(Integer, ForeignKey("tweets.id"), nullable=True)

    tweet = relationship("Tweet", back_populates="image")

    def __repr__(self):
        return f"<Image {self.url}>"