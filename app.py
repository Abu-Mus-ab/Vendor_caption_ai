import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import requests
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    # Safe for local development only; set FLASK_SECRET_KEY in Render for production.
    app.config['SECRET_KEY'] = secrets.token_hex(32)

raw_db_url = os.environ.get('DATABASE_URL', 'sqlite:///vendor_caption_ai.db')
if raw_db_url.startswith('postgres://'):
    raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
if raw_db_url.startswith('postgresql://') and '+psycopg' not in raw_db_url:
    raw_db_url = raw_db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = raw_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', 'true').lower() == 'true'

db = SQLAlchemy(app)
PRICE_NAIRA = 3000
PRICE_KOBO = PRICE_NAIRA * 100
OPAY_NAME = 'ABDULLAHI MUHAMMAD'
OPAY_NUMBER = '9039019035'
WHATSAPP_NUMBER = '2347086332888'
LANGUAGES = ['English', 'Hausa', 'Yoruba', 'Igbo', 'French', 'Spanish', 'Mandarin', 'Arabic', 'Portuguese', 'Russian', 'German', 'Hindi', 'Japanese', 'Indonesian']

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    subscription_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def subscription_active(self):
        if not self.subscription_expires_at:
            return False
        expiry = self.subscription_expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > datetime.now(timezone.utc)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_kobo = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default='initialized', nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)

BASE_STYLE = """
*{font-family:Inter,Arial,sans-serif;box-sizing:border-box}body{background:#f8fafc;color:#0f172a;margin:0;padding:18px;min-height:100vh}
.wrap{width:100%;max-width:850px;margin:24px auto}.card{background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:24px;box-shadow:0 8px 24px rgba(15,23,42,.05);margin-bottom:16px}
h1,h2{text-align:center}h1{font-weight:800;font-size:28px} .muted{color:#64748b;font-size:14px;text-align:center}
input,select{display:block;width:100%;padding:13px 14px;border:1px solid #cbd5e1;border-radius:12px;margin:10px 0;font-size:16px;background:white}
button,.btn{display:block;width:100%;padding:13px 15px;border:0;border-radius:12px;background:#2563eb;color:white;font-weight:800;cursor:pointer;text-align:center;text-decoration:none;margin-top:12px}
.btn.secondary,button.secondary{background:#e2e8f0;color:#0f172a}.nav{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-bottom:18px}.nav a{color:#2563eb;text-decoration:none;font-weight:700}
.pay{background:#f1f5f9;border-radius:12px;padding:14px;font-size:13px;margin-top:14px}.cap{border:1px solid #e2e8f0;border-left:4px solid #2563eb;padding:14px;border-radius:10px;margin:12px 0;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}
.notice{padding:12px;border-radius:10px;background:#eff6ff;margin:12px 0}.error{background:#fef2f2}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}.small{font-size:13px;color:#64748b}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:10px;border-bottom:1px solid #e2e8f0;overflow-wrap:anywhere}
"""
LOGIN_HTML = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>AMAM CAPTION GENERATOR</title><link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap' rel='stylesheet'><style>"""+BASE_STYLE+"""</style></head><body><div class='wrap'><div class='card' style='max-width:440px;margin:30px auto'><h2>AMAM CAPTION GENERATOR</h2><p class='muted'><b>For all business owners</b><br>₦3,000 / month</p>{% with messages = get_flashed_messages() %}{% for m in messages %}<div class='notice'>{{m}}</div>{% endfor %}{% endwith %}<form method='post'><input type='email' name='email' placeholder='Email address' required autocomplete='email'><input type='password' name='password' placeholder='Password' required autocomplete='current-password'><button>Log in</button></form><p class='muted'>New here? <a href='/register'>Create an account</a></p><div class='pay'>Opay: <b>"""+OPAY_NAME+" - "+OPAY_NUMBER+"""</b><br>Subscription: ₦3,000/month<br><a href='https://wa.me/"""+WHATSAPP_NUMBER+"""'>WhatsApp support</a></div></div></div></body></html>"""
REGISTER_HTML = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Create account</title><link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap' rel='stylesheet'><style>"""+BASE_STYLE+"""</style></head><body><div class='wrap'><div class='card' style='max-width:460px;margin:30px auto'><h2>Create your account</h2><p class='muted'>AMAM CAPTION GENERATOR · ₦3,000/month</p>{% with messages = get_flashed_messages() %}{% for m in messages %}<div class='notice'>{{m}}</div>{% endfor %}{% endwith %}<form method='post'><input name='name' placeholder='Your name' required maxlength='120'><input type='email' name='email' placeholder='Email address' required><input type='password' name='password' placeholder='Create password (at least 8 characters)' minlength='8' required><button>Create account</button></form><p class='muted'><a href='/'>Back to login</a></p></div></div></body></html>"""

MAIN_HTML = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>AMAM CAPTION GENERATOR</title><link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap' rel='stylesheet'><style>"""+BASE_STYLE+"""</style></head><body><div class='wrap'><div class='nav'><a href='/'>Caption Generator</a><a href='/billing'>Subscription</a>{% if user.is_admin %}<a href='/admin'>Admin dashboard</a>{% endif %}<a href='/logout'>Log out</a></div><h1>AMAM CAPTION GENERATOR <div class='muted'>FOR ALL BUSINESS OWNERS</div></h1><div class='card'><p class='muted'>Welcome, {{user.name}} · {% if user.subscription_active %}<b>Subscription active until {{expiry}}</b>{% else %}<b>Subscription inactive</b>{% endif %}</p>{% if not user.subscription_active %}<div class='notice'>Activate your monthly subscription to generate AI captions.</div><a class='btn' href='/billing'>Activate subscription — ₦3,000/month</a>{% else %}<label for='product'>Describe your product or service</label><input id='product' type='text' maxlength='500' placeholder='e.g. handmade leather sandals, price, key benefits'><label for='lang'>Caption language</label><select id='lang'>{% for lang in languages %}<option>{{lang}}</option>{% endfor %}</select><button onclick='gen()'>Generate 5 AI Captions</button><div id='res' style='margin-top:20px'></div>{% endif %}<div class='pay'>Opay: <b>"""+OPAY_NAME+" - "+OPAY_NUMBER+"""</b><br>Monthly plan: ₦3,000<br><a href='https://wa.me/"""+WHATSAPP_NUMBER+"""'>WhatsApp support</a></div></div></div><script>
async function gen(){const p=document.getElementById('product').value.trim(),l=document.getElementById('lang').value;if(!p){alert('Please describe your product or service.');return;}const res=document.getElementById('res');res.textContent='Creating captions…';try{const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:p,lang:l})});const d=await r.json();if(!r.ok)throw new Error(d.error||'Unable to generate captions');res.innerHTML='';(d.captions||[]).forEach((c,i)=>{const div=document.createElement('div');div.className='cap';const b=document.createElement('b');b.textContent='Caption '+(i+1)+': ';div.appendChild(b);div.appendChild(document.createTextNode(c));const copy=document.createElement('button');copy.className='secondary';copy.textContent='Copy caption';copy.onclick=()=>navigator.clipboard.writeText(c).then(()=>copy.textContent='Copied');div.appendChild(copy);res.appendChild(div);});}catch(e){res.textContent=e.message;}}
</script></body></html>"""
BILLING_HTML = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Subscription</title><link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap' rel='stylesheet'><style>"""+BASE_STYLE+"""</style></head><body><div class='wrap'><div class='nav'><a href='/'>Caption Generator</a><a href='/logout'>Log out</a></div><div class='card'><h2>Monthly subscription</h2><p class='muted'>₦3,000 for 30 days of AI caption generation</p><div class='notice'>Subscription status: <b>{% if user.subscription_active %}Active until {{expiry}}{% else %}Inactive or expired{% endif %}</b></div><form method='post' action='/pay'><button>Pay ₦3,000 securely with Paystack</button></form><p class='small'>Your account activates only after the server verifies a successful ₦3,000 payment with Paystack. Do not send your card details or payment PIN to anyone.</p><div class='pay'>Need help? Opay: <b>"""+OPAY_NAME+" - "+OPAY_NUMBER+"""</b><br><a href='https://wa.me/"""+WHATSAPP_NUMBER+"""'>WhatsApp support</a></div></div></div></body></html>"""
ADMIN_HTML = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Admin dashboard</title><link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap' rel='stylesheet'><style>"""+BASE_STYLE+"""</style></head><body><div class='wrap'><div class='nav'><a href='/'>Caption Generator</a><a href='/billing'>Subscription</a><a href='/logout'>Log out</a></div><div class='card'><h2>Admin dashboard</h2><div class='grid'><div class='notice'>Customers: <b>{{users|length}}</b></div><div class='notice'>Verified payments: <b>{{payments|length}}</b></div><div class='notice'>Active subscriptions: <b>{{active_count}}</b></div></div><h3>Customers</h3><table><tr><th>Name / email</th><th>Subscription</th><th>Action</th></tr>{% for u in users %}<tr><td>{{u.name}}<br><span class='small'>{{u.email}}</span></td><td>{% if u.subscription_active %}Active to {{u.subscription_expires_at}}{% else %}Inactive{% endif %}</td><td>{% if not u.is_admin %}<form method='post' action='/admin/extend/{{u.id}}'><button>Grant 30 days</button></form>{% endif %}</td></tr>{% endfor %}</table><h3>Recent verified payments</h3><table><tr><th>Reference</th><th>User ID</th><th>Amount</th><th>Date</th></tr>{% for p in payments %}<tr><td>{{p.reference}}</td><td>{{p.user_id}}</td><td>₦{{'%.2f'|format(p.amount_kobo/100)}}</td><td>{{p.verified_at}}</td></tr>{% endfor %}</table></div></div></body></html>"""


def current_user():
    uid = session.get('user_id')
    return db.session.get(User, uid) if uid else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash('Please log in to continue.')
            return redirect(url_for('home'))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            return redirect(url_for('home'))
        return fn(*args, **kwargs)
    return wrapper

def ensure_admin():
    email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
    password = os.environ.get('ADMIN_PASSWORD', '')
    if not email or not password:
        return
    admin = User.query.filter_by(email=email).first()
    if not admin:
        admin = User(name='Administrator', email=email, password_hash=generate_password_hash(password), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    elif not admin.is_admin:
        admin.is_admin = True
        db.session.commit()

with app.app_context():
    db.create_all()
    ensure_admin()

@app.route('/', methods=['GET', 'POST'])
def home():
    user = current_user()
    if user:
        expiry = user.subscription_expires_at.strftime('%Y-%m-%d') if user.subscription_expires_at else 'Not active'
        return render_template_string(MAIN_HTML, user=user, expiry=expiry, languages=LANGUAGES)
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash('Email or password is incorrect.')
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or len(password) < 8:
            flash('Enter your name, a valid email and a password of at least 8 characters.')
        elif User.query.filter_by(email=email).first():
            flash('An account with that email already exists. Please log in.')
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('billing'))
    return render_template_string(REGISTER_HTML)

@app.route('/billing')
@login_required
def billing():
    user = current_user()
    expiry = user.subscription_expires_at.strftime('%Y-%m-%d') if user.subscription_expires_at else 'Not active'
    return render_template_string(BILLING_HTML, user=user, expiry=expiry)

@app.route('/pay', methods=['POST'])
@login_required
def pay():
    user = current_user()
    secret = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret:
        flash('Payment setup is not complete yet. Please contact support.')
        return redirect(url_for('billing'))
    reference = 'AMAM-' + secrets.token_hex(12).upper()
    callback_url = url_for('payment_callback', _external=True)
    try:
        response = requests.post('https://api.paystack.co/transaction/initialize',
            headers={'Authorization': f'Bearer {secret}', 'Content-Type': 'application/json'},
            json={'email': user.email, 'amount': PRICE_KOBO, 'reference': reference,
                  'callback_url': callback_url, 'metadata': {'user_id': user.id, 'plan': 'monthly_caption_generator'}}, timeout=20)
        payload = response.json()
        if response.status_code >= 400 or not payload.get('status') or not payload.get('data', {}).get('authorization_url'):
            app.logger.error('Paystack initialize failed: %s', payload.get('message', 'unknown error'))
            flash('Unable to start payment. Please try again later.')
            return redirect(url_for('billing'))
        db.session.add(Payment(reference=reference, user_id=user.id, amount_kobo=PRICE_KOBO, status='initialized'))
        db.session.commit()
        return redirect(payload['data']['authorization_url'])
    except requests.RequestException:
        app.logger.exception('Paystack initialization request failed')
        flash('Payment service is temporarily unavailable. Please try again.')
        return redirect(url_for('billing'))

def verify_paystack_reference(reference):
    secret = os.environ.get('PAYSTACK_SECRET_KEY')
    if not secret or not reference:
        return False
    try:
        response = requests.get('https://api.paystack.co/transaction/verify/' + requests.utils.quote(reference, safe=''),
            headers={'Authorization': f'Bearer {secret}'}, timeout=20)
        payload = response.json()
        data = payload.get('data') or {}
        if response.status_code != 200 or not payload.get('status'):
            return False
        payment = Payment.query.filter_by(reference=reference).first()
        if not payment or payment.status == 'success':
            return bool(payment and payment.status == 'success')
        if data.get('status') != 'success' or int(data.get('amount') or 0) != payment.amount_kobo or data.get('currency') != 'NGN':
            payment.status = str(data.get('status') or 'unverified')[:30]
            db.session.commit()
            return False
        # Make sure Paystack confirms the payer email matches the account that initiated this payment.
        payer_email = (data.get('customer') or {}).get('email', '').strip().lower()
        user = db.session.get(User, payment.user_id)
        if not user or payer_email != user.email:
            payment.status = 'email_mismatch'
            db.session.commit()
            return False
        now = datetime.now(timezone.utc)
        old_expiry = user.subscription_expires_at
        if old_expiry and old_expiry.tzinfo is None:
            old_expiry = old_expiry.replace(tzinfo=timezone.utc)
        base = old_expiry if old_expiry and old_expiry > now else now
        user.subscription_expires_at = base + timedelta(days=30)
        payment.status = 'success'
        payment.verified_at = now
        db.session.commit()
        return True
    except (requests.RequestException, ValueError, TypeError):
        app.logger.exception('Paystack verification failed')
        return False

@app.route('/payment/callback')
@login_required
def payment_callback():
    reference = request.args.get('reference') or request.args.get('trxref')
    if verify_paystack_reference(reference):
        flash('Payment verified. Your subscription is active for 30 days.')
        return redirect(url_for('home'))
    flash('Payment has not been verified yet. If you were charged, wait a moment and contact support if access does not activate.')
    return redirect(url_for('billing'))

@app.route('/paystack/webhook', methods=['POST'])
def paystack_webhook():
    secret = os.environ.get('PAYSTACK_SECRET_KEY', '')
    signature = request.headers.get('x-paystack-signature', '')
    body = request.get_data()
    expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest() if secret else ''
    if not secret or not signature or not hmac.compare_digest(expected, signature):
        return jsonify({'ok': False}), 401
    event = request.get_json(silent=True) or {}
    if event.get('event') == 'charge.success':
        reference = (event.get('data') or {}).get('reference')
        if reference:
            verify_paystack_reference(reference)
    return jsonify({'ok': True}), 200

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user = current_user()
    if not user.subscription_active:
        return jsonif