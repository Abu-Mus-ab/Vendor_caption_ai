from flask import Flask, request, jsonify, render_template_string, session, redirect
app = Flask(__name__)
app.secret_key = "amam_final_fix_2026"

MY_PASSWORD = "AMAM@2024"
OPAY_NAME = "ABDULLAHI MUHAMMAD"
OPAY_NUMBER = "9039019035"
WHATSAPP_NUMBER = "2347086332888"
PRICE = "N3000"

LOGIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<title>AMAM</title>
<style>
*{font-family:Inter,sans-serif;box-sizing:border-box}
body{background:#f8fafc;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:15px}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:30px;width:100%;max-width:400px;text-align:center;box-shadow:0 10px 20px rgba(0,0,0,.05)}
input{width:100%;padding:14px;border:1px solid #cbd5e1;border-radius:24px;text-align:center;margin-top:15px}
button{margin-top:15px;background:#2563eb;color:#fff;border:none;padding:12px;border-radius:24px;font-weight:700;width:100%;cursor:pointer}
.pay{background:#f1f5f9;padding:12px;border-radius:12px;margin-top:15px;font-size:13px}
</style></head><body>
<div class="box">
<h2>AMAM CAPTION GENERATOR</h2>
<p><b>(for all business owners)</b><br>{{PRICE}}/month</p>
<form method="POST"><input type="password" name="pwd" placeholder="Enter password" required><button>Unlock</button></form>
<div class="pay">Opay: <b>{{OPAY_NAME}} - {{OPAY_NUMBER}}</b><br>{{PRICE}}<br><a href="https://wa.me/{{WHATSAPP_NUMBER}}">WhatsApp</a></div>
</div></body></html>
"""

MAIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<title>AMAM CAPTION GENERATOR</title>
<style>
*{font-family:Inter,sans-serif;box-sizing:border-box}
body{background:#fff;color:#0f172a;margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:15px}
h1{font-weight:800;font-size:28px;text-align:center;margin-top:30px}
h1 span{display:block;font-weight:500;font-size:14px;color:#64748b;margin-top:5px}
.search{margin-top:25px;width:100%;max-width:600px;background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:20px;box-shadow:0 5px 20px rgba(0,0,0,.05)}
input[type=text]{width:100%;padding:14px 18px;border:1px solid #e2e8f0;border-radius:12px;font-size:16px}
select{width:100%;padding:12px;margin-top:12px;border:1px solid #e2e8f0;border-radius:12px;font-weight:600}
.btn{margin-top:15px;width:100%;background:#2563eb;color:#fff;border:none;padding:14px;border-radius:12px;font-weight:800;cursor:pointer}
.cap{border:1px solid #e2e8f0;border-left:4px solid #2563eb;padding:12px;border-radius:10px;margin-bottom:10px;font-size:14px;line-height:1.5}
</style></head><body>
<h1>AMAM CAPTION GENERATOR <span>FOR ALL BUSINESS OWNERS</span></h1>
<div class="search">
<input id="product" type="text" placeholder="Product e.g Sneakers">
<select id="lang">
<option>English</option><option>Hausa</option><option>Yoruba</option><option>Igbo</option><option>French</option>
<option>Spanish</option><option>Mandarin</option><option>Arabic</option><option>Portuguese</option><option>Russian</option>
<option>German</option><option>Hindi</option><option>Japanese</option><option>Indonesian</option>
</select>
<button class="btn" onclick="gen()">Generate Captions</button>
<div id="res" style="margin-top:20px"></div>
</div>
<script>
async function gen(){
 var p=document.getElementById('product').value;
 var l=document.getElementById('lang').value;
 if(!p){alert('Enter product');return;}
 document.getElementById('res').innerHTML='<b>Searching best captions for '+l+'...</b>';
 var r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:p,lang:l})});
 var d=await r.json();
 var h='';
 for(var i=0;i<d.captions.length;i++){h+='<div class=cap><b>Caption '+(i+1)+':</b><br>'+d.captions[i]+'</div>';}
 document.getElementById('res').innerHTML=h;
}
</script></body></html>
"""

def get_captions(product, lang):
    en1 = "STOP SCROLLING Your perfect PRODUCT is HERE Premium quality Limited stock DM NOW".replace("PRODUCT", product)
    en2 = "POV You just found PRODUCT that will change your game 100 Quality Guaranteed".replace("PRODUCT", product)
    en3 = "Luxury plus Affordable Yes PRODUCT proves them WRONG Bosses only Shop now".replace("PRODUCT", product)
    en4 = "TRENDING NOW This PRODUCT is selling FAST because it WORKS From my store to your door".replace("PRODUCT", product)
    en5 = "WARNING This PRODUCT will make everyone ask you Bestseller 2026 Order now".replace("PRODUCT", product)
    en = [en1, en2, en3, en4, en5]

    ha1 = "DENA GUNGURUWA Ga PRODUCT mai inganci Farashi mai sauki Yi oda yanzu".replace("PRODUCT", product)
    ha2 = "Kun taba ganin PRODUCT irin wannan Masu gane inganci kadai DM yanzu".replace("PRODUCT", product)
    ha3 = "Wanda ya san darajar kudi zai sayi PRODUCT Ana sayarwa da sauri".replace("PRODUCT", product)
    ha4 = "Mafi sayarwa PRODUCT yana aiki sosai Daga shagona zuwa gidanka".replace("PRODUCT", product)
    ha5 = "GARGADI PRODUCT zai sa kowa ya tambayeka Yi oda kafin ya kare".replace("PRODUCT", product)
    hausa = [ha1, ha2, ha3, ha4, ha5]

    yo1 = "E DAKU PRODUCT to dara ti de Didara 100 owo ti o rorun DM bayi".replace("PRODUCT", product)
    yo2 = "Iwo nikan ni o ye ki o ni PRODUCT yii Awon oga nikan Pase bayi".replace("PRODUCT", product)
    yo3 = "Ti o ba fe didara PRODUCT ni Ma je ki o koja e".replace("PRODUCT", product)
    yo4 = "Ti n ta lowolowo PRODUCT n ta nitori pe o sise Lati ile itaja mi".replace("PRODUCT", product)
    yo5 = "IKILO PRODUCT yii yoo je ki gbogbo eniyan beere Pase ki o to tan".replace("PRODUCT", product)
    yoruba = [yo1, yo2, yo3, yo4, yo5]

    ig1 = "KWUSI IPIA PRODUCT kacha mma abiala Ogo 100 onu ala DM ugbu a".replace("PRODUCT", product)
    ig2 = "I chotara PRODUCT ga-agbanwe udi gi Ndi isi naani Zuta ugbu a".replace("PRODUCT", product)
    ig3 = "Ha siri na inweghi ike inwe okomoko PRODUCT gosiri na ha ezighi ezi".replace("PRODUCT", product)
    ig4 = "Na-ere ugbu a PRODUCT na-ere ngwa ngwa nihi na o na-aru oru".replace("PRODUCT", product)
    ig5 = "IDOKA PRODUCT a ga-eme ka onye obula juo Zuta tupu o gwu".replace("PRODUCT", product)
    igbo = [ig1, ig2, ig3, ig4, ig5]

    fr1 = "ARRETE Le PRODUCT parfait est la Qualite premium prix doux DM".replace("PRODUCT", product)
    fr2 = "POV Vous venez de trouver le PRODUCT qui va changer votre style".replace("PRODUCT", product)
    fr3 = "Luxe plus abordable PRODUCT prouve le contraire".replace("PRODUCT", product)
    fr4 = "TENDANCE Ce PRODUCT se vend VITE car il MARCHE".replace("PRODUCT", product)
    fr5 = "ATTENTION Ce PRODUCT va faire demander Ou las tu eu Bestseller".replace("PRODUCT", product)
    french = [fr1, fr2, fr3, fr4, fr5]

    if lang == "Hausa": return hausa
    if lang == "Yoruba": return yoruba
    if lang == "Igbo": return igbo
    if lang == "French": return french
    if lang == "English": return en
    out = []
    for c in en: out.append("[" + lang + "] " + c)
    return out

@app.route('/', methods=['GET','POST'])
def home():
    if session.get('auth'):
        return render_template_string(MAIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)
    if request.method == 'POST':
        if request.form.get('pwd') == MY_PASSWORD:
            session['auth'] = True
            return render_template_string(MAIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)
        return "<h3 style=text-align:center;margin-top:100px>Wrong Password<br><a href='/'>Try again</a></h3>"
    return render_template_string(LOGIN_HTML, OPAY_NAME=OPAY_NAME, OPAY_NUMBER=OPAY_NUMBER, WHATSAPP_NUMBER=WHATSAPP_NUMBER, PRICE=PRICE)

@app.route('/generate', methods=['POST'])
def generate():
    if not session.get('auth'): return jsonify({"captions":[]})
    data = request.json
    product = data.get('product','Product')
    lang = data.get('lang','English')
    captions = get_captions(product, lang)
    return jsonify({"captions": captions})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)