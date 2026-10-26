from flask import Flask, request, jsonify, render_template_string, session, redirect
import random

app = Flask(__name__)
app.secret_key = "amam_final_2024"

# ========= PUT YOUR DETAILS HERE =========
MY_PASSWORD = "AREWA@AMAM_1033"
OPAY_NAME = "ABDULLAHI MUHAMMAD"
OPAY_NUMBER = "9039019035"  # YOUR OPAY NUMBER
WHATSAPP_NUMBER = "2347086332888"  # YOUR WHATSAPP e.g 2347012345678
PRICE = "₦3,000"
# =========================================

LOGIN_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AMAM - Login</title>
<style>
body{background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;font-family:Arial,sans-serif;padding:15px}
.box{border:1px solid #dadce0;border-radius:16px;padding:30px;width:100%;max-width:400px;text-align:center;box-shadow:0 2px 15px rgba(0,0,0,.08)}
input{width:100%;padding:14px;border:1px solid #dadce0;border-radius:24px;text-align:center;margin-top:20px;box-sizing:border-box}
button{margin-top:20px;background:#1a73e8;color:#fff;border:none;padding:12px 30px;border-radius:24px;font-weight:bold;cursor:pointer;width:100%}
.pay{background:#f8f9fa;padding:12px;border-radius:12px;margin-top:20px;font-size:13px}
a.wa{color:#fff;background:#25D366;padding:10px 18px;border-radius:24px;text-decoration:none;display:inline-block;margin-top:10px;font-weight:bold}
</style></head><body>
<div class="box">
<h2>🔒 AMAM CAPTION GENERATOR</h2>
<p style="color:#5f6368;font-size:14px">(for all business owners)<br>Subscription: {{PRICE}}/month</p>
<form method="POST"><input type="password" name="pwd" placeholder="Enter password" required><button>Unlock Access</button></form>
<div class="pay">
<b>Pay to get password:</b><br>
Opay: {{OPAY_NAME}}<br><b>{{OPAY_NUMBER}}</b> - {{PRICE}}/month<br>
<a class="wa" href="https://wa.me/{{WHATSAPP_NUMBER}}?text=Hi,%20I%20paid%20for%20AMAM">📱 Chat on WhatsApp</a>
</div></div></body></html>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AMAM CAPTION GENERATOR</title>
<style>
*{box-sizing:border-box} body{background:#fff;color:#202124;font-family:Arial,sans-serif;display:flex;flex-direction:column;align-items:center;min-height:90vh;margin:0;padding:20px}
.top{width:100%;max-width:700px;display:flex;justify-content:space-between;font-size:12px;color:#5f6368}
h1{font-size:30px;font-weight:400;text-align:center;margin:30px 0 0 0} h1 span{display:block;font-size:15px;color:#5f6368;margin-top:6px}
.search{margin-top:30px;width:100%;max-width:600px;display:flex;flex-direction:column;align-items:center}
input[type=text]{width:100%;padding:16px 24px;border:1px solid #dfe1e5;border-radius:24px;outline:none;box-shadow:0 1px 6px rgba(32,33,36,.28);font-size:16px}
select{margin-top:18px;width:100%;padding:14px 20px;border:1px solid #dfe1e5;border-radius:24px;background:#f8f9fa;font-size:15px}
.btn{margin-top:20px;background:#1a73e8;color:#fff;border:none;padding:12px 32px;border-radius:24px;cursor:pointer;font-size:15px}
.result{margin-top:35px;width:100%;max-width:650px}
.cap{border:1px solid #e8eaed;padding:16px;border-radius:12px;margin-bottom:12px;background:#fff;white-space:pre-wrap;line-height:1.5}
.copy{margin-top:8px;background:#f1f3f4;border:none;padding:6px 12px;border-radius:16px;cursor:pointer;font-size:12px}
.paybox{margin-top:30px;max-width:600px;width:100%;background:#e8f0fe;border-radius:12px;padding:16px;text-align:center;font-size:13px}
@media(max-width:600px){h1{font-size:24px} body{padding:12px}}
</style></head><body>
<div class="top"><span>✅ Subscribed {{PRICE}}/month</span><a href="/logout" style="color:#5f6368;text-decoration:none">Logout</a></div>
<h1>AMAM CAPTION GENERATOR <span>(for all business owners)</span></h1>
<div class="search">
<input id="product" type="text" placeholder="Enter product name e.g Sneakers, Abaya, Shawarma">
<select id="lang">
<option>English</option><option>Hausa</option><option>Yoruba</option><option>Igbo</option><option>French</option>
<option>Spanish</option><option>Mandarin</option><option>Arabic</option><option>Portuguese</option>
<option>Russian</option><option>German</option><option>Hindi</option><option>Japanese</option><option>Indonesian</option>
</select>
<button class="btn" onclick="gen()">✨ Generate Captions</button>
<div class="result" id="res"></div></div>
<div class="paybox">Renew: Opay <b>{{OPAY_NAME}} - {{OPAY_NUMBER}} - {{PRICE}}</b><br>
<a href="https://wa.me/{{WHATSAPP_NUMBER}}?text=Payment%20Proof%20AMAM" style="background:#25D366;color:#fff;padding:8px 16px;border-radius:20px;text-decoration:none;display:inline-block;margin-top:8px">📱 Send Proof on WhatsApp</a>
</div>
<script>
async function gen(){
 const p=document.getElementById('product').value; const l=document.getElementById('lang').value;
 if(!p){alert('Enter product');return;}
 document.getElementById('res').innerHTML='<p style=text-align:center>Generating...</p>';
 const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:p,lang:l})});
 const d=await r.json(); let h=''; d.captions.forEach((c,i)=>{h+=`<div class=cap><b>Caption ${i+1}:</b><br>${c}<br><button class=copy onclick="navigator.clipboard.writeText(\`${c.replace(/`/g,'')}\`);this.innerText='Copied!'">📋 Copy</button></div>`}); document.getElementById('res').innerHTML=h;
}
</script></body></html>
"""

TEMPLATES = [
 "STOP SCROLLING! 😍 Perfect {product} is HERE! Limited stock - DM now! 🔥",
 "POV: You just found the {product} that changes your style ✨ 100% Quality",
 "Luxury + Affordable? Yes! {product} proves them wrong! 💅 Shop now! 🚚",
 "This {product} is NOT for everyone. Only for bosses who love quality 👑",
 "Trending {product} 🚚 From my store to your doorstep - DM now!",
 "Warning: {product} will make friends ask 'Where did you get it?' 😂 #Bestseller"
]

@app.route('/', methods=['GET','POST'])
def home():
    if session.get('auth'):
        return render_template_string(MAIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)
    if request.method == 'POST':
        if request.form.get('pwd') == MY_PASSWORD:
            session['auth'] = True
            return render_template_string(MAIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)
        return f"<h3 style='text-align:center;margin-top:100px'>❌ Wrong Password!<br>Pay {PRICE} to {OPAY_NUMBER}<br><br><a href='/'>Try again</a></h3>"
    return render_template_string(LOGIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)

@app.route('/generate', methods=['POST'])
def gen():
    if not session.get('auth'): return jsonify({"captions":[]})
    p = request.json.get('product','Product')
    caps = [t.format(product=p) for t in random.sample(TEMPLATES, 5)]
    return jsonify({"captions": caps})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)