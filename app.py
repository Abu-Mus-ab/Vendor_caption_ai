import os
import io
import hmac
import hashlib
import time
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import requests
from PIL import Image, ImageDraw, ImageFont
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openai import OpenAI

# ---------------- CONFIGURATION ----------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "true").lower() == "true"


database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///vendor_caption_ai.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Help SQLAlchemy detect and replace stale database connections.
if database_url.startswith("postgresql+psycopg://"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
    }

db = SQLAlchemy(app)


PRICE_NAIRA = 3000
PRICE_KOBO = PRICE_NAIRA * 100
PAYSTACK_BASE = "https://api.paystack.co"
LANGUAGES = [
    "English", "Nigerian Pidgin", "Hausa", "Yoruba", "Igbo"
]
STYLES = [
    "Catchy", "Premium", "New Arrival", "Discount Sale", "Persuasive"
]


# ---------------- DATABASE ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    subscription_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def subscription_active(self):
        return bool(
            self.subscription_until
            and self.subscription_until > datetime.utcnow()
        )


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- SHARED HELPERS ----------------

def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def active_subscription_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if not user.is_admin and not user.subscription_active:
            flash("Your subscription is not active. Please subscribe to continue.")
            return redirect(url_for("billing"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Admin access required.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def make_admin_if_configured():
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not password:
        return

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            name="Administrator",
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
    else:
        user.is_admin = True
        db.session.commit()


def paystack_headers():
    key = os.environ.get("PAYSTACK_SECRET_KEY", "")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def verify_and_activate_payment(reference):
    key = os.environ.get("PAYSTACK_SECRET_KEY", "")
    if not key:
        return False, "Paystack is not configured."

    payment = Payment.query.filter_by(reference=reference).first()
    if not payment:
        return False, "Payment reference was not found."

    # Do not activate a payment twice.
    if payment.status == "success":
        return True, "Subscription already activated."

    try:
        response = requests.get(
            f"{PAYSTACK_BASE}/transaction/verify/{reference}",
            headers=paystack_headers(),
            timeout=20
        )
        data = response.json()
    except Exception:
        return False, "Could not verify payment. Please try again."

    result = data.get("data", {})
    if (
        not response.ok
        or not data.get("status")
        or result.get("status") != "success"
        or result.get("amount") != payment.amount
        or result.get("currency") != "NGN"
    ):
        return False, "Payment has not been verified."

    user = db.session.get(User, payment.user_id)
    if not user:
        return False, "Account not found."

    now = datetime.utcnow()
    start = user.subscription_until if (
        user.subscription_until and user.subscription_until > now
    ) else now

    user.subscription_until = start + timedelta(days=30)
    payment.status = "success"
    db.session.commit()
    return True, "Payment verified. Your subscription is active."


# ---------------- HTML TEMPLATE ----------------

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} - Vendor Caption AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f5f8;color:#17202a;font-family:Arial,sans-serif}
header{background:#123c32;color:white;padding:18px 16px}
header a{color:white;text-decoration:none;margin-right:12px}
main{max-width:850px;margin:22px auto;padding:0 14px}
.card{background:white;padding:20px;margin-bottom:16px;border-radius:14px;
box-shadow:0 2px 10px #0000000c}
h1,h2{margin-top:0}
input,select,textarea{width:100%;padding:12px;margin:7px 0 14px;
border:1px solid #ccd3d9;border-radius:8px;font-size:16px}
button,.button{display:inline-block;background:#13795b;color:white;border:0;
padding:12px 16px;border-radius:8px;text-decoration:none;font-size:15px;cursor:pointer}
.secondary{background:#465766}
.notice{background:#fff2cc;padding:12px;border-radius:8px;margin-bottom:12px}
.muted{color:#65717c;font-size:14px}
img.advert{width:100%;max-width:550px;border-radius:10px}
.result{white-space:pre-wrap;background:#f5f7f8;padding:12px;border-radius:8px;margin:10px 0}
label{font-weight:bold}
</style>
</head>
<body>
<header>
  <strong>Vendor Caption AI</strong>
  <div style="margin-top:12px">
  {% if user %}
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    <a href="{{ url_for('billing') }}">Subscription</a>
    {% if user.is_admin %}<a href="{{ url_for('admin') }}">Admin</a>{% endif %}
    <a href="{{ url_for('logout') }}">Log out</a>
  {% else %}
    <a href="{{ url_for('login') }}">Log in</a>
    <a href="{{ url_for('register') }}">Create account</a>
  {% endif %}
  </div>
</header>
<main>
{% with messages = get_flashed_messages() %}
  {% for message in messages %}<div class="notice">{{ message }}</div>{% endfor %}
{% endwith %}
{{ body|safe }}
</main>
</body>
</html>
"""


def page(title, body, **kwargs):
    return render_template_string(
        PAGE, title=title, body=render_template_string(body, **kwargs),
        user=current_user()
    )


# ---------------- ACCOUNT ROUTES ----------------

@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))
    return page("Welcome", """
    <div class="card">
      <h1>Sell more through WhatsApp Status.</h1>
      <p>Create marketing captions and promotional advert designs for your products.</p>
      <p>Designed for Nigerian vendors, with local language options.</p>
      <p><strong>Subscription: ₦3,000 per 30 days.</strong></p>
      <a class="button" href="{{ url_for('register') }}">Get started</a>
      <a class="button secondary" href="{{ url_for('login') }}">Log in</a>
    </div>
    """)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
        else:
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

    return page("Create account", """
    <div class="card">
    <h1>Create your account</h1>
    <form method="post">
      <label>Your name</label><input name="name" required maxlength="100">
      <label>Email</label><input name="email" type="email" required>
      <label>Password (at least 8 characters)</label>
      <input name="password" type="password" minlength="8" required>
      <button type="submit">Create account</button>
    </form></div>
    """)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.")

    return page("Log in", """
    <div class="card">
    <h1>Log in</h1>
    <form method="post">
      <label>Email</label><input name="email" type="email" required>
      <label>Password</label><input name="password" type="password" required>
      <button type="submit">Log in</button>
    </form>
    <p class="muted">New here? <a href="{{ url_for('register') }}">Create an account</a>.</p>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- MAIN DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return page("Dashboard", """
    <div class="card">
      <h1>Hello, {{ user.name }}!</h1>
      {% if user.is_admin %}
        <p><strong>Administrator account</strong></p>
      {% elif user.subscription_active %}
        <p>Subscription active until {{ user.subscription_until.strftime('%d %b %Y') }}.</p>
      {% else %}
        <p>Your subscription is inactive. Subscribe for ₦3,000 per 30 days to generate content.</p>
        <a class="button" href="{{ url_for('billing') }}">Subscribe</a>
      {% endif %}
    </div>
    <div class="card">
      <h2>Generate WhatsApp Status captions</h2>
      <form method="post" action="{{ url_for('generate') }}">
        <label>What are you selling?</label>
        <input name="product" placeholder="e.g. ladies' handbags, cakes, phones" required maxlength="500">
        <label>Price (optional)</label>
        <input name="price" placeholder="e.g. ₦15,000" maxlength="100">
        <label>Offer or important details (optional)</label>
        <textarea name="details" rows="3" maxlength="700" placeholder="Size, location, discount, delivery..."></textarea>
        <label>Caption language</label>
        <select name="language">{% for item in languages %}<option>{{ item }}</option>{% endfor %}</select>
        <label>Marketing style</label>
        <select name="style">{% for item in styles %}<option>{{ item }}</option>{% endfor %}</select>
        <button type="submit">Generate 3 captions</button>
      </form>
    </div>
    <div class="card">
      <h2>Create a promotional advert image</h2>
      <p class="muted">Upload a real product photo if available. Your original product photo will be used in the design.</p>
      <form method="post" action="{{ url_for('create_advert') }}" enctype="multipart/form-data">
        <label>Product name</label><input name="product" required maxlength="150">
        <label>Price (optional)</label><input name="price" maxlength="100" placeholder="e.g. ₦15,000">
        <label>Short offer (optional)</label><input name="offer" maxlength="180" placeholder="e.g. New arrival — order today">
        <label>Product photo (optional, JPG/PNG/WebP, max 8 MB)</label>
        <input name="photo" type="file" accept="image/jpeg,image/png,image/webp">
        <button type="submit">Create advert image</button>
      </form>
    </div>
    """, user=user, languages=LANGUAGES, styles=STYLES)


# ---------------- AI CAPTIONS ----------------


@app.route("/generate", methods=["POST"])
@login_required
@active_subscription_required
def generate():
    product = request.form.get("product", "").strip()
    price = request.form.get("price", "").strip()
    details = request.form.get("details", "").strip()
    language = request.form.get("language", "English")
    style = request.form.get("style", "Catchy")

    if not product or len(product) > 500 or len(details) > 700:
        flash("Please enter valid product details.")
        return redirect(url_for("dashboard"))

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        flash("AI service is not configured. Please contact the administrator.")
        return redirect(url_for("dashboard"))

    prompt = f"""
You are a professional marketing copywriter for Nigerian small businesses.

Write exactly THREE different, ready-to-post WhatsApp Status captions.

Product: {product}
Price: {price or "Not provided"}
Details: {details or "Not provided"}
Language: {language}
Style: {style}

Instructions:
- Number the captions 1, 2, and 3.
- Make each caption attractive, natural, and different.
- Use the requested language and style.
- Use emojis where suitable.
- Include a simple call to action.
- Use only the information provided.
- Never invent product features, discounts, guarantees,
  stock levels, fabric details, or delivery promises.
- Do not explain your process.
- Return only the three captions.
"""

    try:
        response = None

        for attempt in range(3):
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/"
                "models/gemini-3.8-flash:generateContent",
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 1000,
                    },
                },
                timeout=60,
            )

            if response.status_code not in (429, 503):
                break

            if attempt < 2:
                time.sleep(attempt + 1)

        if not response.ok:
            app.logger.error(
                "Gemini API error: status=%s response=%s",
                response.status_code,
                response.text[:1000],
            )
            response.raise_for_status()

        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            app.logger.error(
                "Gemini returned no candidates: %s",
                str(data)[:1000],
            )
            raise ValueError("Gemini returned no captions.")

        parts = candidates[0].get("content", {}).get("parts", [])

        captions = "\n".join(
            part["text"].strip()
            for part in parts
            if isinstance(part.get("text"), str)
            and part["text"].strip()
        ).strip()

        if not captions:
            raise ValueError("Gemini returned empty caption text.")

    except Exception:
        app.logger.exception("Gemini caption generation failed")
        flash(
            "Caption generation failed. Please try again later."
        )
        return redirect(url_for("dashboard"))

    return page(
        "Your captions",
        """
        <div class="card">
          <h1>Your 3 captions</h1>
          <p class="muted">
            Review product details and prices before posting.
          </p>
          <div class="result" id="captions"
               style="white-space: pre-wrap;">{{ captions }}</div>
          <button type="button"
            onclick="navigator.clipboard.writeText(
              document.getElementById('captions').innerText
            ).then(() => alert('Copied')).catch(() => alert('Please copy the text manually.'))">
            Copy captions
          </button>
          <a class="button secondary"
             href="{{ url_for('dashboard') }}">
            Back to dashboard
          </a>
        </div>
        """,
        captions=captions,
    )





# ---------------- ADVERT IMAGE CREATION ----------------

def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for filename in candidates:
        try:
            return ImageFont.truetype(filename, size)
        except Exception:
            pass
    return ImageFont.load_default()


def fit_text(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


@app.route("/create-advert", methods=["POST"])
@login_required
@active_subscription_required
def create_advert():
    product = request.form.get("product", "").strip()
    price = request.form.get("price", "").strip()
    offer = request.form.get("offer", "").strip()
    photo = request.files.get("photo")

    if not product or len(product) > 150 or len(offer) > 180:
        flash("Please enter a valid product name and offer.")
        return redirect(url_for("dashboard"))

    canvas = Image.new("RGB", (1080, 1350), "#f2f5ee")
    draw = ImageDraw.Draw(canvas)

    # Brand header
    draw.rectangle((0, 0, 1080, 205), fill="#123c32")
    draw.text((55, 45), "VENDOR CAPTION AI", fill="white", font=load_font(38, True))
    draw.text((55, 112), "YOUR NEXT FAVOURITE FIND", fill="#d8eee2", font=load_font(23))

    # Product image area; never invent a product photo.
    image_top, image_bottom = 235, 880
    if photo and photo.filename:
        filename = secure_filename(photo.filename)
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            flash("Please upload a JPG, PNG, or WebP image.")
            return redirect(url_for("dashboard"))
        try:
            product_image = Image.open(photo.stream).convert("RGB")
            product_image.thumbnail((930, 620))
            x = (1080 - product_image.width) // 2
            y = image_top + (image_bottom - image_top - product_image.height) // 2
            canvas.paste(product_image, (x, y))
        except Exception:
            flash("That image could not be opened. Please try another photo.")
            return redirect(url_for("dashboard"))
    else:
        draw.rounded_rectangle((65, image_top, 1015, image_bottom), radius=35, fill="#dce8df")
        draw.text((110, 440), "YOUR PRODUCT", fill="#123c32", font=load_font(48, True))
        draw.text((110, 510), "Add a product photo next time", fill="#34594b", font=load_font(28))

    # Text and price
    draw.rectangle((0, 915, 1080, 1350), fill="#ffffff")
    y = 945
    for line in fit_text(draw, product.upper(), load_font(48, True), 960)[:2]:
        draw.text((55, y), line, fill="#123c32", font=load_font(48, True))
        y += 60

    if price:
        draw.text((55, y + 8), price, fill="#bd5c22", font=load_font(43, True))
        y += 72

    if offer:
        for line in fit_text(draw, offer, load_font(28), 960)[:2]:
            draw.text((55, y + 8), line, fill="#263b32", font=load_font(28))
            y += 40

    draw.rounded_rectangle((55, 1215, 1025, 1295), radius=20, fill="#13795b")
    draw.text((85, 1237), "MESSAGE US TO ORDER", fill="white", font=load_font(32, True))
    draw.text((55, 1310), "Please confirm price and availability with the seller.", fill="#5a655f", font=load_font(18))

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return send_file(
        output,
        mimetype="image/png",
        as_attachment=True,
        download_name="vendor-caption-advert.png"
    )

# ---------------- SUBSCRIPTIONS / PAYSTACK ----------------

@app.route("/billing")
@login_required
def billing():
    user = current_user()
    return page("Subscription", """
    <div class="card">
      <h1>Monthly subscription</h1>
      <p><strong>₦3,000 for 30 days</strong></p>
      {% if user.subscription_active %}
        <p>Your subscription is active until {{ user.subscription_until.strftime('%d %b %Y') }}.</p>
      {% else %}
        <p>Subscribe to use caption generation and advert creation.</p>
      {% endif %}
      <form method="post" action="{{ url_for('pay') }}">
        <button type="submit">Pay ₦3,000 with Paystack</button>
      </form>
      <p class="muted">Payments will only activate a subscription after server-side verification.</p>
    </div>
    """, user=user)

@app.route("/pay", methods=["POST"])
@login_required
def pay():
    user = current_user()
    secret_key = os.environ.get("PAYSTACK_SECRET_KEY", "")
    if not secret_key:
        flash("Paystack is not configured.")
        return redirect(url_for("billing"))

    reference = secrets.token_hex(16)
    payment = Payment(
        reference=reference,
        user_id=user.id,
        amount=PRICE_KOBO,
        status="pending"
    )
    db.session.add(payment)
    db.session.commit()

    callback_url = url_for("payment_callback", _external=True)
    try:
        response = requests.post(
            f"{PAYSTACK_BASE}/transaction/initialize",
            headers=paystack_headers(),
            json={
                "email": user.email,
                "amount": PRICE_KOBO,
                "currency": "NGN",
                "reference": reference,
                "callback_url": callback_url,
                "metadata": {"user_id": user.id}
            },
            timeout=20
        )
        data = response.json()
    except Exception:
        app.logger.exception("Paystack initialization failed")
        flash("Could not start payment. Please try again.")
        return redirect(url_for("billing"))

    if response.ok and data.get("status") and data.get("data", {}).get("authorization_url"):
        return redirect(data["data"]["authorization_url"])

    app.logger.error("Paystack initialization response: %s", data)
    flash("Paystack could not start the payment. Check your Paystack settings.")
    return redirect(url_for("billing"))


@app.route("/payment/callback")
@login_required
def payment_callback():
    reference = request.args.get("reference", "").strip()
    if not reference:
        flash("No payment reference was returned.")
        return redirect(url_for("billing"))

    payment = Payment.query.filter_by(reference=reference).first()
    if not payment or payment.user_id != current_user().id:
        flash("Payment reference does not match your account.")
        return redirect(url_for("billing"))

    success, message = verify_and_activate_payment(reference)
    flash(message)
    return redirect(url_for("dashboard" if success else "billing"))

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    secret_key = os.environ.get("PAYSTACK_SECRET_KEY", "")
    signature = request.headers.get("x-paystack-signature", "")
    raw_body = request.get_data()

    expected = hmac.new(
        secret_key.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()

    if not secret_key or not signature or not hmac.compare_digest(signature, expected):
        return "Invalid signature", 401

    event = request.get_json(silent=True) or {}
    if event.get("event") == "charge.success":
        reference = (event.get("data") or {}).get("reference")
        if reference:
            verify_and_activate_payment(reference)
    return "OK", 200
# ---------------- ADMIN ----------------

@app.route("/admin")
@login_required
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).limit(200).all()
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(100).all()

    return page("Admin dashboard", """
    <div class="card">
      <h1>Admin dashboard</h1>
      <p>Registered users: <strong>{{ users|length }}</strong> (showing up to 200)</p>
      <h2>Users</h2>
      {% for item in users %}
        <div class="result">
          <strong>{{ item.name }}</strong> — {{ item.email }}
          {% if item.is_admin %}(admin){% endif %}
          <br>Joined: {{ item.created_at.strftime('%d %b %Y') }}
          <br>Subscription:
          {% if item.subscription_active %}
            Active until {{ item.subscription_until.strftime('%d %b %Y') }}
          {% else %}Inactive{% endif %}
        </div>
      {% else %}<p>No users yet.</p>{% endfor %}
    </div>
    <div class="card">
      <h2>Recent payments</h2>
      {% for payment in payments %}
        <div class="result">
          Reference: {{ payment.reference }}<br>
          Amount: ₦{{ "%.2f"|format(payment.amount / 100) }}<br>
          Status: {{ payment.status }}<br>
          User ID: {{ payment.user_id }}
        </div>
      {% else %}<p>No payments yet.</p>{% endfor %}
    </div>
    """, users=users, payments=payments)


@app.route("/health")
def health():
    return {"status": "ok", "app": "Vendor Caption AI"}
# ---------------- STARTUP ----------------

with app.app_context():
    db.create_all()
    make_admin_if_configured()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))