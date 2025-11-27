// index.js
const express = require("express");
const axios = require("axios");
const app = express();

// === YiwuGo 新版 API 基础设定 ===
const CLIENT_ID = process.env.YIWUGO_CLIENT_ID;
const CLIENT_SECRET = process.env.YIWUGO_CLIENT_SECRET;
const REFERER = process.env.YIWUGO_REFERER || "https://vidaintl.hezon.cn";

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.warn("⚠️ Missing YIWUGO_CLIENT_ID or YIWUGO_CLIENT_SECRET env vars");
}

// 简单内存缓存（生产环境你以后可以换成 Redis / DB）
const cache = new Map();
const CACHE_TTL_MS = 60 * 1000; // 60 秒缓存

let accessToken = null;
let tokenExpires = 0;

// ------------ Token 管理：自动获取 + 自动刷新 ------------
async function getToken() {
  // 还有有效 token 就直接用
  if (accessToken && Date.now() < tokenExpires) {
    return accessToken;
  }

  if (!CLIENT_ID || !CLIENT_SECRET) {
    throw new Error("YIWUGO_CLIENT_ID / SECRET not set");
  }

  const url = `https://open.yiwugo.com/oauth/token?grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}`;

  const resp = await axios.post(url);
  accessToken = resp.data.access_token;
  tokenExpires = Date.now() + (resp.data.expires_in - 60) * 1000;

  console.log("🔑 Token refreshed");
  return accessToken;
}

// ------------ 缓存 Helper ------------
function getCache(key) {
  const item = cache.get(key);
  if (!item) return null;
  if (Date.now() > item.expires) {
    cache.delete(key);
    return null;
  }
  return item.value;
}

function setCache(key, value, ttlMs = CACHE_TTL_MS) {
  cache.set(key, {
    value,
    expires: Date.now() + ttlMs,
  });
}

// ------------ 统一调用 YiwuGo Open API ------------
async function callYiwuGo(path, params = {}) {
  const token = await getToken();

  const url = new URL(`https://open.yiwugo.com${path}`);
  url.searchParams.set("access_token", token);

  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      url.searchParams.set(k, v);
    }
  });

  const cacheKey = url.toString();
  const cached = getCache(cacheKey);
  if (cached) return cached;

  const resp = await axios.get(url.toString(), {
    headers: {
      Referer: REFERER, // ✅ 官方要求的 Referer
      "User-Agent": "Mozilla/5.0",
    },
    timeout: 15000,
  });

  setCache(cacheKey, resp.data);
  return resp.data;
}

// ------------ 健康检查 ------------
app.get("/", (req, res) => {
  res.json({
    ok: true,
    service: "KOG Mall Gateway",
    msg: "YiwuGo NEW API Proxy running with token + referer",
  });
});
// ================================
//  YiwuGo 新版 API → 商品列表
//  GET /api/products?q=bag
// ================================

app.get("/api/products", async (req, res) => {
  try {
    const { q } = req.query;

    if (!q) {
      return res.status(400).json({ ok: false, error: "Missing q parameter" });
    }

    // 获取 Token（自动缓存）
    const token = await getToken();

    const url = `${BASE}/open/cn_product/list?access_token=${token}&q=${encodeURIComponent(q)}`;

    const result = await axios.get(url, {
      headers: {
        referer: REFERER,
        "User-Agent": "Mozilla/5.0",
      }
    });

    return res.json({ ok: true, data: result.data });

  } catch (err) {
    console.error("❌ /api/products error:", err.message);
    return res.status(500).json({ ok: false, error: err.message });
  }
});

// ------------ 商品列表：/api/products ------------
// 对应官方示例：/open/cn_product/list?access_token=xxx&q=玩具
app.get("/api/products", async (req, res) => {
  try {
    const { q = "", page = 1, pageSize = 20 } = req.query;

    const data = await callYiwuGo("/open/cn_product/list", {
      q,
      page,
      size: pageSize // ⚠️ 如果文档用 pageSize / page_size，请改成相应字段名
    });

    res.json({
      ok: true,
      keyword: q,
      page: Number(page),
      pageSize: Number(pageSize),
      raw: data // 保留原始结果，前端可自己映射字段
    });
  } catch (err) {
    console.error("❌ /api/products error:", err.response?.data || err.message);
    res.status(500).json({
      ok: false,
      error: err.response?.data || err.message,
    });
  }
});

// ------------ 商品详情：/api/products/:id ------------
app.get("/api/products/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const data = await callYiwuGo("/open/cn_product/detail", {
      id
      // 若文档是 goodsId / productId，请改这里的 key
    });

    res.json({
      ok: true,
      id,
      raw: data,
    });
  } catch (err) {
    console.error("❌ /api/products/:id error:", err.response?.data || err.message);
    res.status(500).json({
      ok: false,
      error: err.response?.data || err.message,
    });
  }
});

// ------------ SKU / 价格 / 库存：/api/products/:id/skus ------------
app.get("/api/products/:id/skus", async (req, res) => {
  try {
    const { id } = req.params;

    const data = await callYiwuGo("/open/cn_product/sku/list", {
      productId: id
    });

    res.json({
      ok: true,
      id,
      raw: data,
    });
  } catch (err) {
    console.error("❌ /api/products/:id/skus error:", err.response?.data || err.message);
    res.status(500).json({
      ok: false,
      error: err.response?.data || err.message,
    });
  }
});

// ------------ 分类列表：/api/categories ------------
app.get("/api/categories", async (req, res) => {
  try {
    const data = await callYiwuGo("/open/cn_product/class/list", {});
    res.json({
      ok: true,
      raw: data,
    });
  } catch (err) {
    console.error("❌ /api/categories error:", err.response?.data || err.message);
    res.status(500).json({
      ok: false,
      error: err.response?.data || err.message,
    });
  }
});

// ------------ 推荐商品：/api/recommend ------------
app.get("/api/recommend", async (req, res) => {
  try {
    const { q = "玩具" } = req.query;

    const data = await callYiwuGo("/open/cn_product/list", {
      q,
      page: 1,
      size: 10,
    });

    res.json({
      ok: true,
      keyword: q,
      raw: data,
    });
  } catch (err) {
    console.error("❌ /api/recommend error:", err.response?.data || err.message);
    res.status(500).json({
      ok: false,
      error: err.response?.data || err.message,
    });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log("🚀 KOG Mall Gateway running on PORT:", PORT);
});

