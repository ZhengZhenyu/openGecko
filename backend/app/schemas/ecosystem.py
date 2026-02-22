from datetime import datetime

from pydantic import BaseModel

# ─── EcosystemProject ─────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    platform: str           # github / gitee / gitcode
    org_name: str
    repo_name: str | None = None
    description: str | None = None
    tags: list[str] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class ProjectListOut(BaseModel):
    id: int
    name: str
    platform: str
    org_name: str
    repo_name: str | None
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectOut(ProjectListOut):
    description: str | None
    tags: list[str]
    added_by_id: int | None

    model_config = {"from_attributes": True}


# ─── EcosystemContributor ─────────────────────────────────────────────────────

class ContributorOut(BaseModel):
    id: int
    project_id: int
    github_handle: str
    display_name: str | None
    avatar_url: str | None
    role: str | None
    commit_count_90d: int | None
    pr_count_90d: int | None
    star_count: int | None
    followers: int | None
    person_id: int | None
    last_synced_at: datetime

    model_config = {"from_attributes": True}


class PaginatedContributors(BaseModel):
    items: list[ContributorOut]
    total: int
    page: int
    page_size: int


# ─── Sync Result ──────────────────────────────────────────────────────────────

class SyncResult(BaseModel):
    created: int
    updated: int
    errors: int
