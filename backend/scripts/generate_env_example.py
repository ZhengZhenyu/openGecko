#!/usr/bin/env python3
"""
自动从 Pydantic Settings 类生成 .env.example 文件。

用法：
    cd backend
    python scripts/generate_env_example.py                      # 生成到 .env.example（默认）
    python scripts/generate_env_example.py --out .env.new       # 输出到指定文件
    python scripts/generate_env_example.py --check              # diff 模式：检查现有文件是否过时
    python scripts/generate_env_example.py --prod               # 生成 .env.prod.example

原理：读取 app/config.py 中 Settings 类的 model_fields，提取
    - 字段名（KEY）
    - 默认值
    - description（用作注释）
以「# ─ 分组注释 ─」为节标题分组，输出格式化的 .env 文件。

在 CI 中可用 --check 模式防止 config.py 与 .env.example 脱节：
    python scripts/generate_env_example.py --check || exit 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# ── 把 backend/ 加入 sys.path，以便直接 import app.config ──────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings  # noqa: E402

# ── 分节映射：字段名前缀 → 节标题（顺序即生成顺序）─────────────────────
SECTION_MAP: list[tuple[str, str]] = [
    ("DATABASE_URL|DB_",            "数据库"),
    ("JWT_|ACCESS_TOKEN_",          "安全 / JWT"),
    ("CORS_",                       "CORS 跨域"),
    ("RATE_LIMIT_",                 "速率限制"),
    ("DEFAULT_ADMIN_",              "初始管理员（仅首次启动时创建）"),
    ("SMTP_",                       "SMTP 邮件（可选，用于密码重置和通知）"),
    ("FRONTEND_URL",                "前端地址（密码重置邮件跳转链接）"),
    ("STORAGE_BACKEND|UPLOAD_DIR|MAX_UPLOAD_SIZE", "文件存储"),
    ("S3_",                         "S3 / MinIO 对象存储（STORAGE_BACKEND=s3 时填写）"),
    ("APP_TIMEZONE",                "时区"),
    ("GITHUB_TOKEN|GITEE_TOKEN|COLLECTOR_", "生态洞察采集服务"),
    ("ENABLE_",                     "可选功能模块"),
    ("HOST|PORT|DEBUG|LOG_",        "服务器"),
    ("APP_NAME",                    "应用"),
]

# 完全跳过这些字段（不写入 .env 模板）
SKIP_FIELDS: set[str] = {
    "UPLOAD_DIR",    # 由 config.py 从 __file__ 自动派生，写入模板无意义且含绝对路径
}

# 在开发模板中对这些字段使用注释掉的形式（可选项）
DEV_COMMENTED: set[str] = {
    "DB_POOL_SIZE", "DB_MAX_OVERFLOW", "DB_POOL_TIMEOUT", "DB_POOL_RECYCLE", "DB_ECHO",
    "CORS_ORIGINS",
    "RATE_LIMIT_LOGIN", "RATE_LIMIT_DEFAULT",
    "STORAGE_BACKEND", "UPLOAD_DIR", "MAX_UPLOAD_SIZE",
    "S3_ENDPOINT_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET", "S3_PUBLIC_URL",
    "GITHUB_TOKEN", "GITEE_TOKEN",
    "COLLECTOR_SYNC_INTERVAL_HOURS", "COLLECTOR_MAX_WORKERS",
    "COLLECTOR_CHECK_INTERVAL_SECONDS", "COLLECTOR_EMBEDDED",
    "ENABLE_INSIGHTS_MODULE",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", "SMTP_USE_TLS",
    "FRONTEND_URL",
    "APP_NAME", "JWT_ALGORITHM",
    "LOG_LEVEL", "HOST", "PORT",
}

# 生产模板中这些字段使用 REPLACE_WITH_... 占位符
PROD_MUST_REPLACE: dict[str, str] = {
    "JWT_SECRET_KEY":          "REPLACE_WITH_STRONG_RANDOM_KEY_32_BYTES_HEX",
    "DEFAULT_ADMIN_PASSWORD":  "REPLACE_WITH_STRONG_INITIAL_PASSWORD",
    "DEFAULT_ADMIN_EMAIL":     "admin@your-domain.com",
    "DATABASE_URL":            "postgresql://opengecko:YOUR_DB_PASSWORD@db:5432/opengecko",
    "CORS_ORIGINS":            "https://your-domain.com",
    "S3_ACCESS_KEY":           "REPLACE_WITH_MINIO_ACCESS_KEY",
    "S3_SECRET_KEY":           "REPLACE_WITH_MINIO_SECRET_KEY",
}


# ── 工具函数 ────────────────────────────────────────────────────────────

def _match_section(field_name: str) -> str | None:
    """根据字段名匹配节标题，返回第一个匹配的节标题；无匹配返回 None。"""
    for patterns, title in SECTION_MAP:
        for pat in patterns.split("|"):
            if field_name.startswith(pat) or field_name == pat:
                return title
    return None


def _default_str(value: Any) -> str:
    """将默认值转换为 .env 格式字符串。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def generate(prod: bool = False) -> str:
    """生成 .env 内容字符串。"""
    fields = Settings.model_fields

    # 按节分组
    sections: dict[str, list[tuple[str, Any, str]]] = {}  # title → [(name, default, desc)]
    uncategorized: list[tuple[str, Any, str]] = []

    for field_name, field_info in fields.items():
        key = field_name.upper()
        if key in SKIP_FIELDS:
            continue
        default = field_info.default
        desc = field_info.description or ""
        title = _match_section(key)
        if title:
            sections.setdefault(title, []).append((key, default, desc))
        else:
            uncategorized.append((key, default, desc))

    env_header = (
        "# =====================================================================\n"
        + ("# openGecko 生产环境配置模板\n" if prod else "# openGecko 开发环境配置模板\n")
        + "# 此文件由 backend/scripts/generate_env_example.py 自动生成\n"
        + ("# 复制为 backend/.env：  cp backend/.env.prod.example backend/.env\n" if prod
           else "# 复制为 backend/.env：  cp backend/.env.example backend/.env\n")
        + ("# 开发环境请参考 backend/.env.example\n" if prod
           else "# 生产环境请参考 backend/.env.prod.example\n")
        + "# =====================================================================\n\n"
    )

    lines: list[str] = [env_header]

    # 按 SECTION_MAP 顺序输出
    seen_titles: set[str] = set()
    for _, title in SECTION_MAP:
        if title not in sections or title in seen_titles:
            continue
        seen_titles.add(title)
        lines.append(f"# {'─' * 69}\n")
        lines.append(f"# {title}\n")
        lines.append(f"# {'─' * 69}\n")

        for key, default, desc in sections[title]:
            # 描述折行：每行注释文字不超过 76 个字符（含「# "前缀）
            if desc:
                import textwrap
                for para in desc.split("；"):
                    para = para.strip()
                    if not para:
                        continue
                    wrapped = textwrap.wrap(para, width=74,
                                           break_long_words=False,
                                           break_on_hyphens=False)
                    for w_line in wrapped:
                        lines.append(f"# {w_line}\n")

            if prod:
                raw_val = PROD_MUST_REPLACE.get(key, _default_str(default))
            else:
                raw_val = _default_str(default)

            commented = (not prod) and (key in DEV_COMMENTED)
            prefix = "# " if commented else ""
            lines.append(f"{prefix}{key}={raw_val}\n")

        lines.append("\n")

    # 未分类字段
    if uncategorized:
        lines.append("# ─────────────────────────────────────────────────────────────────────\n")
        lines.append("# 其他配置\n")
        lines.append("# ─────────────────────────────────────────────────────────────────────\n")
        import textwrap
        for key, default, desc in uncategorized:
            if desc:
                for w_line in textwrap.wrap(desc, width=74, break_long_words=False):
                    lines.append(f"# {w_line}\n")
            lines.append(f"{key}={_default_str(default)}\n")
        lines.append("\n")

    return "".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="从 Pydantic Settings 生成 .env.example")
    parser.add_argument("--out",   default=None,   help="输出文件路径（默认自动决定）")
    parser.add_argument("--check", action="store_true", help="diff 模式：检查现有文件是否过时")
    parser.add_argument("--prod",  action="store_true", help="生成生产环境模板（.env.prod.example）")
    args = parser.parse_args()

    content = generate(prod=args.prod)

    default_out = BACKEND_DIR / (".env.prod.example" if args.prod else ".env.example")
    out_path = Path(args.out) if args.out else default_out

    if args.check:
        if not out_path.exists():
            print(f"❌ {out_path} 不存在，请先运行生成命令", file=sys.stderr)
            sys.exit(1)
        existing = out_path.read_text(encoding="utf-8")
        if existing == content:
            print(f"✅ {out_path} 与 config.py 保持同步")
        else:
            import difflib
            diff = difflib.unified_diff(
                existing.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=str(out_path),
                tofile="generated",
            )
            print("".join(diff))
            print(f"\n⚠️  {out_path} 已过时，请运行：python scripts/generate_env_example.py",
                  file=sys.stderr)
            sys.exit(1)
        return

    out_path.write_text(content, encoding="utf-8")
    print(f"✅ 已生成: {out_path}")


if __name__ == "__main__":
    main()
