import os
from datetime import datetime

from slugify import slugify

from app.core.timezone import to_app_tz, utc_now


class HugoService:
    def _load_config(self, community_id: int) -> tuple[str, str]:
        """Load Hugo config from the database for a given community."""
        from app.database import SessionLocal
        from app.models.channel import ChannelConfig

        db = SessionLocal()
        try:
            cfg = db.query(ChannelConfig).filter(
                ChannelConfig.community_id == community_id,
                ChannelConfig.channel == "hugo",
            ).first()
            if not cfg or not cfg.config:
                raise ValueError("Hugo 博客未配置。请在渠道设置中配置仓库路径。")
            config = cfg.config
            repo_path = config.get("repo_path", "")
            content_dir = config.get("content_dir", "content/posts")
            if not repo_path:
                raise ValueError("Hugo 仓库路径未配置。")
            return repo_path, content_dir
        finally:
            db.close()

    def _get_posts_dir(self, community_id: int) -> str:
        repo_path, content_dir = self._load_config(community_id)
        posts_dir = os.path.join(repo_path, content_dir)
        os.makedirs(posts_dir, exist_ok=True)
        return posts_dir

    def generate_front_matter(
        self,
        title: str,
        author: str = "",
        tags: list[str] | None = None,
        category: str = "",
        date: datetime | None = None,
    ) -> str:
        """Generate Hugo YAML front matter."""
        if date is None:
            date = to_app_tz(utc_now())

        lines = [
            "---",
            f'title: "{title}"',
            f"date: {date.isoformat(timespec='seconds')}",
        ]
        if author:
            lines.append(f'author: "{author}"')
        if tags:
            tags_str = ", ".join(f'"{t}"' for t in tags)
            lines.append(f"tags: [{tags_str}]")
        if category:
            lines.append(f'categories: ["{category}"]')
        lines.append("draft: false")
        lines.append("---")
        return "\n".join(lines)

    def generate_post(
        self,
        title: str,
        markdown_content: str,
        author: str = "",
        tags: list[str] | None = None,
        category: str = "",
    ) -> str:
        """Generate a complete Hugo post with front matter."""
        front_matter = self.generate_front_matter(title, author, tags, category)
        return f"{front_matter}\n\n{markdown_content}\n"

    def save_post(
        self,
        title: str,
        markdown_content: str,
        author: str = "",
        tags: list[str] | None = None,
        category: str = "",
        community_id: int = 0,
    ) -> str:
        """Save a post as a markdown file in the Hugo content directory.

        Returns the file path of the saved post.
        """
        posts_dir = self._get_posts_dir(community_id)
        filename = f"{slugify(title, allow_unicode=True)}.md"
        file_path = os.path.join(posts_dir, filename)

        post_content = self.generate_post(title, markdown_content, author, tags, category)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(post_content)

        return file_path

    def preview_post(
        self,
        title: str,
        markdown_content: str,
        author: str = "",
        tags: list[str] | None = None,
        category: str = "",
    ) -> str:
        """Generate Hugo post content for preview without saving."""
        return self.generate_post(title, markdown_content, author, tags, category)


hugo_service = HugoService()
