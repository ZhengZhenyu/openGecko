import os
import re
import time
from pathlib import Path

import httpx
import markdown
from bs4 import BeautifulSoup

from app.core.logging import get_logger

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

# WeChat API base URL (public, not a secret)
WECHAT_API_BASE = "https://api.weixin.qq.com"

_logger = get_logger(__name__)


class WechatService:
    def __init__(self):
        self._access_token = None
        self._token_expires = 0
        self._app_id = None
        self._app_secret = None

    def _load_credentials(self, community_id: int) -> tuple[str, str]:
        """Load WeChat credentials from the database for a given community."""
        from app.database import SessionLocal
        from app.models.channel import ChannelConfig
        from app.core.security import decrypt_value

        db = SessionLocal()
        try:
            cfg = db.query(ChannelConfig).filter(
                ChannelConfig.community_id == community_id,
                ChannelConfig.channel == "wechat",
            ).first()
            if not cfg or not cfg.config:
                raise ValueError("微信公众号未配置。请在渠道设置中配置 AppID 和 AppSecret。")
            config = cfg.config
            app_id = config.get("app_id", "")
            app_secret_enc = config.get("app_secret", "")
            if not app_id or not app_secret_enc:
                raise ValueError("微信公众号 AppID 或 AppSecret 未配置。")
            app_secret = decrypt_value(app_secret_enc)
            return app_id, app_secret
        finally:
            db.close()

    async def _get_access_token(self, community_id: int) -> str:
        """Get a valid access token, refreshing if needed."""
        app_id, app_secret = self._load_credentials(community_id)

        # Invalidate cache if credentials changed
        if app_id != self._app_id or app_secret != self._app_secret:
            self._access_token = None
            self._token_expires = 0
            self._app_id = app_id
            self._app_secret = app_secret

        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{WECHAT_API_BASE}/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": app_id,
                        "secret": app_secret,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                if "access_token" not in data:
                    errcode = data.get("errcode", "unknown")
                    errmsg = data.get("errmsg", "未知错误")
                    raise Exception(f"获取access_token失败 [errcode={errcode}]: {errmsg}")

                self._access_token = data["access_token"]
                self._token_expires = time.time() + data.get("expires_in", 7200) - 300
                return self._access_token
        except httpx.TimeoutException:
            raise Exception("微信API请求超时，请稍后重试")
        except httpx.HTTPError as e:
            raise Exception(f"微信API网络错误: {e}")

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

    async def _replace_local_images_with_wechat_urls(
        self, markdown_text: str, community_id: int
    ) -> str:
        """
        查找Markdown中的本地图片引用，上传到微信并替换URL。

        支持格式：
        - ![alt](/uploads/xxx.jpg)
        - ![alt](../uploads/xxx.png)
        """
        from app.config import settings

        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        async def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)

            # 只处理本地路径
            if img_path.startswith('http://') or img_path.startswith('https://'):
                return match.group(0)

            # 解析本地路径
            if img_path.startswith('/uploads/'):
                full_path = Path(settings.UPLOAD_DIR) / img_path.lstrip('/uploads/')
            elif img_path.startswith('uploads/'):
                full_path = Path(settings.UPLOAD_DIR) / img_path.lstrip('uploads/')
            else:
                # 尝试相对路径
                full_path = Path(img_path)

            if not full_path.exists():
                # 图片不存在，保留原样并记录警告
                _logger.warning("图片文件不存在", extra={"img_path": img_path})
                return match.group(0)

            try:
                # 上传到微信并获取URL
                wechat_url = await self.upload_image(str(full_path), community_id)
                return f'![{alt_text}]({wechat_url})'
            except Exception as e:
                # 上传失败，记录错误但不中断流程
                _logger.warning("图片上传失败", extra={"img_path": img_path, "error": str(e)})
                return match.group(0)

        # 查找所有图片并替换
        result = markdown_text
        for match in re.finditer(image_pattern, markdown_text):
            replacement = await replace_image(match)
            result = result.replace(match.group(0), replacement, 1)

        return result

    async def upload_image(self, image_path: str, community_id: int) -> str:
        """Upload an image for use inside article body. Returns a WeChat URL."""
        token = await self._get_access_token(community_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, "rb") as f:
                    resp = await client.post(
                        f"{WECHAT_API_BASE}/cgi-bin/media/uploadimg",
                        params={"access_token": token},
                        files={"media": f},
                    )
                resp.raise_for_status()
                data = resp.json()

                if "url" not in data:
                    errcode = data.get("errcode", "unknown")
                    errmsg = data.get("errmsg", "未知错误")
                    raise Exception(f"微信图片上传失败 [errcode={errcode}]: {errmsg}")

                return data["url"]
        except httpx.TimeoutException:
            raise Exception("微信API请求超时，请稍后重试")
        except httpx.HTTPError as e:
            raise Exception(f"微信API网络错误: {e}")

    async def upload_thumb_media(self, image_path: str, community_id: int) -> str:
        """Upload a permanent thumb image and return media_id for use as cover."""
        token = await self._get_access_token(community_id)
        filename = os.path.basename(image_path)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(image_path, "rb") as f:
                    resp = await client.post(
                        f"{WECHAT_API_BASE}/cgi-bin/material/add_material",
                        params={"access_token": token, "type": "image"},
                        files={"media": (filename, f, "image/png")},
                    )
                resp.raise_for_status()
                data = resp.json()

                if "media_id" not in data:
                    errcode = data.get("errcode", "unknown")
                    errmsg = data.get("errmsg", "未知错误")
                    raise Exception(f"微信封面上传失败 [errcode={errcode}]: {errmsg}")

                return data["media_id"]
        except httpx.TimeoutException:
            raise Exception("微信API请求超时，请稍后重试")
        except httpx.HTTPError as e:
            raise Exception(f"微信API网络错误: {e}")

    async def create_draft(self, title: str, content_html: str, author: str = "", thumb_media_id: str = "", community_id: int = 0) -> dict:
        """Create a draft article in WeChat Official Account."""
        token = await self._get_access_token(community_id)

        article = {
            "title": title,
            "author": author,
            "content": content_html,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{WECHAT_API_BASE}/cgi-bin/draft/add",
                    params={"access_token": token},
                    json={"articles": [article]},
                )
                resp.raise_for_status()
                data = resp.json()

                if "media_id" not in data:
                    errcode = data.get("errcode", "unknown")
                    errmsg = data.get("errmsg", "未知错误")
                    raise Exception(f"微信草稿创建失败 [errcode={errcode}]: {errmsg}")

                return {"media_id": data["media_id"], "status": "draft"}
        except httpx.TimeoutException:
            raise Exception("微信API请求超时，请稍后重试")
        except httpx.HTTPError as e:
            raise Exception(f"微信API网络错误: {e}")

    async def get_article_stats(self, publish_id: str, community_id: int = 0) -> dict:
        """Get article statistics (limited for subscription accounts)."""
        token = await self._get_access_token(community_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WECHAT_API_BASE}/cgi-bin/datacube/getarticlesummary",
                params={"access_token": token},
                json={"begin_date": "", "end_date": ""},
            )
            return resp.json()


wechat_service = WechatService()
