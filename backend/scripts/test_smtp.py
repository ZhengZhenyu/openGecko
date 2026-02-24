#!/usr/bin/env python3
"""
SMTP 连通性测试脚本
用法：从 backend/ 目录执行:
    python scripts/test_smtp.py --to you@example.com

脚本会读取 backend/.env 中的 SMTP 配置，尝试发一封测试邮件。
如未配置 .env，也可直接传命令行参数（见 --help）。
"""

import argparse
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="测试 SMTP 邮件发送")
    parser.add_argument("--host",     help="SMTP 服务器地址")
    parser.add_argument("--port",     type=int, help="SMTP 端口（465=SSL, 587=STARTTLS）")
    parser.add_argument("--user",     help="SMTP 登录账户")
    parser.add_argument("--password", help="SMTP 密码")
    parser.add_argument("--from-email", dest="from_email", help="发件人地址（默认同 --user）")
    parser.add_argument("--to",       required=True, help="收件人地址（用于验证是否收到）")
    return parser.parse_args()


def load_from_env() -> dict:
    """尝试从 .env 文件/环境变量读取配置。"""
    try:
        import os, pathlib
        # 加载 .env
        env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    # 去除行内注释（# 之前可能有空格）
                    v = v.split(" #")[0].split("\t#")[0].strip()
                    os.environ.setdefault(k.strip(), v)
        return {
            "host":       os.environ.get("SMTP_HOST", ""),
            "port":       int(os.environ.get("SMTP_PORT", "465")),
            "user":       os.environ.get("SMTP_USER", ""),
            "password":   os.environ.get("SMTP_PASSWORD", ""),
            "from_email": os.environ.get("SMTP_FROM_EMAIL", ""),
        }
    except Exception as e:
        print(f"[warn] 读取 .env 失败: {e}")
        return {}


def send_test_email(host: str, port: int, user: str, password: str,
                    from_email: str, to: str) -> None:
    from_email = (from_email or user).strip()
    user = user.strip()
    password = password.strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "openGecko SMTP 连通性测试"
    msg["From"]    = from_email
    msg["To"]      = to
    msg.attach(MIMEText("这是一封 SMTP 测试邮件，收到说明配置正常。", "plain", "utf-8"))
    msg.attach(MIMEText(
        "<p>这是一封 <b>SMTP 测试邮件</b>，收到说明 openGecko 邮箱配置正常 ✅</p>",
        "html", "utf-8",
    ))

    print(f"连接 {host}:{port} …")
    if port == 465:
        print("使用 SMTP_SSL (直连 SSL/TLS)")
        with smtplib.SMTP_SSL(host, port, timeout=30) as server:
            server.set_debuglevel(1)
            server.login(user, password)
            server.sendmail(from_email, [to], msg.as_string())
    else:
        print(f"使用 SMTP + {'STARTTLS' if port == 587 else '明文'}")
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.set_debuglevel(1)
            if port == 587:
                server.starttls()
            server.login(user, password)
            server.sendmail(from_email, [to], msg.as_string())

    print(f"\n✅  测试邮件已发送至 {to}，请检查收件箱（含垃圾箱）。")


def main() -> None:
    args = parse_args()
    env  = load_from_env()

    host       = args.host       or env.get("host", "")
    port       = args.port       or env.get("port", 465)
    user       = args.user       or env.get("user", "")
    password   = args.password   or env.get("password", "")
    from_email = args.from_email or env.get("from_email", "")

    missing = [k for k, v in [("host", host), ("port", port), ("user", user), ("password", password)] if not v]
    if missing:
        print(f"❌  缺少以下参数: {', '.join(missing)}")
        print("    请在 backend/.env 中配置，或通过命令行参数传入（--help 查看用法）")
        sys.exit(1)

    print(f"配置摘要:\n  host={host}  port={port}  user={user}  from={from_email or user}  to={args.to}\n")
    try:
        send_test_email(host, port, user, password, from_email, args.to)
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌  认证失败: {e}\n    请检查账户名和密码是否正确。")
        sys.exit(1)
    except smtplib.SMTPConnectError as e:
        print(f"\n❌  连接失败: {e}\n    请检查 host/port 是否正确，以及网络/防火墙设置。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌  发送失败: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
