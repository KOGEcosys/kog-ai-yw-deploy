import os, json, sqlite3, secrets, hashlib, hmac, html
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
from urllib.parse import urlparse, parse_qs
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('KOG_DATA_DIR', ROOT / 'data'))
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = Path(os.environ.get('KOG_DATABASE_PATH', DATA_DIR / 'kog_wallet_exchange.db'))
SESSION_COOKIE = 'kog_wallet_session'
LOCAL_PERCENT = 80
HQ_PERCENT = 20
KCOIN_PERCENT = 100
SESSION_HOURS = 12
DEFAULT_ADMIN_USER = os.environ.get('KOG_ADMIN_USERNAME', 'wenscenter')
DEFAULT_ADMIN_PASSWORD = os.environ.get('KOG_ADMIN_PASSWORD', 'KOG.ONE.2026July')

def now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def make_code(prefix):
    return prefix + '-' + datetime.utcnow().strftime('%Y%m%d') + '-' + secrets.token_hex(3).upper()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rowdict(row):
    return dict(row) if row else None

def rows(rows):
    return [dict(r) for r in rows]

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 180000).hex()
    return salt, digest

def verify_password(password, salt, digest):
    _, test = hash_password(password, salt)
    return hmac.compare_digest(test, digest)

def calc(value):
    try:
        v = max(float(value or 0), 0)
    except Exception:
        v = 0
    return {
        'local_share_value': round(v * LOCAL_PERCENT / 100, 2),
        'hq_share_value': round(v * HQ_PERCENT / 100, 2),
        'kcoin_supply_value': round(v * KCOIN_PERCENT / 100, 2)
    }

def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions(
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS participants(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_type TEXT NOT NULL,
            display_name TEXT NOT NULL,
            organization_name TEXT,
            country TEXT, city TEXT, region TEXT,
            email TEXT, phone TEXT, line_id TEXT, wechat_id TEXT, whatsapp_id TEXT, telegram_id TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            participant_id INTEGER NOT NULL,
            contribution_type TEXT NOT NULL,
            contribution_title TEXT NOT NULL,
            contribution_description TEXT,
            requested_exchange TEXT,
            proposed_value REAL DEFAULT 0,
            confirmed_value REAL,
            currency TEXT DEFAULT 'K.NTD',
            accepts_80_20 INTEGER DEFAULT 1,
            financial_flag INTEGER DEFAULT 0,
            status TEXT DEFAULT 'submitted',
            compliance_status TEXT DEFAULT 'standard',
            local_consensus_note TEXT,
            local_share_value REAL DEFAULT 0,
            hq_share_value REAL DEFAULT 0,
            kcoin_supply_value REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(participant_id) REFERENCES participants(id)
        );
        CREATE TABLE IF NOT EXISTS contact_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            contact_method TEXT,
            contact_summary TEXT NOT NULL,
            next_step TEXT,
            contacted_by TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            trade_code TEXT UNIQUE NOT NULL,
            trade_title TEXT NOT NULL,
            trade_terms TEXT NOT NULL,
            agreed_value REAL DEFAULT 0,
            currency TEXT DEFAULT 'K.NTD',
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS distributions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            trade_id INTEGER,
            total_value REAL DEFAULT 0,
            local_percent REAL DEFAULT 80,
            hq_percent REAL DEFAULT 20,
            kcoin_percent REAL DEFAULT 100,
            local_share_value REAL DEFAULT 0,
            hq_share_value REAL DEFAULT 0,
            kcoin_supply_value REAL DEFAULT 0,
            status TEXT DEFAULT 'allocated',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            action TEXT,
            entity TEXT,
            entity_id INTEGER,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        ''')
        exists = c.execute('SELECT id FROM users WHERE username=?', (DEFAULT_ADMIN_USER,)).fetchone()
        if not exists:
            salt, digest = hash_password(DEFAULT_ADMIN_PASSWORD)
            c.execute('INSERT INTO users(username,password_salt,password_hash,role,created_at) VALUES(?,?,?,?,?)', (DEFAULT_ADMIN_USER, salt, digest, 'admin', now()))

STYLE = r'''
:root{--bg:#071224;--card:#101d33;--gold:#f2c766;--green:#32d39a;--text:#f7fbff;--muted:#a9b7cf;--line:rgba(255,255,255,.12);--danger:#ff7979}*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif;background:radial-gradient(circle at top left,#17345f,#071224 48%,#040914);color:var(--text)}a{color:inherit}.nav{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;padding:18px 7vw;background:rgba(7,18,36,.75);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}.brand{display:flex;gap:12px;align-items:center;font-weight:900}.mark{width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,var(--gold),#fff1b8);color:#071224;display:grid;place-items:center}.links{display:flex;gap:16px;align-items:center}.btn,button{border:0;border-radius:999px;padding:12px 18px;font-weight:800;background:#1b2e4e;color:var(--text);cursor:pointer}.btn.gold,button.gold{background:linear-gradient(135deg,var(--gold),#ffe9a3);color:#10203a}.btn.green,button.green{background:linear-gradient(135deg,var(--green),#9fffd8);color:#10203a}.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:40px;align-items:center;padding:72px 7vw}.eyebrow{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-size:13px;font-weight:900}.hero h1{font-size:clamp(42px,6vw,76px);line-height:1.03;margin:12px 0}.hero p{font-size:19px;color:var(--muted);line-height:1.7}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.phone{border:1px solid var(--line);background:linear-gradient(160deg,rgba(255,255,255,.14),rgba(255,255,255,.04));border-radius:38px;padding:22px;box-shadow:0 40px 100px rgba(0,0,0,.45)}.screen{background:#071224;border-radius:28px;padding:20px;border:1px solid var(--line)}.wallet-card{border-radius:24px;padding:22px;background:linear-gradient(135deg,#f2c766,#fff1b8);color:#10203a;margin-bottom:16px}.coupon{background:#fff;color:#10203a;border-radius:20px;padding:16px;margin:12px 0}.qr{width:82px;height:82px;background:repeating-linear-gradient(45deg,#111 0 8px,#fff 8px 16px);border-radius:10px}.section{padding:70px 7vw}.section h2{font-size:clamp(30px,4vw,48px);margin:0 0 14px}.lead{color:var(--muted);max-width:900px;line-height:1.7}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-top:28px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin-top:28px}.card{background:rgba(255,255,255,.075);border:1px solid var(--line);border-radius:26px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.22)}.card h3{margin-top:0}.icon{font-size:34px;margin-bottom:12px}.flow{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:24px}.step{padding:18px;border-radius:18px;border:1px solid var(--line);background:rgba(255,255,255,.06)}.split{display:grid;grid-template-columns:4fr 1fr;gap:18px}.big-num{font-size:54px;font-weight:900;color:var(--gold)}label{display:block;color:var(--muted);font-size:13px;font-weight:800;margin:0 0 8px}input,select,textarea{width:100%;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.08);color:var(--text);padding:13px 14px;outline:none}textarea{min-height:110px}.field{margin-bottom:14px}.formgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.full{grid-column:1/-1}.notice{padding:14px 16px;border-radius:16px;background:rgba(242,199,102,.14);border:1px solid rgba(242,199,102,.28)}.success{padding:14px 16px;border-radius:16px;background:rgba(50,211,154,.13);border:1px solid rgba(50,211,154,.32)}.danger{padding:14px 16px;border-radius:16px;background:rgba(255,121,121,.13);border:1px solid rgba(255,121,121,.32)}table{width:100%;border-collapse:collapse}td,th{padding:12px;border-bottom:1px solid var(--line);text-align:left}.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:12px}.admin{padding:32px 7vw}.modal{position:fixed;inset:0;background:rgba(0,0,0,.7);display:none;place-items:center;padding:24px}.modal.open{display:grid}.modalbox{max-width:1000px;max-height:86vh;overflow:auto;background:#0b1730;border:1px solid var(--line);border-radius:28px;padding:24px}.toprow{display:flex;justify-content:space-between;gap:12px;align-items:center}@media(max-width:900px){.hero,.grid2,.grid3,.split{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}.flow{grid-template-columns:1fr 1fr}.links{display:none}.formgrid{grid-template-columns:1fr}}@media(max-width:560px){.grid,.flow{grid-template-columns:1fr}.hero{padding-top:42px}}
'''

INDEX_HTML = r'''<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KOG Wallet｜互助交换系统</title><style>''' + STYLE + r'''</style></head><body><nav class="nav"><div class="brand"><div class="mark">K</div><div>KOG Wallet<br><small style="color:var(--muted)">Mutual Exchange Gateway</small></div></div><div class="links"><a href="#apply">提出申请</a><a href="#flow">流程</a><a href="#exchange">互助交换</a><a class="btn gold" href="/admin.html">后台登录</a></div></nav><main><section class="hero"><div><div class="eyebrow">KOG Wallet Web App</div><h1>地方互助交换，进入真实流通。</h1><p>KOG Wallet 让买方、卖方、商家、教会、非盈利机构、时间银行成员都能提交可兑换的货物、服务、时间、空间、现金或权益。地方 KOG 团队联系、审核、媒合与完成初步交易；地方保留 80% 形成本位价值体，总部取得 20% 支持系统运营，并供应 100% KCOINs 给参与买卖方。</p><div class="actions"><a class="btn gold" href="#apply">立即提出交换申请</a><a class="btn green" href="#exchange">了解 80/20 制度</a></div></div><div class="phone"><div class="screen"><div class="wallet-card"><b>KOG Mutual Exchange</b><h2 style="margin:.4em 0">100% KCOINs</h2><small>依据地方共识价值自动记录</small></div><div class="coupon"><b>地方资源池 80%</b><p>由当地 KOG 联盟、非盈利机构、教会或时间银行承接。</p></div><div class="coupon"><b>KOG 总部 20%</b><p>用于平台、风控、审核、技术与全球运营。</p><div class="qr"></div></div></div></div></section><section id="exchange" class="section"><div class="eyebrow">What can be exchanged</div><h2>任何真实可验证资源，都可以提出申请。</h2><p class="lead">我们尽量不干预各地区的商务价值评估，而是提供登记、资料库、审核、联系、交易记录、分配与 KCOINs 记录。实际价值由地方买卖双方、非盈利机构、教会、时间银行或 KOG 成员形成共识。</p><div class="grid"><div class="card"><div class="icon">📦</div><h3>货物</h3><p>库存、农产品、设备、礼品、日用品。</p></div><div class="card"><div class="icon">🛠️</div><h3>服务</h3><p>课程、顾问、美容、维修、餐饮、照护。</p></div><div class="card"><div class="icon">⏱️</div><h3>时间</h3><p>志工时数、陪伴、教学、翻译、接送。</p></div><div class="card"><div class="icon">🏛️</div><h3>空间</h3><p>教室、店面、会议室、展位、场地。</p></div></div><div class="grid2"><div class="card"><div class="big-num">80%</div><h3>地方 KOG 交换系统</h3><p>各地区 KOG 联盟、教会、非盈利机构与时间银行保留交换物件或权益，形成地方本位价值体。</p></div><div class="card"><div class="big-num">20%</div><h3>KOG 总部</h3><p>作为中央交换、系统维护、风控审核、跨区媒合、技术与全球推广资源。</p></div></div></section><section id="flow" class="section"><div class="eyebrow">Process</div><h2>从申请到初步交易的自动化流程</h2><div class="flow"><div class="step"><b>1</b><br>网上申请登录</div><div class="step"><b>2</b><br>提交资源与需求</div><div class="step"><b>3</b><br>地方团队联系</div><div class="step"><b>4</b><br>形成交易共识</div><div class="step"><b>5</b><br>80/20 分配记录</div><div class="step"><b>6</b><br>100% KCOINs 供应</div></div></section><section id="apply" class="section"><div class="eyebrow">Application</div><h2>提出 KOG 互助交换申请</h2><p class="lead">请填写真实资料。涉及证券、金融商品、投资合约、收益权等项目会进入合规审查，不走普通互助交换流程。</p><div class="grid2"><form id="exchangeForm" class="card"><div class="formgrid"><div class="field"><label>申请身份</label><select name="participant_type"><option value="buyer">买方</option><option value="seller">卖方</option><option value="both">买卖双方</option><option value="merchant">商家</option><option value="church">教会</option><option value="nonprofit">非盈利机构</option><option value="time_bank">时间银行</option><option value="individual">个人</option><option value="enterprise">企业</option></select></div><div class="field"><label>姓名 / 负责人</label><input name="display_name" required></div><div class="field"><label>机构名称</label><input name="organization_name"></div><div class="field"><label>Email</label><input name="email" type="email"></div><div class="field"><label>电话</label><input name="phone"></div><div class="field"><label>地区</label><input name="city" placeholder="城市 / 乡镇"></div><div class="field"><label>贡献类型</label><select name="contribution_type"><option value="goods">货物</option><option value="service">服务</option><option value="time">时间</option><option value="space">空间</option><option value="cash">现金</option><option value="rights">权益</option><option value="special_asset">特殊资产</option></select></div><div class="field"><label>预估价值</label><input id="value" name="proposed_value" type="number" step="0.01" value="1000"></div><div class="field"><label>币别 / 单位</label><input id="currency" name="currency" value="K.NTD"></div><div class="field"><label>资源标题</label><input name="contribution_title" required></div><div class="field full"><label>可兑换产品 / 服务 / 现金说明</label><textarea name="contribution_description" required></textarea></div><div class="field full"><label>希望交换或对接什么？</label><textarea name="requested_exchange"></textarea></div><div class="field full"><label><input style="width:auto" type="checkbox" name="financial_flag" value="1"> 涉及证券、金融商品、投资合约或收益权，需要合规审查</label></div></div><button class="gold" type="submit">送出申请</button><div id="result" style="margin-top:14px"></div></form><div class="card"><h3>即时分配试算</h3><p>依据申请人提出价值自动试算，最终以地方共识与审核确认值为准。</p><table><tr><th>地方资源池 80%</th><td id="localCalc">800 K.NTD</td></tr><tr><th>KOG 总部 20%</th><td id="hqCalc">200 K.NTD</td></tr><tr><th>KCOINs 100% 供应</th><td id="kcoinCalc">1000 KCOINs</td></tr></table><div class="notice" style="margin-top:16px">KCOINs / K.NTD 在本系统中作为生态权益、优惠券、互助交换与记录单位；不应表述为固定投资收益或保证现金兑付。</div></div></div></section></main><footer class="section" style="border-top:1px solid var(--line)">Copyright @ KOG.ONE · KOG Wallet Mutual Exchange System</footer><script>function $(s){return document.querySelector(s)}function money(v,c){return Number(v||0).toLocaleString()+" "+(c||"K.NTD")}function calc(){let v=Number($('#value').value||0),c=$('#currency').value||'K.NTD';$('#localCalc').textContent=money(v*.8,c);$('#hqCalc').textContent=money(v*.2,c);$('#kcoinCalc').textContent=money(v,'KCOINs')}$('#value').addEventListener('input',calc);$('#currency').addEventListener('input',calc);calc();$('#exchangeForm').addEventListener('submit',async e=>{e.preventDefault();let data=Object.fromEntries(new FormData(e.target).entries());data.accepts_80_20=1;let r=$('#result');r.innerHTML='<div class="notice">正在送出...</div>';try{let res=await fetch('/api/applications',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let j=await res.json();if(!res.ok||!j.ok)throw Error(j.error||'送出失败');r.innerHTML='<div class="success"><b>申请已送出</b><br>编号：'+j.code+'<br>地方80%：'+money(j.distribution.local_share_value,data.currency)+'｜总部20%：'+money(j.distribution.hq_share_value,data.currency)+'｜KCOINs：'+money(j.distribution.kcoin_supply_value,'KCOINs')+'</div>';e.target.reset();calc()}catch(err){r.innerHTML='<div class="danger">'+err.message+'</div>'}})</script></body></html>'''

ADMIN_HTML = r'''<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KOG Wallet 后台</title><style>''' + STYLE + r'''</style></head><body><nav class="nav"><div class="brand"><div class="mark">K</div><div>KOG Wallet Admin<br><small style="color:var(--muted)">Exchange Database</small></div></div><div class="links"><a href="/">前台</a><button id="logout" style="display:none">登出</button></div></nav><main class="admin"><section id="loginBox" class="card" style="max-width:460px;margin:60px auto"><h1>后台登录</h1><p class="lead">管理申请、审核价值、记录地方联系、建立初步交易，并生成 80/20 与 100% KCOINs 配置。</p><form id="loginForm"><div class="field"><label>Username</label><input name="username" value="wenscenter"></div><div class="field"><label>Password</label><input name="password" type="password"></div><button class="gold">登录</button><div id="loginResult" style="margin-top:14px"></div></form></section><section id="adminBox" style="display:none"><div class="toprow"><h1>KOG 互助交换后台</h1><button class="green" onclick="loadAll()">刷新</button></div><div id="stats" class="grid"></div><div class="card" style="margin-top:22px"><h3>申请清单</h3><div class="formgrid"><select id="statusFilter"><option value="">全部状态</option><option value="submitted">待审核</option><option value="local_review">地方初审</option><option value="approved">已通过</option><option value="matching">媒合中</option><option value="completed">已完成</option><option value="compliance_review">合规审查</option></select><input id="q" placeholder="搜索申请编号、名称、标题"><button onclick="loadApps()">搜索</button></div><div id="apps" style="margin-top:18px"></div></div></section></main><div id="modal" class="modal"><div class="modalbox"><div class="toprow"><h2 id="mt">申请处理</h2><button onclick="closeM()">关闭</button></div><div id="mb"></div></div></div><script>function $(s){return document.querySelector(s)}function money(v,c){return Number(v||0).toLocaleString()+" "+(c||"K.NTD")}async function api(p,o={}){let r=await fetch(p,{headers:{'Content-Type':'application/json'},...o});let j=await r.json();if(!r.ok||j.ok===false)throw Error(j.error||'API Error');return j}async function me(){try{let j=await api('/api/auth/me');show(!!j.user)}catch(e){show(false)}}function show(on){$('#loginBox').style.display=on?'none':'block';$('#adminBox').style.display=on?'block':'none';$('#logout').style.display=on?'inline-block':'none';if(on)loadAll()}$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();try{let d=Object.fromEntries(new FormData(e.target).entries());await api('/api/auth/login',{method:'POST',body:JSON.stringify(d)});show(true)}catch(err){$('#loginResult').innerHTML='<div class="danger">'+err.message+'</div>'}});$('#logout').onclick=async()=>{await api('/api/auth/logout',{method:'POST',body:'{}'});location.reload()};async function loadAll(){let s=await api('/api/stats');$('#stats').innerHTML='<div class="card"><h3>总申请</h3><div class="big-num">'+s.total+'</div></div><div class="card"><h3>待审核</h3><div class="big-num">'+s.pending+'</div></div><div class="card"><h3>地方80%</h3><div class="big-num">'+money(s.local_sum)+'</div></div><div class="card"><h3>KCOINs</h3><div class="big-num">'+money(s.kcoin_sum,'KCOINs')+'</div></div>';await loadApps()}async function loadApps(){let p=new URLSearchParams();if($('#statusFilter').value)p.set('status',$('#statusFilter').value);if($('#q').value)p.set('q',$('#q').value);let j=await api('/api/applications?'+p);$('#apps').innerHTML=j.items.map(a=>'<div class="card" style="margin:12px 0"><div class="toprow"><div><b>'+a.contribution_title+'</b><br><span class="pill">'+a.code+' · '+a.display_name+' · '+a.status+'</span></div><div>'+money(a.confirmed_value||a.proposed_value,a.currency)+'</div><button class="gold" onclick="openA('+a.id+')">处理</button></div></div>').join('')||'<div class="notice">暂无申请</div>'}async function openA(id){let j=await api('/api/applications/'+id),a=j.application;$('#mt').textContent=a.code+'｜'+a.contribution_title;$('#mb').innerHTML='<div class="grid2"><div class="card"><h3>申请人</h3><p>'+a.display_name+'<br>'+((a.organization_name)||'')+'<br>'+((a.email)||'')+' '+((a.phone)||'')+'</p></div><div class="card"><h3>分配</h3><p>地方：'+money(a.local_share_value,a.currency)+'<br>总部：'+money(a.hq_share_value,a.currency)+'<br>KCOINs：'+money(a.kcoin_supply_value,'KCOINs')+'</p></div></div><div class="card" style="margin-top:14px"><h3>资源说明</h3><p>'+esc(a.contribution_description||'')+'</p><p style="color:var(--muted)">希望交换：'+esc(a.requested_exchange||'')+'</p></div>'+(a.financial_flag?'<div class="danger" style="margin-top:14px">金融/证券/投资合约风险，必须合规审查。</div>':'')+'<div class="grid2"><form class="card" onsubmit="review(event,'+a.id+')"><h3>审核</h3><div class="field"><label>状态</label><select name="status"><option value="local_review">地方初审</option><option value="approved">通过</option><option value="matching">媒合中</option><option value="completed">完成</option><option value="needs_more_info">需补件</option><option value="rejected">拒绝</option><option value="compliance_review">合规审查</option></select></div><div class="field"><label>确认价值</label><input name="confirmed_value" type="number" step="0.01" value="'+(a.confirmed_value||a.proposed_value)+'"></div><div class="field"><label>地方共识说明</label><textarea name="local_consensus_note">'+esc(a.local_consensus_note||'')+'</textarea></div><button class="gold">更新审核</button></form><form class="card" onsubmit="contact(event,'+a.id+')"><h3>地方联系</h3><div class="field"><label>方式</label><input name="contact_method" value="phone"></div><div class="field"><label>摘要</label><textarea name="contact_summary" required></textarea></div><div class="field"><label>下一步</label><input name="next_step"></div><button class="green">新增联系记录</button></form></div><form class="card" style="margin-top:14px" onsubmit="trade(event,'+a.id+')"><h3>建立初步交易</h3><div class="field"><label>标题</label><input name="trade_title" value="'+esc(a.contribution_title)+'"></div><div class="field"><label>共识价值</label><input name="agreed_value" type="number" step="0.01" value="'+(a.confirmed_value||a.proposed_value)+'"></div><div class="field"><label>条款</label><textarea name="trade_terms" required></textarea></div><button class="gold">建立交易与分配记录</button></form><div id="mr" style="margin-top:14px"></div>';$('#modal').classList.add('open')}function closeM(){$('#modal').classList.remove('open')}async function review(e,id){e.preventDefault();try{await api('/api/applications/'+id+'/review',{method:'PATCH',body:JSON.stringify(Object.fromEntries(new FormData(e.target).entries()))});$('#mr').innerHTML='<div class="success">审核已更新</div>';loadAll()}catch(err){$('#mr').innerHTML='<div class="danger">'+err.message+'</div>'}}async function contact(e,id){e.preventDefault();try{await api('/api/applications/'+id+'/contact',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target).entries()))});$('#mr').innerHTML='<div class="success">联系记录已新增</div>'}catch(err){$('#mr').innerHTML='<div class="danger">'+err.message+'</div>'}}async function trade(e,id){e.preventDefault();try{let j=await api('/api/applications/'+id+'/trade',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target).entries()))});$('#mr').innerHTML='<div class="success">交易已建立：'+j.trade_code+'</div>';loadAll()}catch(err){$('#mr').innerHTML='<div class="danger">'+err.message+'</div>'}}function esc(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}me()</script></body></html>'''

class App(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args))
    def json(self, obj, status=200, extra=None):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.send_header('X-Content-Type-Options','nosniff')
        if extra:
            for k,v in extra.items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(data)
    def read_json(self):
        n=int(self.headers.get('Content-Length','0') or 0)
        return json.loads(self.rfile.read(n).decode() or '{}')
    def user(self):
        jar=cookies.SimpleCookie(self.headers.get('Cookie',''))
        if SESSION_COOKIE not in jar: return None
        sid=jar[SESSION_COOKIE].value
        with db() as c:
            return rowdict(c.execute('SELECT u.id,u.username,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.id=? AND s.expires_at>?',(sid,now())).fetchone())
    def require(self):
        u=self.user()
        if not u: self.json({'ok':False,'error':'Authentication required'},401)
        return u
    def page(self, content):
        data=content.encode()
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        p=urlparse(self.path); path=p.path
        if path=='/api/health': return self.json({'ok':True,'status':'healthy','service':'kog-wallet'})
        if path=='/api/auth/me': return self.json({'ok':True,'user':self.user()})
        if path=='/api/stats':
            if not self.require(): return
            with db() as c:
                total=c.execute('SELECT COUNT(*) c FROM applications').fetchone()['c']; pending=c.execute("SELECT COUNT(*) c FROM applications WHERE status IN ('submitted','local_review','compliance_review')").fetchone()['c']; sums=c.execute("SELECT COALESCE(SUM(local_share_value),0) l,COALESCE(SUM(hq_share_value),0) h,COALESCE(SUM(kcoin_supply_value),0) k FROM distributions").fetchone()
            return self.json({'ok':True,'total':total,'pending':pending,'local_sum':sums['l'],'hq_sum':sums['h'],'kcoin_sum':sums['k']})
        if path=='/api/applications':
            if not self.require(): return
            q=parse_qs(p.query); wh=[]; args=[]
            if q.get('status',[''])[0]: wh.append('a.status=?'); args.append(q['status'][0])
            if q.get('q',[''])[0]: wh.append('(a.code LIKE ? OR a.contribution_title LIKE ? OR p.display_name LIKE ?)'); term='%'+q['q'][0]+'%'; args += [term,term,term]
            sql='''SELECT a.*,p.display_name,p.organization_name,p.email,p.phone FROM applications a JOIN participants p ON p.id=a.participant_id'''
            if wh: sql+=' WHERE '+ ' AND '.join(wh)
            sql+=' ORDER BY a.created_at DESC LIMIT 200'
            with db() as c: items=rows(c.execute(sql,args).fetchall())
            return self.json({'ok':True,'items':items})
        if path.startswith('/api/applications/'):
            if not self.require(): return
            app_id=int(path.split('/')[3])
            with db() as c:
                app=rowdict(c.execute('''SELECT a.*,p.display_name,p.organization_name,p.email,p.phone,p.participant_type FROM applications a JOIN participants p ON p.id=a.participant_id WHERE a.id=?''',(app_id,)).fetchone())
                contacts=rows(c.execute('SELECT * FROM contact_logs WHERE application_id=? ORDER BY created_at DESC',(app_id,)).fetchall())
                trades=rows(c.execute('SELECT * FROM trades WHERE application_id=? ORDER BY created_at DESC',(app_id,)).fetchall())
            if not app: return self.json({'ok':False,'error':'Not found'},404)
            return self.json({'ok':True,'application':app,'contacts':contacts,'trades':trades})
        if path=='/admin.html': return self.page(ADMIN_HTML)
        return self.page(INDEX_HTML)
    def do_POST(self):
        p=urlparse(self.path).path
        try: body=self.read_json()
        except Exception: return self.json({'ok':False,'error':'Invalid JSON'},400)
        if p=='/api/auth/login':
            with db() as c:
                u=c.execute('SELECT * FROM users WHERE username=?',(body.get('username',''),)).fetchone()
                if not u or not verify_password(body.get('password',''),u['password_salt'],u['password_hash']): return self.json({'ok':False,'error':'Invalid credentials'},401)
                sid=secrets.token_urlsafe(32); exp=(datetime.utcnow()+timedelta(hours=SESSION_HOURS)).replace(microsecond=0).isoformat()+'Z'
                c.execute('INSERT INTO sessions(id,user_id,expires_at,created_at) VALUES(?,?,?,?)',(sid,u['id'],exp,now()))
            ck=cookies.SimpleCookie(); ck[SESSION_COOKIE]=sid; ck[SESSION_COOKIE]['httponly']=True; ck[SESSION_COOKIE]['samesite']='Lax'; ck[SESSION_COOKIE]['path']='/'
            return self.json({'ok':True,'user':{'username':u['username'],'role':u['role']}},200,{'Set-Cookie':ck.output(header='',sep='')})
        if p=='/api/auth/logout':
            ck=cookies.SimpleCookie(); ck[SESSION_COOKIE]=''; ck[SESSION_COOKIE]['max-age']='0'; ck[SESSION_COOKIE]['path']='/'
            return self.json({'ok':True},200,{'Set-Cookie':ck.output(header='',sep='')})
        if p=='/api/applications':
            required=['participant_type','display_name','contribution_type','contribution_title','contribution_description']
            if any(not body.get(x) for x in required): return self.json({'ok':False,'error':'Missing required fields'},400)
            val=float(body.get('proposed_value') or 0); d=calc(val); status='compliance_review' if body.get('financial_flag') else 'submitted'; comp='needs_review' if body.get('financial_flag') else 'standard'; code=make_code('KOG')
            with db() as c:
                cur=c.execute('''INSERT INTO participants(participant_type,display_name,organization_name,country,city,region,email,phone,line_id,wechat_id,whatsapp_id,telegram_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(body.get('participant_type'),body.get('display_name'),body.get('organization_name'),body.get('country'),body.get('city'),body.get('region'),body.get('email'),body.get('phone'),body.get('line_id'),body.get('wechat_id'),body.get('whatsapp_id'),body.get('telegram_id'),now()))
                pid=cur.lastrowid
                cur=c.execute('''INSERT INTO applications(code,participant_id,contribution_type,contribution_title,contribution_description,requested_exchange,proposed_value,currency,accepts_80_20,financial_flag,status,compliance_status,local_share_value,hq_share_value,kcoin_supply_value,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(code,pid,body.get('contribution_type'),body.get('contribution_title'),body.get('contribution_description'),body.get('requested_exchange'),val,body.get('currency','K.NTD'),1,int(bool(body.get('financial_flag'))),status,comp,d['local_share_value'],d['hq_share_value'],d['kcoin_supply_value'],now(),now()))
                app_id=cur.lastrowid
                c.execute('INSERT INTO audit_logs(actor,action,entity,entity_id,detail,created_at) VALUES(?,?,?,?,?,?)',('public','CREATE_APPLICATION','applications',app_id,code,now()))
            return self.json({'ok':True,'code':code,'status':status,'distribution':d},201)
        if p.endswith('/contact'):
            u=self.require();
            if not u: return
            app_id=int(p.split('/')[3])
            with db() as c: c.execute('INSERT INTO contact_logs(application_id,contact_method,contact_summary,next_step,contacted_by,created_at) VALUES(?,?,?,?,?,?)',(app_id,body.get('contact_method'),body.get('contact_summary'),body.get('next_step'),u['username'],now()))
            return self.json({'ok':True})
        if p.endswith('/trade'):
            u=self.require();
            if not u: return
            app_id=int(p.split('/')[3]); val=float(body.get('agreed_value') or 0); d=calc(val); code=make_code('TRD')
            with db() as c:
                app=c.execute('SELECT currency FROM applications WHERE id=?',(app_id,)).fetchone(); currency=app['currency'] if app else 'K.NTD'
                cur=c.execute('INSERT INTO trades(application_id,trade_code,trade_title,trade_terms,agreed_value,currency,status,created_at) VALUES(?,?,?,?,?,?,?,?)',(app_id,code,body.get('trade_title'),body.get('trade_terms'),val,currency,'draft',now()))
                tid=cur.lastrowid
                c.execute('INSERT INTO distributions(application_id,trade_id,total_value,local_share_value,hq_share_value,kcoin_supply_value,created_at) VALUES(?,?,?,?,?,?,?)',(app_id,tid,val,d['local_share_value'],d['hq_share_value'],d['kcoin_supply_value'],now()))
                c.execute('UPDATE applications SET status=?,confirmed_value=?,local_share_value=?,hq_share_value=?,kcoin_supply_value=?,updated_at=? WHERE id=?',('trade_in_progress',val,d['local_share_value'],d['hq_share_value'],d['kcoin_supply_value'],now(),app_id))
            return self.json({'ok':True,'trade_code':code,'distribution':d})
        return self.json({'ok':False,'error':'Not found'},404)
    def do_PATCH(self):
        p=urlparse(self.path).path
        if not p.endswith('/review'): return self.json({'ok':False,'error':'Not found'},404)
        u=self.require();
        if not u: return
        body=self.read_json(); app_id=int(p.split('/')[3]); val=float(body.get('confirmed_value') or 0); d=calc(val)
        with db() as c:
            c.execute('''UPDATE applications SET status=?,confirmed_value=?,local_consensus_note=?,compliance_status=?,local_share_value=?,hq_share_value=?,kcoin_supply_value=?,updated_at=? WHERE id=?''',(body.get('status','local_review'),val,body.get('local_consensus_note'),body.get('compliance_status','standard'),d['local_share_value'],d['hq_share_value'],d['kcoin_supply_value'],now(),app_id))
            if body.get('status') in ('approved','completed','matching'):
                c.execute('INSERT INTO distributions(application_id,total_value,local_share_value,hq_share_value,kcoin_supply_value,created_at) VALUES(?,?,?,?,?,?)',(app_id,val,d['local_share_value'],d['hq_share_value'],d['kcoin_supply_value'],now()))
            c.execute('INSERT INTO audit_logs(actor,action,entity,entity_id,detail,created_at) VALUES(?,?,?,?,?,?)',(u['username'],'REVIEW_APPLICATION','applications',app_id,body.get('status',''),now()))
        return self.json({'ok':True,'distribution':d})

def main():
    init_db()
    port=int(os.environ.get('PORT') or os.environ.get('KOG_PORT') or '8080')
    host=os.environ.get('KOG_HOST','0.0.0.0')
    print(f'KOG Wallet Web App running on http://{host}:{port}')
    ThreadingHTTPServer((host,port),App).serve_forever()

if __name__=='__main__':
    main()
