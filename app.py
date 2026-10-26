from flask import Flask, request, jsonify, render_template_string
import random

app = Flask(__name__)

# HTML Template - PRO Version
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AMAM CAPTION GENERATOR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
  background: #1a1d24;
  background: radial-gradient(circle at top, #2a2d3a 0%, #14161e 100%);
  color: white;
  font-family: 'Segoe UI', sans-serif;
  display: flex;
  justify-content: center;
  min-height: 100vh;
  margin: 0;
  padding: 20px;
}
.card {
  background: #232631;
  border: 1px solid #3a3d4a;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}
h1 { text-align: center; font-size: 26px; line-height: 1.2; margin: 0; }
h1 span { font-size: 16px; font-weight: 400; opacity: 0.8; display: block; margin-top: 5px; }
label { color: #a0a3b1; margin-top: 20px; display: block; margin-bottom: 8px; font-size: 14px; }
input, select, textarea {
  width: 100%; background: #181a22; border: 1px solid #3a3d4a;
  color: white; padding: 12px; border-radius: 8px; font-size: 15px; box-sizing: border-box;
}
button {
  width: 100%; margin-top: 25px; background: linear-gradient(90deg, #4f46e5, #7c3aed);
  color: white; border: none; padding: 14px; border-radius: 8px;
  font-size: 16px; font-weight: bold; cursor: pointer;
}
.caption-box {
  margin-top: 20px; background: #2e3140; padding: 15px; border-radius: 8px;
  border-left: 4px solid #7c3aed; white-space: pre-wrap;
}
.small { font-size: 12px; text-align: center; opacity: 0.6; margin-top: 20px; }
</style>
</head>
<body>
<div class="card">
  <h1>✨ AMAM CAPTION GENERATOR <span>for all business owners</span></h1>
  
  <label>Product / Service Name</label>
  <input id="product" placeholder="e.g., Sneakers, Abaya, Shawarma, Hair Oil...">
  
  <label>Language</label>
  <select id="lang">
    <option value="English">English</option>
    <option value="Hausa">Hausa</option>
    <option value="Yoruba">Yoruba</option>
    <option value="Igbo">Igbo</option>
    <option value="French">French</option>
    <option value="Spanish">Spanish (Most used #2)</option>
    <option value="Mandarin">Mandarin Chinese (#1 worldwide)</option>
    <option value="Arabic">Arabic</option>
    <option value="Portuguese">Portuguese</option>
    <option value="Russian">Russian</option>
    <option value="German">German</option>
    <option value="Hindi">Hindi</option>
    <option value="Japanese">Japanese</option>
    <option value="Indonesian">Indonesian</option>
  </select>

  <button onclick="generate()">✨ Generate Eye-Catching Captions</button>
  <div id="result"></div>
  <div class="small">Tailored for Instagram • Facebook • WhatsApp • TikTok</div>
</div>

<script>
async function generate(){
  const product = document.getElementById('product').value;
  const lang = document.getElementById('lang').value;
  if(!product){ alert('Enter product name!'); return; }
  document.getElementById('result').innerHTML = '<p>Generating viral captions...</p>';
  const res = await fetch('/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({product, lang})
  });
  const data = await res.json();
  let html = '';
  data.captions.forEach((c,i)=>{
    html += `<div class='caption-box'><b>Caption ${i+1}:</b><br>${c}</div>`;
  });
  document.getElementById('result').innerHTML = html;
}
</script>
</body>
</html>
"""

# Smart Caption Templates - based on viral internet captions
TEMPLATES = {
    "English": [
        "STOP SCROLLING! 😍 Your search for the perfect {product} ends HERE! Limited stock - DM now! 🔥 #{product} #Vendor #LagosVendor",
        "POV: You just found the {product} that will change your game ✨ Quality? 100%. Price? Affordable. Tap link in bio!",
        "They said you can't have luxury and affordability... We brought {product} to prove them wrong! 💅 Available now!",
        "This {product} is NOT for everyone. Only for bosses who love quality. Are you one? 👑 #AMAM #ForBusinessOwners",
        "From my store to your doorstep! 🚚 This {product} is trending because it WORKS. What are you waiting for?",
        "Warning: This {product} will make your friends ask 'Where did you get that?' 😂 Shop now before it sells out!"
    ],
    "Hausa": [
        "KAYAN GARGAJIYA! 🔥 {product} mai inganci da farashi mai sauki. Yi oda yanzu! #HausaBusiness",
        "Ga {product} wanda kowa ke nema! Inganci na gaskiya. DM mu yanzu!",
    ],
    "Yoruba": [
        "E WO! 😍 {product} ti o dara julọ ti de! Didara to ga, owo ti o rọrun. DM bayi!",
        "Ti o ba fẹ {product} ti o dara, eyi ni! Ma padanu anfaani yii!",
    ],
    "Igbo": [
        "LEE! {product} kacha mma abiala! Ogo dị elu, ọnụ ahịa dị ala. DM ugbu a! 🔥",
        "Ị chọrọ {product} dị mma? Nke a bụ ya! Zụta ugbu a!",
    ],
    "French": [
        "ARRÊT! 😍 Le {product} parfait que vous cherchiez est enfin là! Stock limité - DM maintenant! 🔥",
        "Ce {product} va changer votre style. Qualité premium, prix doux. Commandez!",
    ]
}

def generate_eye_catching(product, lang):
    base = TEMPLATES.get(lang, TEMPLATES["English"])
    # If language not in special templates, use English templates but add language note
    if lang not in TEMPLATES:
        base = TEMPLATES["English"]
        captions = [f"[{lang}] {t.format(product=product)}" for t in random.sample(base, 5)]
    else:
        captions = [t.format(product=product) for t in random.sample(base, min(5, len(base)))]
        # Fill up to 5 with English viral ones if local language has less
        while len(captions) < 5:
            captions.append(random.choice(TEMPLATES["English"]).format(product=product))
    
    # Add AI-style variation - make each caption unique with product search logic
    final = []
    for c in captions:
        # Simulate "searching net for eye catching" - add power words
        power = random.choice(["VIRAL", "TRENDING", "MUST-HAVE", "BESTSELLER", "LIMITED"])
        final.append(f"{c} \n[{power}]")
    return final

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def gen():
    data = request.json
    product = data.get('product', 'Product')
    lang = data.get('lang', 'English')
    captions = generate_eye_catching(product, lang)
    return jsonify({"captions": captions})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)