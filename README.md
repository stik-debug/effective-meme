# Chama App Kenya 🇰🇪

A complete digital platform for managing Kenyan Chamas (savings & investment groups).

**Works on Web + Mobile (PWA)** | **M-Pesa STK Push** | **SMS Notifications** | **Ready to Deploy**

---

## Features

### Core
- ✅ Member registration & login (phone-based)
- ✅ Multiple Chamas support
- ✅ Contributions / Savings tracking (Cash, M-Pesa, Bank)
- ✅ Loans with interest + approval workflow
- ✅ Loan repayments
- ✅ Merry-Go-Round (rotating savings)
- ✅ Meetings scheduling
- ✅ Reports & Member Statements
- ✅ Role-based access (Chairperson, Treasurer, Secretary, Member)

### New in this version
- ✅ **Real M-Pesa Daraja STK Push** (Lipa Na M-Pesa Online)
- ✅ **SMS Notifications** via Africa's Talking
- ✅ Dark Mode toggle
- ✅ PWA (install on phone home screen)
- ✅ Production-ready (Gunicorn + Render/Railway deploy)

---

## Quick Start (Local)

```bash
cd chama-app
pip install -r requirements.txt
cp .env.example .env          # optional – works in simulation mode by default
python app.py
```

Open: **http://localhost:5000**

### Demo Accounts

| Role        | Phone       | Password     |
|-------------|-------------|--------------|
| Chairperson | 0712345678  | password123  |
| Treasurer   | 0723456789  | password123  |
| Member      | 0734567890  | password123  |

Demo Chama: **Umoja Women Chama** (pre-loaded with data)

---

## M-Pesa Integration

### Simulation Mode (default)
No credentials needed. STK Push is simulated and logged to console.  
You can click **Complete** on pending transactions to finish them.

### Live Mode
1. Get credentials from [Safaricom Daraja](https://developer.safaricom.co.ke)
2. Copy `.env.example` → `.env` and fill in:
   ```
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=174379
   MPESA_PASSKEY=...
   MPESA_CALLBACK_URL=https://your-domain.com/mpesa/callback
   MPESA_ENV=sandbox
   SIMULATE_PAYMENTS=false
   ```
3. Restart the app

Members can pay contributions directly via **Pay via M-Pesa** button → STK prompt on their phone.

---

## SMS Notifications

Uses **Africa's Talking** (most popular in Kenya).

Automatic SMS is sent when:
- Contribution is recorded
- Loan is approved / rejected
- Loan repayment is received
- Merry-Go-Round payout is due
- STK Push is sent

### Setup
1. Create free account at [africastalking.com](https://africastalking.com)
2. Add to `.env`:
   ```
   AT_USERNAME=sandbox
   AT_API_KEY=your_key
   SIMULATE_SMS=false
   ```

In simulation mode, SMS content is printed to the server console.

---

## Deploy Online

See **[DEPLOY.md](DEPLOY.md)** for full instructions.

**Fastest path (Render.com):**
1. Push code to GitHub
2. Create Web Service on Render
3. Set environment variables
4. Deploy → your app is live at `https://xxx.onrender.com`

Members open the link on their phones and can **Add to Home Screen**.

---

## Project Structure

```
chama-app/
├── app.py                  # Main application
├── config.py               # Configuration from environment
├── requirements.txt
├── Procfile                # For Render / Heroku
├── runtime.txt
├── .env.example
├── DEPLOY.md
├── services/
│   ├── mpesa.py            # Safaricom Daraja STK Push
│   └── sms.py              # Africa's Talking SMS
├── templates/              # HTML pages
└── static/                 # CSS, JS, PWA icons
```

---

## Technology

- **Backend**: Python Flask + SQLAlchemy
- **Frontend**: Bootstrap 5 (mobile-first) + Dark Mode
- **Payments**: Safaricom Daraja (STK Push)
- **SMS**: Africa's Talking
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Deploy**: Gunicorn + Render / Railway / PythonAnywhere

---

Built for Kenyan Chamas — digitalizing traditional savings groups so members can contribute, borrow, and grow together from anywhere.
