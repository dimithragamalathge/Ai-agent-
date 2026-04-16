"""
SQLAlchemy ORM models for the health content agent.
"""

import json
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Article(Base):
    """A scraped health article from any source."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(128), nullable=False)   # e.g. "healthline", "pubmed"
    topic = Column(String(64), nullable=True)       # e.g. "nutrition", "mental_health"
    scraped_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

    posts = relationship("Post", back_populates="article")

    def __repr__(self) -> str:
        return f"<Article id={self.id} source={self.source!r} title={self.title[:40]!r}>"


class Post(Base):
    """A generated Instagram post waiting for review or already published."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)

    # Content
    post_type = Column(String(16), nullable=True, default="tips")  # "stat"|"tips"|"myth_fact"|"quote"
    format = Column(String(16), nullable=False, default="single")  # "single" | "carousel"
    hook = Column(String(256), nullable=True)        # First grabbing line
    caption = Column(Text, nullable=False)
    hashtags = Column(Text, nullable=True)           # JSON list stored as string
    slide_texts = Column(Text, nullable=True)        # JSON list of {heading, body} dicts

    # Design
    canva_design_id = Column(String(128), nullable=True)
    image_paths = Column(Text, nullable=True)        # JSON list of local file paths

    # Status: draft → approved → posted  (or → rejected / failed)
    status = Column(String(16), nullable=False, default="draft")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)

    # Instagram
    instagram_media_id = Column(String(64), nullable=True)

    article = relationship("Article", back_populates="posts")
    scheduled_jobs = relationship("ScheduledJob", back_populates="post")

    # ── Helpers for JSON fields ───────────────────────────────────────────────

    def get_hashtags(self) -> list[str]:
        if not self.hashtags:
            return []
        return json.loads(self.hashtags)

    def set_hashtags(self, tags: list[str]) -> None:
        self.hashtags = json.dumps(tags)

    def get_slide_texts(self) -> list[dict]:
        if not self.slide_texts:
            return []
        return json.loads(self.slide_texts)

    def set_slide_texts(self, slides: list[dict]) -> None:
        self.slide_texts = json.dumps(slides)

    def get_image_paths(self) -> list[str]:
        if not self.image_paths:
            return []
        return json.loads(self.image_paths)

    def set_image_paths(self, paths: list[str]) -> None:
        self.image_paths = json.dumps(paths)

    def __repr__(self) -> str:
        return f"<Post id={self.id} format={self.format!r} status={self.status!r}>"


class ScheduledJob(Base):
    """Tracks scheduled publish jobs (future use for time-delayed posting)."""

    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(16), nullable=False, default="pending")  # pending | done | failed

    post = relationship("Post", back_populates="scheduled_jobs")

    def __repr__(self) -> str:
        return (
            f"<ScheduledJob id={self.id} post_id={self.post_id} "
            f"at={self.scheduled_time} status={self.status!r}>"
        )
