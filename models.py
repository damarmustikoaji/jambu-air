from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class TikTokPost:
    post_id: str
    username: str
    display_name: str
    caption: str
    like_count: int
    comment_count: int
    share_count: int
    view_count: int
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    post_url: str
    timestamp: Optional[datetime]
    hashtags: list[str] = field(default_factory=list)
    platform: str = "tiktok"

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "post_id": self.post_id,
            "username": self.username,
            "display_name": self.display_name,
            "caption": self.caption,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "view_count": self.view_count,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
            "post_url": self.post_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "hashtags": self.hashtags,
        }


@dataclass
class ThreadsPost:
    post_id: str
    username: str
    display_name: str
    caption: str
    like_count: int
    reply_count: int
    repost_count: int
    share_count: int
    post_url: str
    timestamp: Optional[datetime]
    media_urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    platform: str = "threads"

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "post_id": self.post_id,
            "username": self.username,
            "display_name": self.display_name,
            "caption": self.caption,
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "repost_count": self.repost_count,
            "share_count": self.share_count,
            "post_url": self.post_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "media_urls": self.media_urls,
            "hashtags": self.hashtags,
        }


@dataclass
class ScrapeResult:
    query: str
    scraped_at: datetime
    tiktok_posts: list[TikTokPost] = field(default_factory=list)
    threads_posts: list[ThreadsPost] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {
            "query": self.query,
            "scraped_at": self.scraped_at.isoformat(),
            "results": {
                "tiktok": [p.to_dict() for p in self.tiktok_posts],
                "threads": [p.to_dict() for p in self.threads_posts],
            },
            "summary": {
                "tiktok_count": len(self.tiktok_posts),
                "threads_count": len(self.threads_posts),
                "total_count": len(self.tiktok_posts) + len(self.threads_posts),
            },
        }
