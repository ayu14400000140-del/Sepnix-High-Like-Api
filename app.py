from flask import Flask, request, jsonify, render_template_string
import json
import binascii
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import aiohttp
import asyncio
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from google.protobuf.json_format import MessageToJson
import uid_generator_pb2
import like_count_pb2

app = Flask(__name__)

# ---------- CONFIG ----------
TOTAL_VISITS = 5050          # Fixed total visits
CONCURRENT_LIMIT = 50        # Max concurrent requests (avoid overload)
# ----------------------------

def load_tokens(region):
    try:
        if region == "IND":
            with open("token_ind.json", "r") as f:
                tokens = json.load(f)
        elif region in {"BR", "US", "SAC", "NA"}:
            with open("token_br.json", "r") as f:
                tokens = json.load(f)
        else:
            with open("token_bd.json", "r") as f:
                tokens = json.load(f)
        return tokens
    except:
        return None

def encrypt_message(plaintext):
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        encrypted_message = cipher.encrypt(padded_message)
        return binascii.hexlify(encrypted_message).decode('utf-8')
    except:
        return None

def create_protobuf(uid):
    try:
        message = uid_generator_pb2.uid_generator()
        message.saturn_ = int(uid)
        message.garena = 1
        return message.SerializeToString()
    except:
        return None

def enc(uid):
    protobuf_data = create_protobuf(uid)
    if protobuf_data is None:
        return None
    encrypted_uid = encrypt_message(protobuf_data)
    return encrypted_uid

async def make_request_async(encrypt, region, token, session, semaphore):
    async with semaphore:
        try:
            if region == "IND":
                url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
            elif region in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
            else:
                url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

            edata = bytes.fromhex(encrypt)
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Authorization': f"Bearer {token}",
                'Content-Type': "application/x-www-form-urlencoded",
                'Expect': "100-continue",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB55"
            }

            async with session.post(url, data=edata, headers=headers, ssl=False, timeout=10) as response:
                if response.status != 200:
                    return None
                hex_data = await response.read()
                binary = bytes.fromhex(hex_data.hex())
                return decode_protobuf(binary)
        except:
            return None

def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except:
        return None

# ---------------- HTML UI ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FF Visit Tool — AyushXSarkar</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Poppins',sans-serif; }
  body {
    min-height:100vh;
    background: radial-gradient(circle at 20% 20%, #1e3c72, #0f172a 60%);
    display:flex; align-items:center; justify-content:center;
    padding:20px; color:#fff;
  }
  .card {
    width:100%; max-width:480px;
    background: rgba(255,255,255,0.06);
    border:1px solid rgba(255,255,255,0.12);
    border-radius:22px;
    padding:32px 26px;
    backdrop-filter: blur(14px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    animation: fadeIn .6s ease;
  }
  @keyframes fadeIn { from{opacity:0; transform:translateY(20px);} to{opacity:1; transform:translateY(0);} }
  .logo {
    text-align:center; font-size:26px; font-weight:800;
    background: linear-gradient(90deg,#00d4ff,#7b2ff7,#ff2e63);
    -webkit-background-clip:text; background-clip:text; color:transparent;
    letter-spacing:1px; margin-bottom:4px;
  }
  .sub { text-align:center; font-size:12px; color:#9aa7bd; margin-bottom:24px; letter-spacing:.5px; }
  label { font-size:13px; color:#c7d2e3; display:block; margin-bottom:6px; font-weight:600; }
  input, select {
    width:100%; padding:13px 14px; border-radius:12px;
    border:1px solid rgba(255,255,255,0.15);
    background: rgba(0,0,0,0.25); color:#fff;
    font-size:14px; outline:none; transition:.25s;
    margin-bottom:16px;
  }
  input:focus, select:focus {
    border-color:#00d4ff; box-shadow:0 0 0 3px rgba(0,212,255,0.15);
  }
  select option { background:#0f172a; }
  button {
    width:100%; padding:14px; border:none; border-radius:12px;
    background: linear-gradient(90deg,#00d4ff,#7b2ff7);
    color:#fff; font-weight:700; font-size:15px; cursor:pointer;
    transition:.25s; letter-spacing:.5px;
  }
  button:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(123,47,247,0.45); }
  button:disabled { opacity:.6; cursor:not-allowed; transform:none; }
  .result {
    margin-top:22px; padding:18px; border-radius:14px;
    background: rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.1);
    font-size:13px; display:none;
  }
  .result.show { display:block; animation: fadeIn .4s ease; }
  .row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px dashed rgba(255,255,255,0.08); }
  .row:last-child { border-bottom:none; }
  .row span:first-child { color:#9aa7bd; }
  .row span:last-child { font-weight:600; color:#fff; }
  .ok { color:#00e676 !important; }
  .bad { color:#ff5252 !important; }
  .credit {
    text-align:center; margin-top:22px; font-size:12px; color:#8a96ad;
  }
  .credit b {
    background: linear-gradient(90deg,#00d4ff,#ff2e63);
    -webkit-background-clip:text; background-clip:text; color:transparent;
  }
  .spinner {
    display:inline-block; width:16px; height:16px; border:2px solid rgba(255,255,255,.3);
    border-top-color:#fff; border-radius:50%; animation: spin .7s linear infinite;
    vertical-align:middle; margin-right:8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <div class="card">
    <div class="logo">FF VISIT TOOL</div>
    <div class="sub">Powered by AyushXSarkar • 10k Visits Fixed</div>

    <label for="uid">Player UID</label>
    <input id="uid" type="text" placeholder="Enter target UID" autocomplete="off">

    <label for="region">Region</label>
    <select id="region">
      <option value="IND">IND — India</option>
      <option value="BR">BR — Brazil</option>
      <option value="US">US — United States</option>
      <option value="SAC">SAC — South America</option>
      <option value="NA">NA — North America</option>
      <option value="BD">BD — Bangladesh</option>
    </select>

    <button id="btn" onclick="sendVisit()">🚀 Send 10k Visits</button>

    <div class="result" id="result"></div>

    <div class="credit">Made with ❤️ by <b>AyushXSarkar</b></div>
  </div>

<script>
async function sendVisit() {
  const uid = document.getElementById('uid').value.trim();
  const region = document.getElementById('region').value;
  const btn = document.getElementById('btn');
  const result = document.getElementById('result');

  if (!uid) { alert('Please enter UID'); return; }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Sending 10k visits...';
  result.classList.remove('show');
  result.innerHTML = '';

  try {
    const res = await fetch(`/visit?uid=${encodeURIComponent(uid)}&region=${encodeURIComponent(region)}`);
    const data = await res.json();
    result.classList.add('show');

    if (data.error) {
      result.innerHTML = `<div class="row"><span>Error</span><span class="bad">${data.error}</span></div>`;
    } else {
      result.innerHTML = `
        <div class="row"><span>Player Nickname</span><span>${data.PlayerNickname || '—'}</span></div>
        <div class="row"><span>UID</span><span>${data.UID || '—'}</span></div>
        <div class="row"><span>Total Visits</span><span>${data.TotalVisits}</span></div>
        <div class="row"><span>Successful</span><span class="ok">${data.SuccessfulVisits}</span></div>
        <div class="row"><span>Failed</span><span class="bad">${data.FailedVisits}</span></div>
        <div class="row"><span>Tokens Loaded</span><span>${data.TokensLoaded}</span></div>
      `;
    }
  } catch (e) {
    result.classList.add('show');
    result.innerHTML = `<div class="row"><span>Error</span><span class="bad">${e.message}</span></div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Send 10k Visits';
  }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/visit', methods=['GET'])
async def visit():
    target_uid = request.args.get("uid")
    region = request.args.get("region", "").upper()

    if not target_uid or not region:
        return jsonify({"error": "Target UID and region are required"}), 400

    try:
        tokens = load_tokens(region)
        if not tokens:
            raise Exception("Failed to load tokens for this region.")

        encrypted_target_uid = enc(target_uid)
        if encrypted_target_uid is None:
            raise Exception("Encryption of target UID failed.")

        tokens_loaded = len(tokens)

        # Build a list of exactly TOTAL_VISITS tokens by cycling through available tokens
        token_pool = [t['token'] for t in tokens]
        request_tokens = []
        i = 0
        while len(request_tokens) < TOTAL_VISITS:
            request_tokens.append(token_pool[i % len(token_pool)])
            i += 1

        # Shuffle so the same token isn't hammered back-to-back
        random.shuffle(request_tokens)

        semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
        success_count = 0
        failed_count = 0
        player_name = None
        player_uid = None

        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request_async(encrypted_target_uid, region, tok, session, semaphore)
                for tok in request_tokens
            ]
            results = await asyncio.gather(*tasks)

        for info in results:
            if info is not None:
                if player_name is None and player_uid is None:
                    try:
                        jsone = MessageToJson(info)
                        data_info = json.loads(jsone)
                        player_name = str(data_info.get('AccountInfo', {}).get('PlayerNickname', ''))
                        player_uid = int(data_info.get('AccountInfo', {}).get('UID', 0))
                    except:
                        pass
                success_count += 1
            else:
                failed_count += 1

        summary = {
            "TotalVisits": TOTAL_VISITS,
            "SuccessfulVisits": success_count,
            "FailedVisits": failed_count,
            "PlayerNickname": player_name,
            "UID": player_uid,
            "TokensLoaded": tokens_loaded
        }
        return jsonify(summary)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)