// index.js
const express = require("express");
const axios = require("axios");
const app = express();

// === YiwuGo API 基础设置 ===
const CLIENT_ID = process.env.YIWUGO_CLIENT_ID;
const CLIENT_SECRET = process.env.YIWUGO_CLIENT_SECRET;
const REFERER = process.env.YIWUGO_REFERER || "https://vidaintl.hezon.cn";
const BASE_URL = process.env.YIWUGO_BASE_URL || "https://open.yiwugo.com";

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.warn("⚠ Missing YIWUGO_CLIENT_ID or YIWUGO_CLIENT_SECRET env vars");
}

// 简单内存缓存（生产环境后可以改 Redis）
let accessToken = null;
let tokenExpires = 0;

// ----------- Token 管理：自动获取 + 自动刷新 ------------
async function getToken() {
  if (accessToken && Date.now() < tokenExpires) {
    return accessToken;
  }

  const url = `${BASE_URL}/oauth/token?grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}`;
  const resp = await axios.post(url);

  accessToken = resp.data.access_token;
  tokenExpires = Date.now() + (resp.data.expires_in - 60) * 1000;

  console.log("🔄 Token refreshed");
  return accessToken;
}

// ----------- 通用 GET 请求函数（减少重复） -----------
async function yiwugoGet(path, params = {}) {
  const token = await getToken();
  const url = `${BASE_URL}${path}`;

  const resp = await axios.get(url, {
    headers: { Referer: REFERER },
    params: { access_token: token, ...params },
  });

  return resp.data;
}

// ------------------ API 路由 ------------------

// 商品列表（支持关键词搜索）
app.get("/api/products", async (req, res) => {
  try {
    const q = req.query.q || "";
    const data = await yiwugoGet("/open/cn_product/list", { q });
    res.json(data);
  } catch (err) {
    console.error("❌ /api/products error:", err);
    res.status(500).json({ error: err.message });
  }
});

// 商品详情
app.get("/api/product/:id", async (req, res) => {
  try {
    const data = await yiwugoGet("/open/cn_product/detail", {
      id: req.params.id,
    });
    res.json(data);
  } catch (err) {
    console.error("❌ /api/product/:id error:", err);
    res.status(500).json({ error: err.message });
  }
});

// SKU 列表
app.get("/api/product/:id/sku", async (req, res) => {
  try {
    const data = await yiwugoGet("/open/cn_product/skuList", {
      id: req.params.id,
    });
    res.json(data);
  } catch (err) {
    console.error("❌ /api/product/:id/sku error:", err);
    res.status(500).json({ error: err.message });
  }
});

// 分类列表
app.get("/api/categories", async (req, res) => {
  try {
    const data = await yiwugoGet("/open/cn_category/list");
    res.json(data);
  } catch (err) {
    console.error("❌ /api/categories error:", err);
    res.status(500).json({ error: err.message });
  }
});

// 推荐商品
app.get("/api/recommend", async (req, res) => {
  try {
    const data = await yiwugoGet("/open/cn_product/recommend");
    res.json(data);
  } catch (err) {
    console.error("❌ /api/recommend error:", err);
    res.status(500).json({ error: err.message });
  }
});

// ----------- 服务器运行 -----------
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`🚀 YiwuGo Proxy v2 running on port ${PORT}`);
});

