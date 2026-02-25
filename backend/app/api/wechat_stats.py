"""微信公众号文章统计 API 路由。

提供文章分类管理、每日统计录入、趋势数据查询、
排名看板等端点。
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_community, get_current_user
from app.database import get_db
from app.models import User
from app.models.publish_record import PublishRecord
from app.schemas.wechat_stats import (
    ArticleCategoryUpdate,
    ArticleRankItem,
    SyncArticlesResponse,
    SyncStatsRequest,
    SyncStatsResponse,
    TrendResponse,
    WechatArticleStatOut,
    WechatDailyStatBatchCreate,
    WechatDailyStatCreate,
    WechatStatsOverview,
)
from app.services.wechat_stats import wechat_stats_service
from app.services.wechat_sync import wechat_sync_service

router = APIRouter()


# ── 概览 ──

@router.get("/overview", response_model=WechatStatsOverview)
def get_wechat_stats_overview(
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取微信公众号统计概览。"""
    return wechat_stats_service.get_overview(db, community_id=community_id)


# ── 趋势数据（折线图） ──

@router.get("/trend", response_model=TrendResponse)
def get_wechat_stats_trend(
    period_type: str = Query(
        default="daily",
        description="统计周期: daily/weekly/monthly/quarterly/semi_annual/annual",
        pattern="^(daily|weekly|monthly|quarterly|semi_annual|annual)$",
    ),
    category: str | None = Query(
        default=None,
        description="文章分类: release/technical/activity，为空则全部",
    ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取微信统计趋势折线图数据。"""
    return wechat_stats_service.get_trend(
        db,
        community_id=community_id,
        period_type=period_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )


# ── 文章排名 ──

@router.get("/ranking", response_model=list[ArticleRankItem])
def get_wechat_article_ranking(
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取微信文章阅读量排名（最新前 N 篇）。"""
    return wechat_stats_service.get_article_ranking(
        db, community_id=community_id, category=category, limit=limit
    )


# ── 单篇文章每日统计 ──

@router.get("/articles/{publish_record_id}/daily", response_model=list[WechatArticleStatOut])
def get_article_daily_stats(
    publish_record_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某篇文章的每日统计数据。"""
    record = db.query(PublishRecord).get(publish_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    return wechat_stats_service.get_article_daily_stats(
        db,
        publish_record_id=publish_record_id,
        start_date=start_date,
        end_date=end_date,
    )


# ── 文章分类管理 ──

@router.put("/articles/{publish_record_id}/category")
def update_article_category(
    publish_record_id: int,
    body: ArticleCategoryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新文章的统计分类。"""
    record = db.query(PublishRecord).get(publish_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    rows = wechat_stats_service.update_article_category(
        db, publish_record_id=publish_record_id, category=body.article_category
    )
    return {"updated": rows, "article_category": body.article_category}


# ── 统计数据录入 ──

@router.post("/daily-stats", response_model=WechatArticleStatOut, status_code=status.HTTP_201_CREATED)
def create_daily_stat(
    body: WechatDailyStatCreate,
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """录入/更新单条每日统计数据。"""
    record = db.query(PublishRecord).get(body.publish_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    if record.channel != "wechat":
        raise HTTPException(status_code=400, detail="仅支持微信渠道的文章")

    return wechat_stats_service.create_daily_stat(
        db, data=body.model_dump(), community_id=community_id
    )


@router.post("/daily-stats/batch", response_model=list[WechatArticleStatOut], status_code=status.HTTP_201_CREATED)
def batch_create_daily_stats(
    body: WechatDailyStatBatchCreate,
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量录入每日统计数据。"""
    return wechat_stats_service.batch_create_daily_stats(
        db, items=[item.model_dump() for item in body.items], community_id=community_id
    )


# ── 聚合重建 ──

@router.post("/aggregates/rebuild")
def rebuild_aggregates(
    period_type: str = Query(
        default="daily",
        pattern="^(daily|weekly|monthly|quarterly|semi_annual|annual)$",
    ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重建统计聚合数据。"""
    count = wechat_stats_service.rebuild_aggregates(
        db,
        community_id=community_id,
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
    )
    return {"rebuilt_count": count, "period_type": period_type}


# ── 微信数据同步 ──

@router.post("/sync/articles", response_model=SyncArticlesResponse)
async def sync_wechat_articles(
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从微信公众号同步已发布文章列表。"""
    try:
        result = await wechat_sync_service.sync_articles(
            db, community_id=community_id, user_id=user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/sync/stats", response_model=SyncStatsResponse)
async def sync_wechat_stats(
    body: SyncStatsRequest,
    community_id: int = Depends(get_current_community),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从微信公众号同步文章阅读统计数据。"""
    if (body.end_date - body.start_date).days > 30:
        raise HTTPException(status_code=400, detail="日期范围不能超过30天")
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
    try:
        result = await wechat_sync_service.sync_stats(
            db,
            community_id=community_id,
            start_date=body.start_date,
            end_date=body.end_date,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
