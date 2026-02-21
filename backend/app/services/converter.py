import os
import uuid

import html2text
import mammoth
import markdown

from app.config import settings

# Module-level constants — created once, reused across all calls
_MD_EXTENSIONS = ["extra", "codehilite", "tables", "toc", "nl2br"]
_MD_EXTENSION_CONFIGS = {
    "codehilite": {
        "css_class": "highlight",
        "linenums": False,
    }
}


def convert_docx_to_markdown(docx_path: str) -> tuple[str, list[str]]:
    """Convert a WORD .docx file to Markdown.

    Returns:
        tuple of (markdown_text, list_of_image_paths)
    """
    image_paths = []
    image_dir = os.path.join(settings.UPLOAD_DIR, "images")
    os.makedirs(image_dir, exist_ok=True)

    def convert_image(image):
        image_ext = image.content_type.split("/")[-1] if image.content_type else "png"
        image_name = f"{uuid.uuid4().hex}.{image_ext}"
        image_path = os.path.join(image_dir, image_name)
        with open(image_path, "wb") as f:
            with image.open() as img_stream:
                f.write(img_stream.read())
        rel_path = f"/uploads/images/{image_name}"
        image_paths.append(rel_path)
        return {"src": rel_path}

    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f, convert_image=mammoth.images.img_element(convert_image))

    html_content = result.value

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    h2t.protect_links = True
    h2t.wrap_links = False
    h2t.single_line_break = False
    markdown_text = h2t.handle(html_content)

    return markdown_text.strip(), image_paths


def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(md_text, extensions=_MD_EXTENSIONS, extension_configs=_MD_EXTENSION_CONFIGS)


def read_markdown_file(file_path: str) -> str:
    """Read a .md file and return its content."""
    with open(file_path, encoding="utf-8") as f:
        return f.read().strip()
