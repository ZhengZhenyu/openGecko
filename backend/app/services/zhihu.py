import markdown
from bs4 import BeautifulSoup

ZHIHU_STYLES = {
    "h1": "font-size:24px;font-weight:bold;margin:20px 0 12px;",
    "h2": "font-size:20px;font-weight:bold;margin:18px 0 10px;",
    "h3": "font-size:18px;font-weight:bold;margin:16px 0 8px;",
    "p": "font-size:15px;line-height:1.8;margin:8px 0;",
    "blockquote": "border-left:3px solid #0084ff;padding:10px 16px;margin:12px 0;background:#f6f6f6;color:#666;",
    "code_inline": "background:#f0f0f0;color:#e96900;padding:2px 4px;border-radius:3px;font-size:13px;",
    "code_block": "background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;font-size:13px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;",
    "img": "max-width:100%;height:auto;margin:12px 0;",
    "a": "color:#0084ff;text-decoration:none;",
    "table": "width:100%;border-collapse:collapse;margin:12px 0;",
    "th": "border:1px solid #ddd;padding:8px;background:#f5f5f5;text-align:left;",
    "td": "border:1px solid #ddd;padding:8px;",
}


class ZhihuService:
    """Zhihu publishing service.

    Zhihu does not have a public content API, so we generate
    formatted HTML for the user to copy-paste into Zhihu's editor.
    """

    def format_for_zhihu(self, title: str, markdown_content: str) -> dict:
        """Format content for Zhihu.

        Returns a dict with:
        - title: article title
        - html: Zhihu-compatible HTML with inline styles
        - markdown: original markdown (Zhihu editor also accepts MD)
        """
        html = markdown.markdown(
            markdown_content,
            extensions=["extra", "tables", "nl2br"],
        )
        soup = BeautifulSoup(html, "html.parser")

        for tag_name, style in ZHIHU_STYLES.items():
            if tag_name in ("code_inline", "code_block"):
                continue
            for tag in soup.find_all(tag_name):
                tag["style"] = style

        for code_tag in soup.find_all("code"):
            parent = code_tag.parent
            if parent and parent.name == "pre":
                parent["style"] = ZHIHU_STYLES["code_block"]
                code_tag["style"] = "background:none;color:inherit;padding:0;"
            else:
                code_tag["style"] = ZHIHU_STYLES["code_inline"]

        return {
            "title": title,
            "html": str(soup),
            "markdown": markdown_content,
            "platform": "zhihu",
        }


zhihu_service = ZhihuService()
