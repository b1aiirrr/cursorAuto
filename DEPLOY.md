# Deployment Guide (DigitalOcean + PM2)

Target server: `46.101.66.34` (Ubuntu)

## 1) Provision server dependencies

```bash
ssh root@46.101.66.34
apt update && apt upgrade -y
apt install -y git curl build-essential python3.12 python3.12-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g pm2
```

## 2) Clone project and configure worker

```bash
git clone <YOUR_REPO_URL> sentinel-square
cd sentinel-square/sentinel-worker
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Set real values in `.env`, including Binance and Gemini keys.

## 3) Run worker with PM2

```bash
cd ~/sentinel-square/sentinel-worker
pm2 start ".venv/bin/python run.py" --name sentinel-worker
pm2 save
pm2 startup
```

## 4) Build and run dashboard

```bash
cd ~/sentinel-square/sentinel-dashboard
npm install
npm run build
pm2 start "npm run start -- --port 3001" --name sentinel-dashboard
pm2 save
```

## 5) Useful PM2 commands

```bash
pm2 list
pm2 logs sentinel-worker
pm2 logs sentinel-dashboard
pm2 restart sentinel-worker
pm2 restart sentinel-dashboard
pm2 delete sentinel-worker
pm2 delete sentinel-dashboard
```

## 6) Git update workflow on server

```bash
cd ~/sentinel-square
git pull origin main
cd sentinel-square/sentinel-worker && source .venv/bin/activate && pip install -r requirements.txt
cd ../sentinel-dashboard && npm install && npm run build
pm2 restart sentinel-worker
pm2 restart sentinel-dashboard
```

## 7) Vercel deployment checklist (frontend in subfolder)

Use these values in the Vercel dashboard when importing `b1aiirrr/cursorAuto`:

- Project framework: `Next.js`
- Root Directory: `sentinel-dashboard`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `.next`
- Environment Variable:
  - `NEXT_PUBLIC_WORKER_URL=https://api.yourdomain.com/api`

`sentinel-dashboard/vercel.json` is already configured with matching build settings.

## 8) Secure API proxy on DigitalOcean (`api.yourdomain.com`)

Install Nginx + Certbot:

```bash
apt update
apt install -y nginx certbot python3-certbot-nginx
ufw allow 'Nginx Full'
```

Create Nginx site:

```bash
nano /etc/nginx/sites-available/sentinel-api
```

Paste:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8585;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600;
    }
}
```

Enable and reload:

```bash
ln -s /etc/nginx/sites-available/sentinel-api /etc/nginx/sites-enabled/sentinel-api
nginx -t
systemctl reload nginx
```

Issue HTTPS certificate:

```bash
certbot --nginx -d api.yourdomain.com
```

After TLS is active, set your Vercel env var to:

```env
NEXT_PUBLIC_WORKER_URL=https://api.yourdomain.com/api
```
