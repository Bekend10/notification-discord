# Deploy GitLab → Discord Notifier lên Cloud

## 🚀 Option 1: Render.com (Free tier)

### Bước 1: Chuẩn bị
1. Push code lên GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### Bước 2: Deploy trên Render.com
1. Vào [render.com](https://render.com) → Sign up/Login
2. **New** → **Blueprint** (hoặc **Web Service** nếu không dùng render.yaml)
3. Connect GitHub repository
4. Render sẽ tự detect file `render.yaml`

### Bước 3: Cấu hình Environment Variables
Trong Render dashboard, thêm:
- `DISCORD_WEBHOOK_URL`: `https://discord.com/api/webhooks/...`
- `GITLAB_WEBHOOK_TOKEN`: `chamchi123`

### Bước 4: Deploy
- Click **Create Web Service**
- Chờ build (3-5 phút)
- Lấy URL: `https://gitlab-discord-notifier.onrender.com`

### Bước 5: Cấu hình GitLab Webhook
URL: `https://gitlab-discord-notifier.onrender.com/gitlab/webhook`

---

## 🚂 Option 2: Railway.app (Free $5/month credit)

### Bước 1: Chuẩn bị
Push code lên GitHub (như trên)

### Bước 2: Deploy trên Railway
1. Vào [railway.app](https://railway.app) → Login with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Chọn repository `notification-discord`
4. Railway auto-detect Dockerfile

### Bước 3: Add Environment Variables
Trong Railway dashboard:
- Click **Variables** tab
- Add:
  - `DISCORD_WEBHOOK_URL` = `https://discord.com/api/webhooks/...`
  - `GITLAB_WEBHOOK_TOKEN` = `chamchi123`

### Bước 4: Tạo Public Domain
- Click **Settings** → **Networking**
- **Generate Domain**
- Lấy URL: `https://your-app.up.railway.app`

### Bước 5: Cấu hình GitLab Webhook
URL: `https://your-app.up.railway.app/gitlab/webhook`

---

## ☁️ Option 3: Fly.io (Free tier)

### Cài Fly CLI:
```bash
# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

### Deploy:
```bash
# Login
fly auth login

# Launch app
fly launch --name gitlab-discord-notifier

# Set secrets
fly secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
fly secrets set GITLAB_WEBHOOK_TOKEN="chamchi123"

# Deploy
fly deploy
```

URL: `https://gitlab-discord-notifier.fly.dev/gitlab/webhook`

---

## 🆚 So sánh Cloud Platforms

| Platform | Free Tier | Region | URL cố định | Sleep? | Deploy |
|----------|-----------|--------|-------------|--------|--------|
| **Render** | ✅ 750h/month | Singapore | ✅ | ⚠️ 15min inactive | Dễ nhất |
| **Railway** | ✅ $5 credit | Global | ✅ | ❌ | Dễ |
| **Fly.io** | ✅ 3 VMs | Global | ✅ | ❌ | CLI |
| **Heroku** | ❌ (trả phí) | US/EU | ✅ | - | Dễ |

---

## ⚠️ Lưu ý Render.com Free Tier

Service sẽ **sleep sau 15 phút không hoạt động**. Khi GitLab gọi webhook:
- Lần đầu: ~30s để wake up (có thể timeout)
- Sau đó: Response nhanh

**Giải pháp:**
1. Upgrade lên paid plan ($7/month) - không sleep
2. Dùng Railway (không sleep nhưng hết credit sau 1 tháng)
3. Dùng cron job ping mỗi 10 phút:
```bash
# Trong cron hoặc GitHub Actions
*/10 * * * * curl https://your-app.onrender.com/docs
```

---

## 🎯 Khuyến nghị

**Cho production:**
- ✅ **Railway.app** - Không sleep, deploy nhanh, free $5/month
- ✅ **Fly.io** - Không sleep, nhiều region, free 3 VMs

**Cho testing:**
- ✅ **Render.com** - Dễ nhất, miễn phí hoàn toàn

---

## 📝 Checklist Deploy

- [ ] Push code lên GitHub
- [ ] Tạo file `render.yaml` hoặc `railway.json`
- [ ] Deploy trên platform
- [ ] Add environment variables
- [ ] Lấy public URL
- [ ] Update GitLab webhook URL
- [ ] Test webhook trong GitLab
- [ ] Kiểm tra Discord nhận message

---

## 🔍 Debug

### Xem logs trên Render:
Dashboard → Logs tab → Real-time logs

### Xem logs trên Railway:
Dashboard → Deployments → View Logs

### Test endpoint:
```bash
curl https://your-app.onrender.com/docs
```

### Test webhook:
```bash
curl -X POST https://your-app.onrender.com/gitlab/webhook \
  -H "X-Gitlab-Token: chamchi123" \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

---

Bạn muốn deploy lên platform nào? Tôi sẽ hướng dẫn chi tiết! 🚀
