# AMAM / Vendor Caption AI — upgraded Flask app

This version adds customer accounts, OpenAI-powered multilingual captions, Paystack server-side payment verification, 30-day subscriptions, and an admin dashboard while retaining the AMAM visual style and ₦3,000 monthly price.

## Files
- `app.py` — Flask application
- `requirements.txt` — Python dependencies
- `Procfile` — Render/Gunicorn start command

## Render environment variables
Configure these in Render → your Web Service → Environment. Never commit their values to GitHub.

- `FLASK_SECRET_KEY` — long random secret (at least 32 random bytes)
- `DATABASE_URL` — Render PostgreSQL internal URL (recommended; SQLite is only a local fallback)
- `OPENAI_API_KEY` — API key from your OpenAI developer account
- `OPENAI_MODEL` — optional; defaults to `gpt-5.5`
- `PAYSTACK_SECRET_KEY` — Paystack test secret key for testing, then live secret key after launch
- `ADMIN_EMAIL` — the admin login email you choose
- `ADMIN_PASSWORD` — strong admin password you choose (minimum 12 characters recommended)
- `COOKIE_SECURE` — `true` for HTTPS production (default)

The app creates the initial admin user on startup if `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set. The password is stored as a hash. If the admin email already exists, the app marks that account as admin but does not reset its password.

## Paystack setup
1. Start with Paystack test keys.
2. In Paystack dashboard, set webhook URL to `https://YOUR-RENDER-SERVICE.onrender.com/paystack/webhook`.
3. Make a test payment. The app verifies transaction status, amount (₦3,000), currency (NGN), payer email, and local payment reference before granting 30 days.
4. Use live keys only after testing and after the service URL is stable.

## Important notes
- Subscription renewal is currently manual: customer clicks Paystack payment again after expiry. It is not automatic recurring billing.
- Existing shared-password access is replaced with individual accounts. Existing users need to register a new account.
- Before production launch, test registration, login, payment success/failure, webhook handling, subscription expiry, admin access and mobile layout.
- Configure a persistent PostgreSQL database on Render. Do not rely on local SQLite for production because service filesystems may be ephemeral.
- This package does not deploy itself or push to GitHub automatically. Review the changes and upload/commit these files to your repository.
