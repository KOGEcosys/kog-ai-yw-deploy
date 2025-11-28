/**
 * KOG YiwuGo Proxy v5 — New API Edition
 * 自动获取 token + 自动刷新 + 支持商品搜索
 * Author: Dr. David Lin + KOG Global Mall
 */

import express from "express";
import axios from "axios";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

// ================================
// 🔧 配置（你必须设置这四个）
// ================================
const YIWUGO_AUTH_URL = "https://open.yiwugo.com/oauth/token";
const YIWUGO_API_BASE = "https://open.yiwugo.com";  // 正式环境
const CLIENT_ID = process.env.YIWUGO_CLIENT_ID;
const CLIENT_SECRET = process.env.YIWUGO_CLIENT_SECRET;

let cachedToken = null;
let tokenExpireAt = 0;

// ================================
// 🔥 自动获取 Token（含自动刷新）
// ================================
async function getAccessToken() {
  const now = Date.now();

  // Token 有效 → 直接返回
  if (cachedToken && now < tokenExpireAt) {
    return cachedToken;
  }

  try {
    console.log("🔑 Fetching new YiwuGo token...");
    const response = await axios.post(
      `${YIWUGO_AUTH_URL}?grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}`
    );

    cachedToken = response.data.access_token;
    const expiresIn = response.data.expires_in || 7200;
    tokenExpireAt = now + expiresIn * 1000 - 60 * 1000; // 提前 60 秒刷新

    console.log("✅ Token refreshed:", cachedToken);

    return cachedToken;
  } catch (err) {
    console.error("❌ Failed to get access token:", err.response?.data || err);
    throw new Error("Failed to get access token");
  }
}

// ================================
// 🔍 商品搜索 API（新版）
// ================================
app.get("/api/search", async (req, res) => {
  const q = req.query.q || "";
  const page = req.query.page || 1;

  try {
    const token = await getAccessToken();

    const url = `${YIWUGO_API_BASE}/open/cn_product/list`;
    const params = {
      access_token: token,
      q,
      cpage: page,
      pageSize: 60
    };

    console.log("📡 Calling YiwuGo Search:", params);

    const response = await axios.get(url, { params });

    res.json({
      success: true,
      keyword: q,
      page,
      data: response.data
    });
  } catch (err) {
    console.error("❌ YiwuGo Search Error:", err.response?.data || err);

    res.status(500).json({
      success: false,
      error: err.response?.data || "YiwuGo API error"
    });
  }
});

// ================================
// 🔍 商品详情 API（新版）
// ================================
app.get("/api/detail", async (req, res) => {
  const id = req.query.id;
  if (!id) return res.status(400).json({ error: "Missing id" });

  try {
    const token = await getAccessToken();

    const url = `${YIWUGO_API_BASE}/open/cn_product/detail`;
    const params = {
      access_token: token,
      goodId: id
    };

    console.log("📡 Calling YiwuGo Detail:", params);

    const response = await axios.get(url, { params });

    res.json({
      success: true,
      id,
      data: response.data
    });
  } catch (err) {
    console.error("❌ YiwuGo Detail Error:", err.response?.data || err);

    res.status(500).json({
      success: false,
      error: err.response?.data || "YiwuGo API error"
    });
  }
});

// ================================
// 🖼 图片代理（避免 403）
// ================================
app.get("/api/img", async (req, res) => {
  const imgUrl = req.query.url;
  if (!imgUrl) return res.status(400).send("Missing url");

  try {
    const response = await axios.get(imgUrl, {
      responseType: "arraybuffer",
      headers: {
        Referer: "https://www.yiwugo.com" // 避免 403
      }
    });

    res.set("Content-Type", response.headers["content-type"]);
    res.send(response.data);
  } catch (err) {
    console.error("❌ Image Proxy Error:", err);
    res.status(500).send("Cannot fetch image");
  }
});

// ================================
// 🚀 Start Server
// ================================
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`🚀 YiwuGo Proxy v5 running on port ${PORT}`);
});
