from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.people import PersonProfile


def find_or_suggest(db: Session, row: dict) -> dict:
    """对导入的单行记录执行去重匹配。

    匹配优先级：
    1. github_handle 精确匹配 → matched
    2. email 精确匹配 → suggest (reason: email)
    3. 姓名 + 公司模糊匹配 (ratio > 0.70) → suggest (reason: name+company)
    4. 均未匹配 → new

    Returns:
        {
            "status": "matched" | "suggest" | "new",
            "person_id": int | None,   # matched 时有值
            "candidates": list[dict],  # suggest 时有值
        }
    """
    github = row.get("github_handle", "").strip().lower()
    email = row.get("email", "").strip().lower()
    name = row.get("display_name", "").strip()
    company = row.get("company", "").strip()

    # 1. github_handle 精确匹配
    if github:
        p = db.query(PersonProfile).filter(PersonProfile.github_handle == github).first()
        if p:
            return {"status": "matched", "person_id": p.id, "candidates": []}

    # 2. email 精确匹配 → 疑似（可能同名不同人，需人工确认）
    if email:
        p = db.query(PersonProfile).filter(PersonProfile.email == email).first()
        if p:
            return {
                "status": "suggest",
                "person_id": None,
                "candidates": [{"id": p.id, "display_name": p.display_name, "reason": "email"}],
            }

    # 3. 姓名 + 公司模糊匹配
    if name:
        candidates = []
        query_str = f"{name}|{company}"
        for p in (
            db.query(PersonProfile)
            .filter(PersonProfile.display_name.ilike(f"%{name[:4]}%"))
            .limit(50)
        ):
            target_str = f"{p.display_name}|{p.company or ''}"
            ratio = SequenceMatcher(None, query_str, target_str).ratio()
            if ratio > 0.70:
                candidates.append({
                    "id": p.id,
                    "display_name": p.display_name,
                    "company": p.company,
                    "ratio": round(ratio, 2),
                    "reason": "name+company",
                })
        if candidates:
            return {
                "status": "suggest",
                "person_id": None,
                "candidates": sorted(candidates, key=lambda x: -x["ratio"]),
            }

    return {"status": "new", "person_id": None, "candidates": []}
