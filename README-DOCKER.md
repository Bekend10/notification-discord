# GitLab Discord Notifier - Docker Deployment

## 🚀 Quick Start

### 1. Build và chạy với Docker Compose:
```bash
docker-compose up -d --build
```

### 2. Xem logs:
```bash
docker-compose logs -f
```

### 3. Dừng service:
```bash
docker-compose down
```

---

## 📋 Các lệnh Docker thường dùng

### Build image:
```bash
docker build -t gitlab-discord-notifier .
```

### Chạy container thủ công:
```bash
docker run -d \
  --name gitlab-discord \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  gitlab-discord-notifier
```

### Xem logs realtime:
```bash
docker logs -f gitlab-discord
```

### Restart container:
```bash
docker-compose restart
```

### Rebuild khi thay đổi code:
```bash
docker-compose up -d --build
```

### Stop và xóa container:
```bash
docker-compose down
```

### Kiểm tra container đang chạy:
```bash
docker ps
```

### Vào bên trong container để debug:
```bash
docker exec -it gitlab-discord bash
```

---

## 🌐 Deploy lên Server

### Option 1: VPS/Server với Docker

```bash
# 1. SSH vào server
ssh user@your-server.com

# 2. Cài Docker (nếu chưa có)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Cài Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone repo (hoặc upload files)
git clone <your-repo-url>
cd notification-discord

# 5. Tạo file .env
nano .env
# Paste:
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
# GITLAB_WEBHOOK_TOKEN=your-secret-token

# 6. Chạy
docker-compose up -d --build

# 7. Kiểm tra
docker-compose logs -f
```

### Option 2: Deploy với Nginx Reverse Proxy

Nếu muốn dùng domain name:

```nginx
# /etc/nginx/sites-available/gitlab-discord
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/gitlab-discord /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Add SSL với Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

**GitLab webhook URL:**
```
https://your-domain.com/gitlab/webhook
```

---

## 🐳 Deploy lên Docker Cloud Platforms

### Railway.app
1. Push code lên GitHub
2. Vào Railway.app → New Project → Deploy from GitHub
3. Railway tự detect Dockerfile
4. Add Environment Variables:
   - `DISCORD_WEBHOOK_URL`
   - `GITLAB_WEBHOOK_TOKEN`
5. Deploy!

URL: `https://your-app.railway.app/gitlab/webhook`

### Render.com
1. New → Web Service
2. Connect GitHub repo
3. Environment: Docker
4. Add environment variables
5. Deploy

URL: `https://your-app.onrender.com/gitlab/webhook`

---

## 🔧 Troubleshooting

### Container không start:
```bash
docker-compose logs
```

### Kiểm tra health:
```bash
docker ps
# Xem cột STATUS - nên thấy "healthy"
```

### Test endpoint:
```bash
curl http://localhost:8000/docs
```

### Rebuild hoàn toàn:
```bash
docker-compose down
docker system prune -a
docker-compose up -d --build
```

---

## 📊 Monitoring

### Xem resource usage:
```bash
docker stats gitlab-discord
```

### Auto-restart khi server reboot:
Service đã được config với `restart: unless-stopped` nên sẽ tự động chạy lại khi server restart.

---

## 🔐 Security Notes

- ✅ Không commit file `.env` lên Git
- ✅ Dùng secrets management trên cloud platforms
- ✅ Thường xuyên update base image: `docker-compose pull && docker-compose up -d`
- ✅ Enable firewall chỉ cho phép port 8000 từ GitLab IP

---

## 📝 Environment Variables

Required:
- `DISCORD_WEBHOOK_URL` - Discord webhook URL
- `GITLAB_WEBHOOK_TOKEN` - Secret token để verify requests từ GitLab

Optional:
- `PORT` - Port to run on (default: 8000)
