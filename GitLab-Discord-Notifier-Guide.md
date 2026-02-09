# GitLab → Discord Notifier (Python/FastAPI)

Tài liệu này hướng dẫn bạn dựng một service nhỏ bằng **Python (FastAPI)** để nhận webhook từ **GitLab Merge Request (PR)** và gửi thông báo sang **Discord** bằng **Discord Webhook**.

---

## 1) Chuẩn bị

### Yêu cầu
- Python 3.10+ (khuyên dùng 3.11)
- GitLab (self-host hoặc SaaS)
- Discord server + quyền tạo webhook
- Server public (hoặc dùng ngrok để test)

---

## 2) Tạo Discord Webhook

1. Vào Discord Server → chọn kênh bạn muốn nhận thông báo
2. **Edit Channel** → **Integrations** → **Webhooks**
3. **New Webhook**
4. Đặt tên (ví dụ: `GitLab Bot`)
5. Copy **Webhook URL** dạng:

```
https://discord.com/api/webhooks/<id>/<token>
```

---

## 3) Tạo GitLab Webhook

Trong GitLab project:

- Project → **Settings** → **Webhooks**
- URL:  
  `https://<YOUR_DOMAIN>/gitlab/webhook`
- Tick: **Merge request events**
- Secret token: đặt 1 chuỗi bí mật, ví dụ:  
  `supersecret123`
- Save

Bạn có thể bấm **Test** → Merge request events để gửi thử.

---

## 4) Tạo source code

Tạo folder dự án, ví dụ:

```
gitlab-discord-notifier/
```

### 4.1) File `main.py`
Copy code dưới đây:

```python
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

    project = _safe_get(payload, "project", "path_with_namespace", default="unknown/project")
    iid = attrs.get("iid")
    title = attrs.get("title", "(no title)")
    state = attrs.get("state", "unknown")
    src = attrs.get("source_branch", "?")
    tgt = attrs.get("target_branch", "?")

    # Link MR: ưu tiên web_url (thường là link đúng để click)
    link = attrs.get("web_url") or attrs.get("url") or ""

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

    # Emoji + title theo action
    icon = {"open": "🆕", "merge": "✅", "close": "🛑", "reopen": "♻️", "approved": "👍"}.get(action, "🔔")
    embed_title = f"{icon} [{action.upper()}] {project} !{iid}"

    fields: List[Dict[str, Any]] = [
        {"name": "Title", "value": title[:1024], "inline": False},
        {"name": "Branch", "value": f"`{src}` → `{tgt}`", "inline": True},
        {"name": "State", "value": f"`{state}`", "inline": True},
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
        "content": "",
        "embeds": [embed],
        "allowed_mentions": {"parse": []},  # tránh ping @everyone/@here ngoài ý muốn
    }


async def post_to_discord(payload: Dict[str, Any]) -> None:
    if not DISCORD_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="DISCORD_WEBHOOK_URL is not set")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(DISCORD_WEBHOOK_URL, json=payload)
        if r.status_code >= 300:
            raise HTTPException(status_code=502, detail=f"Discord error: {r.status_code} {r.text}")


@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: Optional[str] = Header(default=None, convert_underscores=False),
):
    # Verify secret token (GitLab header: X-Gitlab-Token)
    if GITLAB_WEBHOOK_TOKEN:
        if not x_gitlab_token or not hmac.compare_digest(x_gitlab_token, GITLAB_WEBHOOK_TOKEN):
            raise HTTPException(status_code=401, detail="Invalid X-Gitlab-Token")

    data = await request.json()
    out = build_discord_payload(data)
    if out is None:
        return {"ok": True, "ignored": True, "object_kind": data.get("object_kind")}

    await post_to_discord(out)
    return {"ok": True}
```

### 4.2) File `requirements.txt`
```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
python-dotenv==1.0.1
```

### 4.3) File `.env`
Tạo file `.env` cùng thư mục với `main.py`:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY
GITLAB_WEBHOOK_TOKEN=supersecret123
```

> Lưu ý: đừng commit `.env` lên Git. Nên thêm `.env` vào `.gitignore`.

---

## 5) Chạy local (không Docker)

### 5.1) Cài thư viện
```bash
pip install -r requirements.txt
```

### 5.2) Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Endpoint webhook:
```
http://localhost:8000/gitlab/webhook
```

---

## 6) Test nhanh bằng ngrok (khuyên dùng)

Nếu bạn chạy local nhưng muốn GitLab gọi được webhook:

```bash
ngrok http 8000
```

Ngrok sẽ trả về URL kiểu:
```
https://xxxx-xx-xx-xx.ngrok-free.app
```

Khi đó bạn set GitLab webhook URL thành:
```
https://xxxx-xx-xx-xx.ngrok-free.app/gitlab/webhook
```

---

## 7) Docker hoá (deploy nhanh)

### 7.1) File `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2) File `docker-compose.yml`
```yaml
services:
  gitlab-discord:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

### 7.3) Run
```bash
docker compose up -d --build
```

---

## 8) Troubleshooting

### 8.1) GitLab báo webhook failed
- Kiểm tra URL đúng chưa
- Service có public không (nếu local thì phải dùng ngrok)
- Nếu dùng HTTPS self-signed → tắt SSL verify ở GitLab hoặc dùng cert chuẩn

### 8.2) Discord không nhận
- Check `DISCORD_WEBHOOK_URL`
- Thử curl:
```bash
curl -X POST -H "Content-Type: application/json"   -d '{"content":"hello from webhook"}'   "https://discord.com/api/webhooks/XXX/YYY"
```

### 8.3) Lỗi 401 Invalid X-Gitlab-Token
- Kiểm tra Secret token GitLab có đúng với `GITLAB_WEBHOOK_TOKEN` trong `.env` không

---

## 9) Tuỳ biến thêm (gợi ý)

- Chỉ notify khi mở/merge MR:
  Trong `build_discord_payload`, bật filter:

```python
if action not in {"open", "merge", "reopen", "close"}:
    return None
```

- Route theo label (nhiều Discord channels):
  Bạn tạo nhiều webhook URL và map theo label.

- Mention reviewer/assignee:
  Cần mapping GitLab username → Discord userId.

---

Nếu bạn muốn, mình có thể giúp bạn:
- thêm pipeline status (success/fail)
- route theo label
- viết bản deploy lên Kubernetes
