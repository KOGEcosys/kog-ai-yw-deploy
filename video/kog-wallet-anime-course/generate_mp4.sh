#!/usr/bin/env bash
set -euo pipefail

OUT="kog-wallet-anime-course-preview.mp4"
WORKDIR="frames"
FPS=24
WIDTH=1920
HEIGHT=1080

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to generate ${OUT}. Install ffmpeg, then run this script again." >&2
  exit 127
fi

rm -rf "${WORKDIR}"
mkdir -p "${WORKDIR}"

python3 - <<'PY'
from pathlib import Path
import math

out = Path('frames')
out.mkdir(exist_ok=True)
W, H, FPS = 1920, 1080, 24
scenes = [
    (8, 'KOG Wallet 全球國度錢包', '全球 AI 商業支付 · 商家聯盟 · AI OPC 一人公司', 'world'),
    (10, '商家痛點', '客戶少 · 廣告貴 · 會員難經營', 'merchant'),
    (10, 'KOG Wallet 定位', '不是銀行 · 不是投資平台 · 是全球商業生態工具', 'triangle'),
    (10, '下載 Telegram', '搜尋 KOGWallet_bot · Start · 選擇語言', 'phone'),
    (12, '完成註冊', '手機 · Email · Telegram · LINE · WeChat · QR Code', 'profile'),
    (12, 'QR Code 與優惠券', 'K.USD / K.NTD / K.RMB：合作商家折抵使用', 'coupon'),
    (12, '商家 Dashboard', '掃碼數 · 新會員 · 優惠券使用率 · 回訪率', 'dashboard'),
    (11, 'AI OPC 一人公司', 'AI SEO · GEO · Chatbot · CRM · Video · Agent', 'ai'),
    (10, 'Merchant Alliance', 'Restaurant · Coffee · Hotel · Clinic · School · Church · Law Firm · AI Company', 'alliance'),
    (5, '立即開始', '學習 30 集完整課程 · 註冊會員 · 申請商家 · 加入 AI OPC', 'end'),
]

def esc(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def anime_character(x, y, color, label):
    return f'''
    <g transform="translate({x},{y})">
      <circle cx="0" cy="-80" r="58" fill="#ffe4c9" stroke="#3b2b5f" stroke-width="8"/>
      <path d="M-58 -95 Q0 -165 58 -95 Q15 -125 -58 -95" fill="#26366f"/>
      <circle cx="-20" cy="-86" r="7" fill="#1c244d"/><circle cx="22" cy="-86" r="7" fill="#1c244d"/>
      <path d="M-18 -55 Q0 -42 20 -55" fill="none" stroke="#a65572" stroke-width="5" stroke-linecap="round"/>
      <path d="M-75 20 Q0 -35 75 20 L100 170 L-100 170 Z" fill="{color}" stroke="#3b2b5f" stroke-width="8"/>
      <text x="0" y="230" text-anchor="middle" font-size="38" fill="#ffffff" font-family="sans-serif" font-weight="700">{esc(label)}</text>
    </g>'''

def scene_art(kind, frame, total):
    t = frame / max(total-1, 1)
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2)
    nodes = ''
    for i in range(18):
        x = 160 + (i * 97) % 1600
        y = 170 + (i * 173) % 650
        r = 7 + 8 * ((i % 3) / 2) + pulse * 5
        nodes += f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="#ffd76a" opacity="0.85"/><line x1="960" y1="540" x2="{x}" y2="{y}" stroke="#59d7ff" stroke-width="3" opacity="0.25"/>'
    phone = '<rect x="760" y="230" width="400" height="600" rx="55" fill="#101a3d" stroke="#70d7ff" stroke-width="10"/><rect x="800" y="300" width="320" height="80" rx="18" fill="#233b7a"/><rect x="800" y="420" width="320" height="95" rx="18" fill="#2d5fb8"/><rect x="800" y="550" width="320" height="95" rx="18" fill="#d8a73f"/><text x="960" y="352" text-anchor="middle" font-size="34" fill="#fff" font-family="sans-serif">KOGWallet_bot</text><text x="960" y="480" text-anchor="middle" font-size="38" fill="#fff" font-family="sans-serif">START</text><text x="960" y="610" text-anchor="middle" font-size="34" fill="#1a224a" font-family="sans-serif">Language</text>'
    qr = ''.join(f'<rect x="{790+(i%9)*38}" y="{320+(i//9)*38}" width="24" height="24" fill="#101a3d"/>' for i in range(81) if (i*7+i//2)%4==0)
    dashboard = ''.join(f'<rect x="{240+(i%3)*500}" y="{250+(i//3)*210}" width="410" height="150" rx="25" fill="#17275a" stroke="#64d7ff" stroke-width="4"/><text x="{445+(i%3)*500}" y="{335+(i//3)*210}" text-anchor="middle" font-size="42" fill="#ffd76a" font-family="sans-serif">{["QR Scan","New Members","Coupons","CRM","AI Marketing","Ranking"][i]}</text>' for i in range(6))
    if kind in ('world','alliance','end'):
        return f'<g>{nodes}<circle cx="960" cy="540" r="150" fill="none" stroke="#ffd76a" stroke-width="8" opacity="0.9"/><text x="960" y="555" text-anchor="middle" font-size="46" fill="#fff" font-family="sans-serif" font-weight="800">KOG</text></g>'
    if kind == 'merchant':
        return anime_character(520, 690, '#d8a73f', 'Merchant') + anime_character(960, 700, '#3a7bd5', 'Member') + anime_character(1400, 690, '#7a5cff', 'AI OPC')
    if kind == 'triangle':
        return '<polygon points="960,230 520,760 1400,760" fill="none" stroke="#ffd76a" stroke-width="8"/>' + anime_character(960, 330, '#3a7bd5', 'Member') + anime_character(520, 810, '#d8a73f', 'Merchant') + anime_character(1400, 810, '#7a5cff', 'AI OPC')
    if kind in ('phone','profile'):
        return phone
    if kind == 'coupon':
        return f'<rect x="700" y="260" width="520" height="520" rx="35" fill="#ffffff"/>{qr}<text x="960" y="860" text-anchor="middle" font-size="50" fill="#ffd76a" font-family="sans-serif" font-weight="800">K.USD · K.NTD · K.RMB</text>'
    if kind == 'dashboard':
        return dashboard
    if kind == 'ai':
        return anime_character(960, 690, '#7a5cff', 'AI OPC') + nodes
    return nodes

frame_index = 0
for duration, title, subtitle, kind in scenes:
    frames = duration * FPS
    for f in range(frames):
        t = f / max(frames-1, 1)
        bg_shift = int(30 + 25 * math.sin((frame_index/FPS)*0.8))
        art = scene_art(kind, f, frames)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#050816"/><stop offset="0.55" stop-color="#0b1d4d"/><stop offset="1" stop-color="#2b155f"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <circle cx="{260+bg_shift}" cy="180" r="210" fill="#1a75ff" opacity="0.16"/>
  <circle cx="{1640-bg_shift}" cy="820" r="260" fill="#ffd76a" opacity="0.12"/>
  <g filter="url(#glow)">{art}</g>
  <rect x="0" y="0" width="1920" height="1080" fill="none" stroke="#ffd76a" stroke-width="16" opacity="0.45"/>
  <text x="960" y="120" text-anchor="middle" fill="#ffd76a" font-family="sans-serif" font-size="72" font-weight="900">{esc(title)}</text>
  <text x="960" y="205" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-size="42" font-weight="700">{esc(subtitle)}</text>
  <text x="960" y="1010" text-anchor="middle" fill="#ffffff" opacity="0.85" font-family="sans-serif" font-size="30">KOG Wallet is not a bank or investment platform · Coupons are merchant discounts only</text>
</svg>'''
        (out / f'frame_{frame_index:05d}.svg').write_text(svg, encoding='utf-8')
        frame_index += 1
PY

ffmpeg -y -framerate "${FPS}" -i "${WORKDIR}/frame_%05d.svg" \
  -vf "scale=${WIDTH}:${HEIGHT},format=yuv420p" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart "${OUT}"

echo "Generated ${OUT}"
