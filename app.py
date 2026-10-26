from flask import Flask, request, jsonify, render_template_string, session, redirect
import random, os
import urllib.request, json

app = Flask(__name__)
app.secret_key = "amam_pro_2026_final"

# ========= YOUR DETAILS =========
MY_PASSWORD = "AMAM@AREWA_1033"
OPAY_NAME = "ABDULLAHI MUHAMMAD"
OPAY_NUMBER = "9039019035"
WHATSAPP_NUMBER = "2347086332888"
PRICE = "₦3,000"
# ================================

LOGIN_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet">
<title>AMAM - Login</title>
<style>
*{font-family:'Inter',sans-serif;box-sizing:border-box}
body{background: radial-gradient(circle at top, #eef2ff 0%, #ffffff 40%, #f8fafc 100%);display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:15px}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:32px;width:100%;max-width:420px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,.07)}
h2{font-weight:800;font-size:22px;margin:0} h2 span{color:#2563eb}
input{width:100%;padding:14px;border:1px solid #cbd5e1;border-radius:24px;text-align:center;margin-top:20px;font-size:15px;font-weight:500}
button{margin-top:18px;background:#2563eb;color:#fff;border:none;padding:13px 30px;border-radius:24px;font-weight:700;cursor:pointer;width:100%;font-size:15px}
button:hover{background:#1d4ed8}
.pay{background:#f1f5f9;padding:14px;border-radius:12px;margin-top:20px;font-size:13px;line-height:1.6}
a.wa{background:#25D366;color:#fff;padding:10px 20px;border-radius:24px;text-decoration:none;display:inline-block;margin-top:10px;font-weight:700}
small{color:#64748b}
</style></head><body>
<div class="box">
<h2>🔒 <span>AMAM</span> CAPTION GENERATOR</h2>
<small><b>FOR ALL BUSINESS OWNERS</b><br>Subscription: {{PRICE}}/month</small>
<form method="POST"><input type="password" name="pwd" placeholder="Enter password" required><button>Unlock Access</button></form>
<div class="pay">
<b>Pay to get password:</b><br>Opay: <b>{{OPAY_NAME}} - {{OPAY_NUMBER}}</b><br>Amount: <b>{{PRICE}}/month</b><br>
<a class="wa" href="https://wa.me/{{WHATSAPP_NUMBER}}?text=Hi,%20I%20paid%20{{PRICE}}%20for%20AMAM">📱 Chat on WhatsApp</a>
</div></div></body></html>
"""

MAIN_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<title>AMAM CAPTION GENERATOR</title>
<style>
*{font-family:'Inter',sans-serif;box-sizing:border-box}
body{background: radial-gradient(1200px 600px at 50% -10%, #dbeafe 0%, #ffffff 50%, #f8fafc 100%);color:#0f172a;margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}
.top{width:100%;max-width:750px;display:flex;justify-content:space-between;font-size:12px;color:#64748b;margin-bottom:10px}
h1{font-weight:800;font-size:36px;letter-spacing:-1px;text-align:center;margin:25px 0 0 0}
h1 b{color:#2563eb}
h1 span{display:block;font-weight:500;font-size:16px;color:#475569;margin-top:8px}
.search{margin-top:35px;width:100%;max-width:620px;background:#fff;border:1px solid #e2e8f0;border-radius:24px;padding:24px;box-shadow:0 8px 30px rgba(0,0,0,.06)}
label{font-weight:700;font-size:13px;color:#334155;display:block;margin-bottom:6px;margin-top:14px}
input[type=text]{width:100%;padding:16px 22px;border:1.5px solid #e2e8f0;border-radius:14px;outline:none;font-size:16px;font-weight:500}
input[type=text]:focus{border-color:#2563eb;box-shadow:0 0 0 3px #dbeafe}
select{width:100%;padding:14px 18px;border:1.5px solid #e2e8f0;border-radius:14px;background:#fff;font-size:15px;font-weight:600;outline:none}
.btn{margin-top:22px;width:100%;background: linear-gradient(90deg,#2563eb,#7c3aed);color:#fff;border:none;padding:15px;border-radius:14px;font-weight:800;font-size:16px;cursor:pointer;letter-spacing:.3px}
.btn:hover{opacity:.9}
.result{margin-top:30px;width:100%}
.cap{background:#fff;border:1px solid #e2e8f0;border-left:4px solid #2563eb;padding:16px 18px;border-radius:12px;margin-bottom:14px;line-height:1.6;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.cap b{font-weight:800}
.copy{margin-top:10px;background:#0f172a;color:#fff;border:none;padding:7px 14px;border-radius:20px;cursor:pointer;font-size:12px;font-weight:700}
.paybox{margin-top:30px;max-width:620px;width:100%;background:#fff;border:1px dashed #94a3b8;border-radius:14px;padding:14px;text-align:center;font-size:13px}
@media(max-width:600px){h1{font-size:26px} .search{padding:18px} body{padding:12px}}
</style></head><body>
<div class="top"><span>💎 Active Plan: {{PRICE}}/month</span><a href="/logout" style="color:#64748b;text-decoration:none;font-weight:700">Logout</a></div>
<h1><b>AMAM</b> CAPTION GENERATOR <span>(for all business owners)</span></h1>
<div class="search">
<label>PRODUCT / SERVICE NAME</label>
<input id="product" type="text" placeholder="e.g. Sneakers, Abaya, Shawarma, Hair Oil...">
<label>LANGUAGE</label>
<select id="lang">
<option value="English">English</option>
<option value="Hausa">Hausa</option>
<option value="Yoruba">Yoruba</option>
<option value="Igbo">Igbo</option>
<option value="French">French</option>
<option value="Spanish">Spanish</option>
<option value="Mandarin">Mandarin Chinese</option>
<option value="Arabic">Arabic</option>
<option value="Portuguese">Portuguese</option>
<option value="Russian">Russian</option>
<option value="German">German</option>
<option value="Hindi">Hindi</option>
<option value="Japanese">Japanese</option>
<option value="Indonesian">Indonesian</option>
</select>
<button class="btn" onclick="gen()">✨ Generate Viral Captions</button>
<div class="result" id="res"></div>
</div>
<div class="paybox">Renew Subscription: <b>{{OPAY_NAME}} - {{OPAY_NUMBER}} - {{PRICE}}</b> | <a href="https://wa.me/{{WHATSAPP_NUMBER}}" style="color:#25D366;font-weight:800;text-decoration:none">WhatsApp Proof</a></div>
<script>
async function gen(){
 const p=document.getElementById('product').value; const l=document.getElementById('lang').value;
 if(!p){alert('Enter product name');return;}
 document.getElementById('res').innerHTML='<p style=text-align:center;font-weight:700>🤖 ChatGPT searching best captions online for '+l+'...</p>';
 const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:p,lang:l})});
 const d=await r.json(); let h=''; 
 d.captions.forEach((c,i)=>{
   const safe = c.replace(/`/g,'').replace(/'/g,"&#39;");
   h+=`<div class=cap><b>Caption ${i+1}:</b><br>${c}<br><button class=copy onclick="navigator.clipboard.writeText('${safe}');this.innerText='✅ Copied!'">📋 Copy</button></div>`;
 }); 
 document.getElementById('res').innerHTML=h;
}
</script></body></html>
"""

# ChatGPT-like professional caption engine with multi-language
def get_pro_captions(product, lang):
    # This simulates ChatGPT online search for best captions
    base_en = [
        f"**STOP SCROLLING!** 😍 Your search for perfect <b>{product}</b> ends HERE! Premium quality, affordable price. Limited stock - DM NOW! 🔥 #{product.replace(' ','')} #AMAMVendor",
        f"POV: You just found the <b>{product}</b> that will change your game ✨ <b>100% Quality Guaranteed.</b> Nationwide delivery 🚚 Tap link in bio to order!",
        f"They said you can't have <b>luxury + affordable</b>... We brought <b>{product}</b> to prove them WRONG! 💅 Bosses only 👑 Shop now!",
        f"<b>TRENDING NOW:</b> This {product} is selling FAST because it WORKS! From my store to your doorstep. What are you waiting for? 🛒",
        f"WARNING: This <b>{product}</b> will make everyone ask 'Where did you get that?' 😂 <b>Bestseller 2026</b> - Order before sold out! #Viral"
    ]
    
    translations = {
        "Hausa": [
            f"**DENA GUNGURUWA!** 😍 Ga <b>{product}</b> mai inganci! Farashi mai sauki, inganci 100%. Yi oda yanzu! 🔥",
            f"Kun taba ganin <b>{product}</b> irin wannan? Masu gane inganci kadai! DM yanzu 🚚",
            f"Wanda ya san darajar kudi, zai sayi <b>{product}</b>! Ana sayarwa da sauri - Kada a barka a baya!",
            f"**Mafi sayarwa:** <b>{product}</b> yana aiki sosai! Daga shagona zuwa gidanka!",
            f"GARGADI: <b>{product}</b> zai sa kowa ya tambayeka! Yi oda kafin ya kare!"
        ],
        "Yoruba": [
            f"**E DAKU!** 😍 <b>{product}</b> to dara julọ ti de! Didara 100%, owo ti o rọrun! DM bayi! 🔥",
            f"Iwo nikan ni o ye ki o ni <b>{product}</b> yii! Awọn oga nikan! Paṣẹ bayii 🚚",
            f"Ti o ba fẹ didara, <b>{product}</b> ni! Ma jẹ ki o kọja ọ!",
            f"**Ti n ta lọwọlọwọ:** <b>{product}</b> n ta nitori pe o ṣiṣẹ! Lati ile itaja mi si ile rẹ!",
            f"IKILO: <b>{product}</b> yii yoo jẹ ki gbogbo eniyan be