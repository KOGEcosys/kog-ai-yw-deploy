// index.js
const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

// ===== 配置 =====
const API_BASE = process.env.YIWUGO_API_BASE || 'https://opentest.yiwugo.com';
const AUTH_URL = process.env.YIWUGO_AUTH_URL || `${API_BASE}/oauth/token`;
const CLIENT_ID = process.env.YIWUGO_CLIENT_ID;
const CLIENT_SECRET = process.env.YIWUGO_CLIENT_SECRET;

// ===== Token 缓存 =====
let cachedToken = null;
let tokenExpiresAt = 0;

// 拿新的 token
async function fetchNewToken() {
  if (!CLIENT_ID || !CLIENT_SECRET)
    throw new Error("缺少 YIWUGO_CLIENT_ID 或 YIWUGO_CLIENT_SECRET");

  const authStr = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");

  const res = await axios.post(AUTH_URL, null, {
    params: {
      grant_type: "client_credentials",
      client_id: CLIENT_ID
    },
    headers: {
      Authorization: `Basic ${authStr}`,
    },
    timeout: 8000,
  });

  const data = res.data;
  if (!data.access_token) {
    console.log("token response:", data);
    throw new Error("无法取得 access_token");
  }

  const expiresIn = data.expires_in || 3600;
  cachedToken = data.access_token;
  tokenExpiresAt = Date.now() + (expiresIn - 300) * 1000;

  return cachedToken;
}

// 用缓存 token
async function getAccessToken() {
  if (cachedToken && Date.now() < tokenExpiresAt)
    return cachedToken;

  return fetchNewToken();
}

// 健康检查
app.get("/", (req, res) => {
  res.json({ ok: true, msg: "YiwuGo Proxy running" });
});

// 搜索接口
app.get("/search", async (req, res) => {
  try {
    const q = req.query.q || "";
    const token = await getAccessToken();

    const r = await axios.get(`${API_BASE}/open/cn_product/list`, {
      params: {
        access_token: token,
        q,
        page: req.query.page || 1,
        pageSize: req.query.pageSize || 60
      }
    });

    res.json(r.data);
  } catch (err) {
    res.status(500).json({
      error: err.message,
      detail: err.response?.data || null
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("YiwuGo Proxy running on " + PORT));
