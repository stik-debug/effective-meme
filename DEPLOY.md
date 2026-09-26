# Deploy Chama App Kenya Online 🚀

This guide shows you how to put the app live so all chama members can access it from anywhere on their phones.

---

## Option 1: Render.com (Recommended – Free Tier Available)

### Steps

1. **Create a free account** at [https://render.com](https://render.com)

2. **Push your code to GitHub**
   ```bash
   cd chama-app
   git init
   git add .
   git commit -m "Chama App Kenya"
   # Create a repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/chama-app.git
   git push -u origin main
   ```

3. **On Render Dashboard**
   - Click **New +** → **Web Service**
   - Connect your GitHub repo
   - Settings:
     - **Name**: `chama-app-kenya`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Free

4. **Environment Variables** (in Render → Environment)
   ```
   SECRET_KEY=any-long-random-string-here
   SIMULATE_PAYMENTS=true
   SIMULATE_SMS=true
   ```
   
   Later when you have real credentials:
   ```
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=...
   MPESA_PASSKEY=...
   MPESA_CALLBACK_URL=https://your-app.onrender.com/mpesa/callback
   MPESA_ENV=sandbox
   AT_USERNAME=sandbox
   AT_API_KEY=...
   SIMULATE_PAYMENTS=false
   SIMULATE_SMS=false
   ```

5. Click **Create Web Service**

6. After deploy finishes, your app will be live at:
   `https://chama-app-kenya.onrender.com`

---

## Option 2: Railway.app

1. Go to [https://railway.app](https://railway.app) and login with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Select your chama-app repo
4. Add the same environment variables as above
5. Railway auto-detects Python and runs gunicorn

---

## Option 3: PythonAnywhere (Good for Kenya – has free tier)

1. Create account at [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload the project files (or clone from GitHub)
3. Create a Web App (Manual configuration)
4. Set source code to your project folder
5. WSGI file should point to `app:app`
6. Install requirements via Bash console: `pip install -r requirements.txt`

---

## After Going Live

### 1. Update M-Pesa Callback URL
In Safaricom Daraja portal and in your `.env` / Render environment:
```
MPESA_CALLBACK_URL=https://your-real-domain.com/mpesa/callback
```

### 2. Get Real Credentials

**M-Pesa Daraja**
- Go to https://developer.safaricom.co.ke
- Create an app → get Consumer Key & Secret
- Use Lipa Na M-Pesa Online (STK Push)
- Sandbox shortcode is usually `174379`

**Africa's Talking SMS**
- Go to https://africastalking.com
- Create account → get API Key
- For testing use `username=sandbox`

### 3. Tell your members
Share the link: `https://your-app.onrender.com`  
They can **Add to Home Screen** on their phones for the best experience.

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a long random value
- [ ] Set `SIMULATE_PAYMENTS=false` and `SIMULATE_SMS=false` when ready
- [ ] Use PostgreSQL instead of SQLite (Render offers free Postgres)
- [ ] Enable HTTPS (automatic on Render/Railway)
- [ ] Test STK Push with a real Safaricom number in sandbox first
- [ ] Test SMS with Africa's Talking sandbox

---

**Your Chama is now digital and accessible from anywhere in Kenya (and the world)!**
