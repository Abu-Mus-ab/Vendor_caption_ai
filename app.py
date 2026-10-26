from flask import Flask, request, render_template_string
import random

app = Flask(__name__)

MASTER_PASSWORD = "AREWA2026"
YOUR_WHATSAPP = "2347086332888"  # << CHANGE TO YOUR NUMBER
YOUR_OPAY = "9039019035 - Abdullahi Muhammad (Opay)"
PRICE = "₦2,000/month"

# === TRENDING PRODUCTS DATABASE 2026 - FROM LIVE SEARCH ===
TRENDING_PRODUCTS = {
    "Abaya - Embroidered Luxury (Trending Dubai 2026)": {
        "tags": ["Abaya", "Dubai", "Luxury"],
        "captions": {
            "english": "✨ Dubai Luxury Embroidered Abaya 2026 Collection ✨\nStrategic embellishment, pleated flow, premium jacquard fabric 💫\nThis is not regular abaya - this is STATEMENT! 👑\nLimited pieces. DM now! #DubaiAbaya #ModestFashion2026【1557522929316233903†L106-L109】",
            "hausa": "✨ Abaya Mai Dinkin Dubai Na 2026! ✨\nKyawun dinki, yadi mai laushi, an yi da inganci!\nBa kamar kowacce ba ce - ta manyan mata ce! 👑\nKi yi DM yanzu, kadan ta rage!",
            "pidgin": "🔥 Original Dubai Embroidered Abaya don land! ✨\nThis one na luxury, no be regular abaya o! Quality choke! DM now before e finish!"
        }
    },
    "Abaya - Open Front Minimalist (Viral)": {
        "captions": {
            "english": "🖤 Minimalist Open Front Abaya - 2026 Trend Alert\nClean lines, monochrome, effortless chic 🏙️🧕\nLayer it, style it, own it! Perfect for work & events.\nMonochrome magic ✨ #MinimalistAbaya #ArewaChic【1557522929316233903†L124-L127】",
            "hausa": "Abaya Mai Bude Gaba - Sabon Salo Na 2026!\nMai sauki, mai kyau, za ki iya saka ta ko'ina! 🖤",
            "pidgin": "This open front abaya na the new wave! Simple but classy, you fit rock am anyhow!"
        }
    },
    "Premium Natural Skincare - Shea Butter & Moringa (High Demand NG)": {
        "captions": {
            "english": "🧴 PREMIUM Shea Butter + Moringa Glow Oil ✨\n100% Natural, Handcrafted in Nigeria 🇳🇬\nNo chemicals, just pure glow! 45-65% margin product that diaspora is rushing! 🌍\nAuthentic Naija formulation - DM for wholesale! #MadeInNaijaSkincare【5620316263177976733†L12-L17】",
            "hausa": "Man shafawa na Shea Butter da Moringa - Na gargajiya, mai kyau!",
            "pidgin": "Original shea butter + moringa oil - No chemical! Your skin go glow like say you travel! DM now!"
        }
    },
    "Lip Oils & Cream Blush (TikTok Viral $662M Sales)": {
        "captions": {
            "english": "💄 VIRAL TikTok Lip Oil + Cream Blush 💋\nThe exact product selling $662M on TikTok Shop Q2 2026! 🔥\nGRWM videos are blowing up - easy to demo, easy to sell! Glossy, long-lasting, affordable luxury.\nOne video = instant sellout! DM! #TikTokViralBeauty【3517687480467350539†L9-L16】",
            "hausa": "Lip Oil Da Blush Mai Dauke Hankali! Wanda ya ke sayarwa sosai a TikTok!",
            "pidgin": "This lip oil na wetin dey burst TikTok now! $662 million sales! If you never get am, you dey dull!"
        }
    },
    "Phone Accessories - Power Banks & Wireless Earbuds (Fastest Selling NG)": {
        "captions": {
            "english": "🔋 FASTEST SELLING IN NIGERIA 2026! Wireless Earbuds + 20,000mAh Power Bank 📱\n195M active lines in Naija - everybody needs this! 💯\nLow capital, high demand, repeat purchase! #PhoneAccessoriesLagos【5620316263177976733†L68-L76】",
            "hausa": "Kayan Waya Mai Sayarwa Sosai - Power Bank Da Earbuds!",
            "pidgin": "Phone accessories na fastest selling for Naija now! Everybody dey buy am! Power bank and earbuds - you no go lose!"
        }
    },
    "Rechargeable Fan & Solar Items (Energy Crisis Seller)": {
        "captions": {
            "english": "💡 ENERGY-SAVING HERO! Rechargeable Fan + Solar Power Bank ☀️\nNEPA no go stress you again! 40-80% profit margin! Most profitable in Naija e-commerce 2026!\nLight no dey? You get light! DM for price! #SolarNaija【5620316263177976733†L137-L143】",
            "hausa": "Fan Mai Caji Da Rana! Ba matsalar wuta!",
            "pidgin": "Rechargeable fan wey dey save you from heat and NEPA wahala! Na money maker for Naija now!"
        }
    },
    "Handcrafted Leather - Kano Leather Bag/Wallet": {
        "captions": {
            "english": "👜 AUTHENTIC Kano Leather Bag - Handcrafted ✨\n55-75% margin! Nigerian leather from Kano - premium, durable, proudly Naija! 🇳🇬\nProfessionals & abroad customers dey rush am! #KanoLeather #MadeInNigeria【5620316263177976733†L30-L35】",
            "hausa": "Jaka Ta Fata Ta Kano - An yi ta da hannu!",
            "pidgin": "Original Kano leather bag - Handmade! Quality wey oyinbo dey rush! E last pass 10 years!"
        }
    }
}

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vendor Caption AI - Trending 2026</title>
<style>
body{font-family:sans-serif; background:#f6f6f7; margin:0; padding:15px}
.container{max-width:520px; margin:auto}
.card{background:white; border-radius:20px; padding:24px; box-shadow:0 10px 30px rgba(0,0,0,0.08); margin-bottom:15px}
h2{margin:0} .sub{color:#666; font-size:13px; margin:8px 0 15px 0}
input, select{width:100%; padding:14px; border:1.5px solid #e5e5e5; border-radius:12px; margin:8px 0; box-sizing:border-box; font-size:16px}
button{width:100%; padding:15px; background:#111; color:white; border:none; border-radius:12px; font-weight:700; font-size:16px; cursor:pointer}
button.secondary{background:#f0f0f0; color:#111; margin-top:10px}
.result{background:#f3f3ff; padding:18px; border-radius:14px; margin-top:15px; white-space:pre-wrap; line-height:1.6}
.badge{background:#111; color:white; padding:4px 10px; border-radius:20px; font-size:11px}
.trend{background:#e8f5e9; border:1px solid #a5d6a7; padding:10px; border-radius:10px; font-size:12px; margin:10px 0}
.paybox{background:#fff8e1; border:1px solid #ffe082; padding:16px; border-radius:14px; font-size:14px}
</style></head>
<body><div class="container"><div class="card">
<h2>🔥 Vendor Caption AI PRO <span class="badge">TRENDING 2026</span></h2>
<div class="sub">Based on live TikTok & Nigeria market data - captions that SELL</div>

{% if not unlocked %}
<div class="paybox">
<b>💳 Unlock {{price}} - Get All Trending Captions</b><br>
Pay to: <b>{{opay}}</b><br><br>
<input id="contact" placeholder="Your WhatsApp or Email">
<button onclick="pay()" style="background:#25D366">I Have Paid - Get Code on WhatsApp</button>
<hr><form method="post"><input name="pwd" placeholder="Have code? Enter here"><button class="secondary">Unlock App</button></form>
</div>
{% else %}
<div class="trend">📈 Currently Trending: Dubai Embroidered Abaya, Lip Oils ($662M sales), Rechargeable Fans, Kano Leather【5620316263177976733†L137-L143】【3517687480467350539†L12-L14】</div>
<form method="post">
<input type="hidden" name="pwd" value="{{pwd}}">
<select name="product_key">
{% for key in products.keys() %}<option value="{{key}}" {% if key==selected_key%}selected{%endif%}>{{key}}</option>{% endfor %}
</select>
<input name="custom_product" placeholder="Or type your own product e.g. Royal Blue Abaya" value="{{custom_product}}">
<select name="lang">
<option value="english" {% if lang=='english'%}selected{%endif%}>English - Instagram/TikTok</option>
<option value="hausa" {% if lang=='hausa'%}selected{%endif%}>Hausa - WhatsApp Status</option>
<option value="pidgin" {% if lang=='pidgin'%}selected{%endif%}>Pidgin - Street Market Vibe</option>
</select>
<button>Generate VIRAL Caption</button>
</form>
{% if caption %}<div class="result">{{caption}}</div>
<button class="secondary" onclick="navigator.clipboard.writeText(document.querySelector('.result').innerText); this.innerText='Copied!'">📋 Copy & Post Now</button>
{% endif %}
<form method="post"><input type="hidden" name="pwd" value="LOGOUT"><button class="secondary" style="margin-top:15px">Lock App</button></form>
{% endif %}
</div><div style="text-align:center; font-size:11px; color:#999">Built on 16GB Phone • Data from TikTok Shop & Jumia Best Sellers 2026 • Abuja</div></div>
<script>
function pay(){
  var c=document.getElementById('contact').value;
  if(!c){alert('Enter WhatsApp/Email');return;}
  var msg="Salam! I paid {{price}} for Vendor AI Trending 2026. My contact: "+c+". Send me code. Paid to {{opay}}";
  window.open("https://wa.me/{{wa}}?text="+encodeURIComponent(msg),'_blank');
}
</script></body></html>
"""

@app.route('/', methods=['GET','POST'])
def home():
    pwd = request.form.get('pwd','')
    unlocked = (pwd == MASTER_PASSWORD) if pwd!="LOGOUT" and pwd!="" else False
    if pwd=="LOGOUT": unlocked=False; pwd=""
    
    selected_key = request.form.get('product_key', list(TRENDING_PRODUCTS.keys())[0])
    custom_product = request.form.get('custom_product','')
    lang = request.form.get('lang','english')
    
    caption = ""
    if unlocked:
        if custom_product.strip():
            # Use custom product with template of selected trending type
            base = TRENDING_PRODUCTS[selected_key]["captions"].get(lang, "")
            caption = base.replace("{p}", custom_product) if "{p}" in base else f"🔥 {custom_product} - {base}"
            if "{p}" not in base and custom_product:
                caption = f"🔥 NEW IN! {custom_product} ✨\n{base}"
        else:
            # Use trending product name itself
            prod_name = selected_key
            caption = TRENDING_PRODUCTS[selected_key]["captions"].get(lang, "")

    return render_template_string(HTML, unlocked=unlocked, pwd=pwd,
                                  products=TRENDING_PRODUCTS, selected_key=selected_key,
                                  custom_product=custom_product, lang=lang,
                                  caption=caption, wa=YOUR_WHATSAPP,
                                  opay=YOUR_OPAY, price=PRICE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)