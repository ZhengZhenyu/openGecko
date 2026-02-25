---
name: github-pr
description: Create a GitHub issue and a linked pull request for openGecko contributions. Use this skill when the user asks to "create a PR", "submit a PR", "open a PR", "create an issue and PR", or similar requests targeting the opensourceways/openGecko repository.
---

# GitHub Issue + PR Workflow for openGecko

## Overview

This skill creates a feature/fix GitHub issue on the upstream repository (`opensourceways/openGecko`) and then opens a pull request from the contributor's personal fork that closes the issue. It **never hardcodes a username** — all identifiers are derived at runtime from the repository's git remotes.

## Repository Conventions

| Remote name | Points to |
|-------------|-----------|
| `upstream`  | `opensourceways/openGecko` (the canonical repo; issue and PR target) |
| `origin`    | contributor's personal fork (PR source) |

---

## Issue Templates

The project uses **GitHub YAML form templates** in `.github/ISSUE_TEMPLATE/`. Because they are `.yml` (not `.md`), `gh issue create --template` **cannot** use them directly — `--template` only accepts `.md` files.

**Approach:** When creating an issue via CLI, compose the body manually to mirror the relevant template's sections. Alternatively, open the GitHub web UI where the form renders interactively.

### Choosing the Right Template

| Commit prefix | Change type | Issue template | Title prefix |
|---------------|-------------|----------------|--------------|
| `feat:` | New feature or enhancement | Feature Request | `[Feature]: ` |
| `fix:` | Bug fix | Bug Report | `[Bug]: ` |
| `docs:` | Documentation improvement | Documentation | `[Docs]: ` |
| `refactor:` | Code refactoring (no behaviour change) | Feature Request (or skip issue) | `[Feature]: ` |
| `test:` / `chore:` | Tests / build / CI changes | Feature Request (or skip issue) | — |
| Governance-related | Committee / meeting / member features | Governance Task | `[Governance]: ` |

### Body Sections by Template Type

#### Feature Request (`feat:`)
```
## Problem Statement
What problem does this solve?

## Proposed Solution
Describe the feature:
- Backend changes (API, model, schema)
- Frontend changes (components, views)
- User stories: As a [role], I want [feature] so that [benefit]

## Use Cases
1. ...
2. ...

## Acceptance Criteria
- [ ] ...
- [ ] ...

## Design Considerations
- Database schema changes needed?
- Performance implications?
- Security concerns?

## Additional Context
Related docs, links, screenshots.
```

#### Bug Report (`fix:`)
```
## Bug Description
A clear description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click '...'
3. See error

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens. Include error messages.

## Environment
- OS: ...
- Browser: ...
- Backend/Frontend version: ...
- Database: SQLite / PostgreSQL

## Error Logs
(paste relevant logs)
```

#### Documentation (`docs:`)
```
## Problem Description
What is missing, incorrect, or unclear?

## Current Documentation
(paste or link to current content)

## Suggested Improvement
What the documentation should say.
```

#### Governance Task (`[Governance]:`)
```
## Task Description
What needs to be implemented and why.

## Acceptance Criteria
- [ ] Backend API endpoint implemented
- [ ] Database migration created
- [ ] Frontend UI implemented
- [ ] Unit tests added (coverage ≥ 80%)

## Technical Details
**Database Changes:** ...
**API Design:** endpoint, request body, response
**Dependencies:** Depends on #..., Blocks #...

## Test Plan
Unit tests / Integration tests / Manual testing steps
```

---

## Step-by-Step Workflow

### Step 1 — Detect fork information

```bash
# Derive the upstream repo slug (should be opensourceways/openGecko)
UPSTREAM_SLUG=$(git remote get-url upstream | sed 's|.*github.com[:/]\(.*\)\.git|\1|; s|.*github.com[:/]\(.*\)|\1|')

# Derive the contributor's GitHub username from origin
FORK_URL=$(git remote get-url origin)
# Works for both SSH (git@github.com:user/repo.git) and HTTPS (https://github.com/user/repo)
FORK_USER=$(echo "$FORK_URL" | sed 's|.*github.com[:/]\([^/]*\)/.*|\1|')

# Current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Upstream: $UPSTREAM_SLUG"
echo "Fork user: $FORK_USER"
echo "Branch: $BRANCH"
```

### Step 2 — Create the issue on upstream

Determine the commit prefix from the changes (see table above), then create the issue using the matching body structure.

```bash
ISSUE_URL=$(gh issue create \
  --repo "$UPSTREAM_SLUG" \
  --title "[Feature]: <concise title>" \
  --body "$(cat <<'BODY'
## Problem Statement
...

## Proposed Solution
...

## Use Cases
1. ...

## Acceptance Criteria
- [ ] ...

## Design Considerations
...
BODY
)")
echo "Issue: $ISSUE_URL"
# Extract issue number
ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')
```

### Step 3 — Push the branch to fork

Check whether origin is up to date first; pull+rebase if behind.

```bash
# Check if ahead/behind
git fetch origin "$BRANCH" 2>/dev/null
BEHIND=$(git rev-list --count "HEAD..origin/$BRANCH" 2>/dev/null || echo 0)

if [ "$BEHIND" -gt 0 ]; then
  git pull origin "$BRANCH" --rebase
fi

git push origin "$BRANCH"
```

### Step 4 — Create the pull request

The PR title prefix must match the issue/commit type (`feat:`, `fix:`, `docs:`, etc.).

```bash
gh pr create \
  --repo "$UPSTREAM_SLUG" \
  --base main \
  --head "${FORK_USER}:${BRANCH}" \
  --title "feat: <same title as issue>" \
  --body "$(cat <<'BODY'
## 关联 Issue

Closes #<ISSUE_NUM>

## 变更概述
<1-3 bullet points summarising what changed>

## 主要变更

### 后端
- ...

### 前端
- ...

### 测试
- ...

## 测试验证

```
<test result summary, e.g. 555 passed, 3 skipped>
```

## 测试计划

- [x] ...
- [x] ...
BODY
)"
```

---

## Alternatives to `gh` CLI

If `gh` is not installed or not authenticated, use one of these alternatives:

### Option A — GitHub REST API via `curl`

```bash
# Create issue
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/opensourceways/openGecko/issues \
  -d "{\"title\":\"[Feature]: your title\",\"body\":\"## Problem Statement\\n...\"}"

# Create PR (after pushing branch)
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/opensourceways/openGecko/pulls \
  -d "{\"title\":\"feat: your title\",\"head\":\"${FORK_USER}:${BRANCH}\",\"base\":\"main\",\"body\":\"Closes #N\\n...\"}"
```

Set `GITHUB_TOKEN` with a personal access token (PAT) that has `repo` scope.

### Option B — GitHub Web UI

Open these URLs in a browser:

```bash
# Create issue from form template (recommended — renders the YAML form correctly)
echo "https://github.com/opensourceways/openGecko/issues/new/choose"

# Create PR after pushing branch
echo "https://github.com/opensourceways/openGecko/compare/main...${FORK_USER}:${BRANCH}"
```

The web UI is especially recommended when using the YAML form templates, since they render as interactive forms with dropdowns and checkboxes that are impossible to fully reproduce via CLI.

### Option C — `hub` CLI (legacy alternative to `gh`)

```bash
# hub is the older GitHub CLI; gh is the official successor
hub issue create -m "[Feature]: title" -l "enhancement"
hub pull-request -m "feat: title" -b opensourceways/openGecko:main -h "${FORK_USER}:${BRANCH}"
```

Install: `brew install hub` (macOS) or `apt install hub` (Ubuntu).

---

## Key Rules

1. **Never hardcode a GitHub username** — always derive from `git remote get-url origin`.
2. **Issue first, then PR** — the issue number must be known before creating the PR body so `Closes #N` links correctly.
3. **Push before PR** — `gh pr create` will fail if the branch does not exist on the fork remote.
4. **Rebase, don't merge** — if `origin` is ahead, use `git pull --rebase` to keep a clean linear history.
5. **Branch matters** — always use `--head "${FORK_USER}:${BRANCH}"` so the PR targets the correct branch of the fork.
6. **Match commit prefix to template** — `feat:` → Feature Request, `fix:` → Bug Report, `docs:` → Documentation, `[Governance]:` → Governance Task.
7. **PR body language** — section headers and user-facing text in Chinese; code, variable names, and CLI output in English (matches project language conventions).
8. **YAML templates can't be used with `--template`** — compose body manually to mirror template sections, or use the web UI.
9. **Single commit per PR (no `needs-squash`)** — the upstream CI bot adds a `needs-squash` label that **blocks merging** when a PR contains more than one commit. Always squash all commits into one before pushing:
   ```bash
   # Squash all commits since upstream/main into one (no interactive editor needed)
   git reset --soft upstream/main
   git commit -m 'type: concise commit message'
   git push origin "$BRANCH" --force-with-lease
   ```

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| `origin` remote is HTTPS (`https://github.com/user/repo`) | The `sed` expression handles both SSH and HTTPS formats |
| `origin` remote has no `.git` suffix | The `sed` expression handles both with and without `.git` |
| Branch already pushed to fork but has diverged | `git pull origin "$BRANCH" --rebase` then push again |
| User is already on `main` | PR from `${FORK_USER}:main` to `upstream:main` works normally; make sure all commits are pushed |
| `upstream` remote not configured | Inform the user: `git remote add upstream https://github.com/opensourceways/openGecko.git` |
| `gh` not installed | Use Option B (web UI) or Option A (`curl` + PAT) from the Alternatives section above |
| PR has `needs-squash` label | Run `git reset --soft upstream/main && git commit -m 'type: message' && git push origin "$BRANCH" --force-with-lease` to squash all commits into one |

---

## Example Invocation

When a user says **"帮我创建一个 PR，把这次的功能提交到上游"**, execute:

```bash
# 1. Detect
UPSTREAM_SLUG="opensourceways/openGecko"
FORK_USER=$(git remote get-url origin | sed 's|.*github.com[:/]\([^/]*\)/.*|\1|')
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 2. Issue (feat: → Feature Request body structure)
ISSUE_URL=$(gh issue create --repo "$UPSTREAM_SLUG" --title "[Feature]: ..." --body "...")
ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

# 3. Push
git push origin "$BRANCH"

# 4. PR
gh pr create --repo "$UPSTREAM_SLUG" --base main --head "${FORK_USER}:${BRANCH}" \
  --title "feat: ..." --body "Closes #${ISSUE_NUM} ..."
```

Return both the issue URL and PR URL to the user.
