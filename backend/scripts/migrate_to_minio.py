#!/usr/bin/env python3
"""将本地 uploads/ 目录中的已有文件批量迁移到 MinIO（或任意 S3 兼容存储）。

用法：
    # 使用默认值（MinIO 本地 Docker 实例）
    python backend/scripts/migrate_to_minio.py

    # 指定参数
    S3_ENDPOINT_URL=http://localhost:9000 \\
    S3_ACCESS_KEY=minioadmin \\
    S3_SECRET_KEY=minioadmin \\
    S3_BUCKET=opengecko \\
    UPLOAD_DIR=./uploads \\
    python backend/scripts/migrate_to_minio.py

注意：
- 执行前请确保 MinIO 服务已启动（docker compose up minio -d）
- 迁移完成后，将 backend/.env 中的 STORAGE_BACKEND 改为 s3 再重启后端
"""

import os
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("错误：缺少依赖 boto3，请先安装：pip install boto3")
    sys.exit(1)

ENDPOINT = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")
BUCKET = os.environ.get("S3_BUCKET", "opengecko")
LOCAL_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads"))


def main() -> None:
    if not LOCAL_DIR.exists():
        print(f"错误：本地上传目录不存在：{LOCAL_DIR}")
        sys.exit(1)

    print(f"MinIO endpoint : {ENDPOINT}")
    print(f"Bucket         : {BUCKET}")
    print(f"本地目录        : {LOCAL_DIR.resolve()}")
    print()

    try:
        client = boto3.client(
            "s3",
            endpoint_url=ENDPOINT,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name="us-east-1",
        )
    except NoCredentialsError:
        print("错误：S3 凭证无效")
        sys.exit(1)

    # 确保 bucket 存在
    try:
        client.head_bucket(Bucket=BUCKET)
        print(f"Bucket '{BUCKET}' 已存在")
    except ClientError:
        print(f"Bucket '{BUCKET}' 不存在，正在创建…")
        client.create_bucket(Bucket=BUCKET)
        print(f"Bucket '{BUCKET}' 创建成功")

    # 遍历本地文件并上传
    files = [p for p in LOCAL_DIR.rglob("*") if p.is_file()]
    if not files:
        print("本地目录为空，无需迁移")
        return

    print(f"共找到 {len(files)} 个文件，开始上传…\n")
    ok = 0
    fail = 0
    for file_path in files:
        key = str(file_path.relative_to(LOCAL_DIR))
        try:
            client.upload_file(str(file_path), BUCKET, key)
            print(f"  ✓  {key}")
            ok += 1
        except Exception as exc:
            print(f"  ✗  {key}  ({exc})")
            fail += 1

    print(f"\n迁移完成：成功 {ok} 个，失败 {fail} 个")
    if fail:
        print("存在上传失败的文件，请检查错误信息后重试")
        sys.exit(1)
    else:
        print("\n下一步：在 backend/.env 中设置 STORAGE_BACKEND=s3，然后重启后端服务")


if __name__ == "__main__":
    main()
