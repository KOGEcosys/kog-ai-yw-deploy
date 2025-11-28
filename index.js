// ===============================
// KOG GLOBAL MALL — Backend v3
// YiwuGo 新版 API  + Token 自动更新
// ===============================

require("dotenv").config();
const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();

// ============= CORS 允许前端访问 ============
app.use(cors());
app.use(express.json());

// ============= YiwuGo 正式 API Base ============
const API_BASE = "https://open.yiwugo.com";

// ============= Referer（你提供的正式值） ============
const REFERER = "https://www.vidaintl.hezon.cn";

// ============= 你的 YiwuGo API 认证信息 ============
const CLIENT_ID = process.env.YIWUGO_CLIENT_ID;
const CLIENT_SECRET = process.env.YIWUGO_CLIENT_SECRET;

let ACCESS_TOKEN = "";
let TOKEN_EXPIRE_TIME = 0; // Unix 时间戳

// ==================================================
// 🔥 获取 Token（YiwuGo 新版要求）
// ==================================================
async function refreshToken() {
    try {
        const url = `${API_BASE}/oauth/token`;
        const params = {
            grant_type: "client_credentials",
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        };

        const res = await axios.post(url, null, { params });
        ACCESS_TOKEN = res.data.access_token;
        TOKEN_EXPIRE_TIME = Date.now() + (res.data.expires_in - 60) * 1000;

        console.log("✅ YiwuGo token refreshed:", ACCESS_TOKEN);
        return ACCESS_TOKEN;
    } catch (err) {
        console.error("❌ Token refresh failed:", err?.response?.data || err);
        return null;
    }
}

// ==================================================
// 🔥 Token 自动管理：过期就刷新
// ==================================================
async function getValidToken() {
    if (!ACCESS_TOKEN || Date.now() > TOKEN_EXPIRE_TIME) {
        console.log("🔄 Token expired → refreshing...");
        await refreshToken();
    }
    return ACCESS_TOKEN;
}

// ==================================================
// 🔥 商品列表 API（新版 YiwuGo）
// open/cn_product/list?q=玩具&page=1
// ==================================================
app.get("/api/products", async (req, res) => {
    try {
        const q = req.query.q || "";
        const page = req.query.page || 1;

        const token = await getValidToken();
        if (!token) return res.status(500).json({ ok: false, error: "Token unavailable" });

        const url = `${API_BASE}/open/cn_product/list`;

        const response = await axios.get(url, {
            params: {
                access_token: token,
                q,
                page
            },
            headers: {
                "User-Agent": "Mozilla/5.0",
                "Referer": REFERER
            }
        });

        res.json({
            ok: true,
            q,
            page,
            items: response.data.data || []
        });

    } catch (err) {
        console.error("❌ Product API Error:", err?.response?.data || err);
        res.status(500).json({
            ok: false,
            error: err?.response?.data || err.toString()
        });
    }
});

// ==================================================
// 🔥 图片代理（YiwuGo 图片需要 Referer，否则 403）
// ==================================================
app.get("/api/img", async (req, res) => {
    try {
        const imgUrl = req.query.url;
        if (!imgUrl) return res.status(400).send("Missing url");

        const result = await axios.get(imgUrl, {
            responseType: "arraybuffer",
            headers: { "Referer": REFERER }
        });

        res.set("Content-Type", result.headers["content-type"]);
        res.send(result.data);

    } catch (err) {
        console.error("❌ Image Proxy Failed:", err?.response?.status);
        res.status(500).send("Image fetch failed");
    }
});

// ==================================================
// 根路径测试
// ==================================================
app.get("/", (req, res) => {
    res.json({ ok: true, msg: "KOG Mall Backend v3 running" });
});

// ==================================================
// 启动后台 Server
// ==================================================
const PORT = process.env.PORT || 8080;

app.listen(PORT, async () => {
    console.log("🚀 KOG Mall Backend v3 running on", PORT);
    await refreshToken();
});
