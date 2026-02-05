import os
import time

import httpx
import markdown
from bs4 import BeautifulSoup

from app.config import settings

# WeChat-compatible inline styles
WECHAT_STYLES = {
    "h1": "font-size:22px;font-weight:bold;color:#1a1a1a;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid #eee;",
    "h2": "font-size:20px;font-weight:bold;color:#1a1a1a;margin:20px 0 10px;",
    "h3": "font-size:18px;font-weight:bold;color:#1a1a1a;margin:16px 0 8px;",
    "p": "font-size:15px;color:#333;line-height:1.8;margin:8px 0;",
    "blockquote": "border-left:4px solid #42b983;padding:12px 16px;margin:16px 0;background:#f8f8f8;color:#666;font-size:14px;line-height:1.6;",
    "code_inline": "background:#f0f0f0;color:#e96900;padding:2px 6px;border-radius:3px;font-size:13px;font-family:Consolas,Monaco,monospace;",
    "code_block": "background:#2d2d2d;color:#ccc;padding:16px;border-radius:6px;font-size:13px;line-height:1.5;font-family:Consolas,Monaco,monospace;overflow-x:auto;white-space:pre-wrap;word-wrap:break-word;",
    "img": "max-width:100%;height:auto;border-radius:4px;margin:12px 0;",
    "a": "color:#42b983;text-decoration:none;",
    "ul": "padding-left:20px;margin:8px 0;",
    "ol": "padding-left:20px;margin:8px 0;",
    "li": "font-size:15px;color:#333;line-height:1.8;margin:4px 0;",
    "table": "width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;",
    "th": "border:1px solid #ddd;padding:8px 12px;background:#f5f5f5;font-weight:bold;text-align:left;",
    "td": "border:1px solid #ddd;padding:8px 12px;",
    "hr": "border:none;border-top:1px solid #eee;margin:20px 0;",
}


class WechatService:
    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.app_secret = settings.WECHAT_APP_SECRET
        self.api_base = settings.WECHAT_API_BASE
        self._access_token = None
        self._token_expires = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.api_base}/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": self.app_id,
                    "secret": self.app_secret,
                },
            )
            data = resp.json()
            if "access_token" not in data:
                raise Exception(f"Failed to get access token: {data}")
            self._access_token = data["access_token"]
            self._token_expires = time.time() + data.get("expires_in", 7200) - 300
            return self._access_token

    def convert_to_wechat_html(self, markdown_text: str) -> str:
        """Convert Markdown to WeChat-compatible HTML with inline styles."""
        html = markdown.markdown(
            markdown_text,
            extensions=["extra", "tables", "nl2br"],
        )
        soup = BeautifulSoup(html, "html.parser")

        for tag_name, style in WECHAT_STYLES.items():
            if tag_name == "code_inline" or tag_name == "code_block":
                continue
            for tag in soup.find_all(tag_name):
                tag["style"] = style

        # Handle code blocks vs inline code
        for code_tag in soup.find_all("code"):
            parent = code_tag.parent
            if parent and parent.name == "pre":
                # Code block
                parent["style"] = WECHAT_STYLES["code_block"]
                code_tag["style"] = "background:none;color:inherit;padding:0;font-size:inherit;"
            else:
                # Inline code
                code_tag["style"] = WECHAT_STYLES["code_inline"]

        # Remove <pre> inner styling conflicts
        for pre_tag in soup.find_all("pre"):
            if not pre_tag.get("style"):
                pre_tag["style"] = WECHAT_STYLES["code_block"]

        return str(soup)

    async def upload_image(self, image_path: str) -> str:
        """Upload an image for use inside article body. Returns a WeChat URL."""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                resp = await client.post(
                    f"{self.api_base}/cgi-bin/media/uploadimg",
                    params={"access_token": token},
                    files={"media": f},
                )
            data = resp.json()
            if "url" not in data:
                raise Exception(f"Failed to upload image: {data}")
            return data["url"]

    async def upload_thumb_media(self, image_path: str) -> str:
        """Upload a permanent thumb image and return media_id for use as cover."""
        token = await self._get_access_token()
        filename = os.path.basename(image_path)
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                resp = await client.post(
                    f"{self.api_base}/cgi-bin/material/add_material",
                    params={"access_token": token, "type": "image"},
                    files={"media": (filename, f, "image/png")},
                )
            data = resp.json()
            if "media_id" not in data:
                raise Exception(f"Failed to upload thumb media: {data}")
            return data["media_id"]

    async def create_draft(self, title: str, content_html: str, author: str = "", thumb_media_id: str = "") -> dict:
        """Create a draft article in WeChat Official Account."""
        token = await self._get_access_token()

        article = {
            "title": title,
            "author": author,
            "content": content_html,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_base}/cgi-bin/draft/add",
                params={"access_token": token},
                json={"articles": [article]},
            )
            data = resp.json()
            if "media_id" not in data:
                raise Exception(f"Failed to create draft: {data}")
            return {"media_id": data["media_id"], "status": "draft"}

    async def get_article_stats(self, publish_id: str) -> dict:
        """Get article statistics (limited for subscription accounts)."""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_base}/cgi-bin/datacube/getarticlesummary",
                params={"access_token": token},
                json={"begin_date": "", "end_date": ""},
            )
            return resp.json()


wechat_service = WechatService()
