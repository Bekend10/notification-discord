import os
import hmac
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv
load_dotenv()
import httpx
from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI(title="GitLab -> Discord notifier")

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
GITLAB_WEBHOOK_TOKEN = os.environ.get("GITLAB_WEBHOOK_TOKEN", "").strip()

if not DISCORD_WEBHOOK_URL:
    print("WARNING: DISCORD_WEBHOOK_URL is not set")
if not GITLAB_WEBHOOK_TOKEN:
    print("WARNING: GITLAB_WEBHOOK_TOKEN is not set")


def _safe_get(d: Dict[str, Any], *keys, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def build_discord_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # GitLab "Pull Request" ~= "Merge Request"
    if payload.get("object_kind") != "merge_request":
        return None

    attrs = payload.get("object_attributes", {})
    action = (attrs.get("action") or "update").lower()  # open/update/merge/close/reopen/approved...
    # Lọc action nếu muốn (gợi ý):
    # if action not in {"open", "merge", "reopen", "close"}:
    #     return None

    project = _safe_get(payload, "project", "path_with_namespace", default="unknown/project")
    iid = attrs.get("iid")
    title = attrs.get("title", "(no title)")
    state = attrs.get("state", "unknown")
    src = attrs.get("source_branch", "?")
    tgt = attrs.get("target_branch", "?")

    # Link MR: tuỳ GitLab version có thể là "url" hoặc "web_url"
    link = attrs.get("url") or attrs.get("web_url") or _safe_get(payload, "object_attributes", "url", default="")

    author_name = _safe_get(payload, "user", "name", default="Unknown")
    author_username = _safe_get(payload, "user", "username", default=None)
    author_display = f"@{author_username}" if author_username else author_name

    reviewers = payload.get("reviewers") or []
    reviewers_str = ", ".join(
        [("@" + r.get("username") if r.get("username") else r.get("name", "unknown")) for r in reviewers]
    ) or "—"

    assignees = payload.get("assignees") or []
    assignees_str = ", ".join(
        [("@" + a.get("username") if a.get("username") else a.get("name", "unknown")) for a in assignees]
    ) or "—"

    # Thời gian tạo MR
    created_at = attrs.get("created_at", "Unknown")
    
    # Trạng thái conflict
    merge_status = attrs.get("merge_status", "unknown")
    has_conflicts = "❌ Yes" if merge_status in ["cannot_be_merged", "unchecked"] else "✅ No"

    # Emoji + title theo action
    icon = {"open": "🆕", "merge": "✅", "close": "🛑", "reopen": "♻️", "approved": "👍"}.get(action, "🔔")
    embed_title = f"{icon} [{action.upper()}] {project} !{iid}"

    fields: List[Dict[str, Any]] = [
        {"name": "Title", "value": title[:1024], "inline": False},
        {"name": "Branch", "value": f"`{src}` → `{tgt}`", "inline": True},
        {"name": "State", "value": f"`{state}`", "inline": True},
        {"name": "Created", "value": created_at, "inline": True},
        {"name": "Conflicts", "value": has_conflicts, "inline": True},
        {"name": "Author", "value": author_display, "inline": True},
        {"name": "Assignees", "value": assignees_str[:1024], "inline": False},
        {"name": "Reviewers", "value": reviewers_str[:1024], "inline": False},
    ]

    embed: Dict[str, Any] = {
        "title": embed_title[:256],
        "fields": fields,
    }
    if link:
        embed["url"] = link

    # Discord webhook payload
    return {
        "content": "",  # có thể bỏ trống hoặc set text chung
        "embeds": [embed],
        "allowed_mentions": {"parse": []},  # tránh ping @everyone/@here ngoài ý muốn
    }


async def post_to_discord(payload: Dict[str, Any]) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(DISCORD_WEBHOOK_URL, json=payload)
        if r.status_code >= 300:
            raise HTTPException(status_code=502, detail=f"Discord error: {r.status_code} {r.text}")


@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
):
    # Debug: print ALL headers
    print("\n=== ALL Received Headers ===")
    for header_name, header_value in request.headers.items():
        # Mask sensitive data but show structure
        if "token" in header_name.lower() or "secret" in header_name.lower():
            print(f"{header_name}: {header_value[:10]}..." if len(header_value) > 10 else f"{header_name}: {header_value}")
        else:
            print(f"{header_name}: {header_value}")
    print("=== End Headers ===\n")
    
    # Try to get token from various possible header names
    token = (
        request.headers.get("X-Gitlab-Token") or
        request.headers.get("x-gitlab-token") or
        request.headers.get("X-GitLab-Token")
    )
    
    # Temporarily disable token check for debugging
    print(f"Expected token: {GITLAB_WEBHOOK_TOKEN}")
    print(f"Received token: {token}")
    
    # TEMPORARY: Comment out validation to see payload
    # if GITLAB_WEBHOOK_TOKEN:
    #     if not token or not hmac.compare_digest(token, GITLAB_WEBHOOK_TOKEN):
    #         raise HTTPException(status_code=401, detail="Invalid X-Gitlab-Token")

    data = await request.json()
    print(f"Event type: {data.get('object_kind')}")
    print(f"Action: {data.get('object_attributes', {}).get('action')}")
    
    out = build_discord_payload(data)
    if out is None:
        return {"ok": True, "ignored": True}

    await post_to_discord(out)
    return {"ok": True}
