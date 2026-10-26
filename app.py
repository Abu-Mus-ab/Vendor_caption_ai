from flask import Flask, request, jsonify, render_template_string, session, redirect
import random

app = Flask(__name__)
app.secret_key = "amam_pro_fixed"

MY_PASSWORD = "AMAM@_1045"
OPAY_NAME = "ABDULLAHI MUHAMMAD"
OPAY_NUMBER = "9039019035"
WHATSAPP_NUMBER = "2347086332888"
PRICE = "N3,000"

LOGIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<title>AMAM - Login</title>
<style>
*{font-family:'Inter',sans-serif;box-sizing:border-box}
body{background: radial-gradient(circle at top, #eef2ff 0%, #ffffff 60%);display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:15px}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:32px;width:100%;max-width:420px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.07)}
input{width:100%;padding:14px;border:1px solid #cbd5e1;border-radius:24px;text-align:center;margin-top:20px;font-size:15px;font-weight:600}
button{margin-top:18px;background:#2563eb;color:#fff;border:none;padding:13px 30px;border-radius:24px;font-weight:700;cursor:pointer;width:100%}
.pay{background:#f1f5f9;padding:14px;border-radius:12px;margin-top:20px;font-size:13px;line-height:1.6}
a.wa{background:#25D366;color:#fff;padding:10px 20px;border-radius:24px;text-decoration:none;display:inline-block;margin-top:10px;font-weight:700}
</style></head><body>
<div class="box">
<h2>AMAM CAPTION GENERATOR</h2>
<small><b>FOR ALL BUSINESS OWNERS</b><br>Subscription: {{PRICE}}/month</small>
<form method="POST"><input type="password" name="pwd" placeholder="Enter password" required><button>Unlock Access</button></form>
<div class="pay">
<b>Pay to get password:</b><br>Opay: <b>{{OPAY_NAME}} - {{OPAY_NUMBER}}</b><br>Amount: <b>{{PRICE}}/month</b><br>
<a class="wa" href="https://wa.me/{{WHATSAPP_NUMBER}}?text=Hi I paid for AMAM">Chat on WhatsApp</a>
</div></div></body></html>
"""

MAIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet">
<title>AMAM CAPTION GENERATOR</title>
<style>
*{font-family:'Inter',sans-serif;box-sizing:border-box}
body{background: radial-gradient(800px 400px at 50% 0%, #dbeafe 0%, #ffffff 60%);color:#0f172a;margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}
.top{width:100%;max-width:750px;display:flex;justify-content:space-between;font-size:12px;color:#64748b}
h1{font-weight:800;font-size:34px;text-align:center;margin:25px 0 0 0} h1 b{color:#2563eb}
h1 span{display:block;font-weight:500;font-size:15px;color:#475569;margin-top:6px}
.search{margin-top:30px;width:100%;max-width:620px;background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:22px;box-shadow:0 8px 25px rgba(0,0,0,.06)}
label{font-weight:700;font-size:12px;color:#334155;display:block;margin:14px 0 6px 0}
input[type=text]{width:100%;padding:15px 20px;border:1.5px solid #e2e8f0;border-radius:12px;outline:none;font-size:16px;font-weight:500}
select{width:100%;padding:13px 16px;border:1.5px solid #e2e8f0;border-radius:12px;background:#fff;font-size:15px;font-weight:600}
.btn{margin-top:20px;width:100%;background:#2563eb;color:#fff;border:none;padding:14px;border-radius:12px;font-weight:800;font-size:16px;cursor:pointer}
.result{margin-top:25px;width:100%}
.cap{background:#fff;border:1px solid #e2e8f0;border-left:4px solid #2563eb;padding:14px;border-radius:10px;margin-bottom:12px;line-height:1.6;font-size:14px}
.copy{margin-top:8px;background:#0f172a;color:#fff;border:none;padding:6px 12px;border-radius:16px;cursor:pointer;font-size:12px;font-weight:700}
@media(max-width:600px){h1{font-size:24px}}
</style></head><body>
<div class="top"><span>Active: {{PRICE}}/month</span><a href="/logout" style="color:#64748b;text-decoration:none;font-weight:700">Logout</a></div>
<h1><b>AMAM</b> CAPTION GENERATOR <span>(for all business owners)</span></h1>
<div class="search">
<label>PRODUCT NAME</label>
<input id="product" type="text" placeholder="e.g. Sneakers, Abaya, Shawarma">
<label>LANGUAGE</label>
<select id="lang">
<option>English</option><option>Hausa</option><option>Yoruba</option><option>Igbo</option><option>French</option>
<option>Spanish</option><option>Mandarin</option><option>Arabic</option><option>Portuguese</option><option>Russian</option>
<option>German</option><option>Hindi</option><option>Japanese</option><option>Indonesian</option>
</select>
<button class="btn" onclick="gen()">Generate Viral Captions</button>
<div class="result" id="res"></div></div>
<script>
async function gen(){
 const p=document.getElementById('product').value;
 const l=document.getElementById('lang').value;
 if(!p){alert('Enter product');return;}
 document.getElementById('res').innerHTML='<p style=text-align:center><b>ChatGPT searching best captions for '+l+'...</b></p>';
 const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:p,lang:l})});
 const d=await r.json();
 let h='';
 d.captions.forEach(function(c,i){
   h+='<div class=cap><b>Caption '+(i+1)+':</b><br>'+c+'<br><button class=copy onclick="navigator.clipboard.writeText(this.parentNode.innerText);this.innerText=\'Copied!\'">Copy</button></div>';
 });
 document.getElementById('res').innerHTML=h;
}
</script></body></html>
"""

def get_captions(product, lang):
    en = [
        f"<b>STOP SCROLLING!</b> Your perfect {product} is HERE! Premium quality, affordable price. Limited stock - DM NOW!",
        f"POV: You just found the {product} that will change your game. 100% Quality Guaranteed. Nationwide delivery!",
        f"Luxury + Affordable? Yes! {product} proves them WRONG! Bosses only. Shop now!",
        f"<b>TRENDING NOW:</b> This {product} is selling FAST because it WORKS! From my store to your doorstep.",
        f"WARNING: This {product} will make everyone ask Where did you get that? Bestseller 2026 -