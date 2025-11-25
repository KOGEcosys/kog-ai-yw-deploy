const express = require("express");
const axios = require("axios");
const app = express();

// YiwuGo API 基本网址（可在 Railway 变量中覆盖）
const BASE = process.env.YIWUGO_API_BASE || "https://opentest.yiwugo.com";

// 测试根路径
app.get("/", (req, res) => {
  res.json({ ok: true, msg: "YiwuGo Proxy Running" });
});


// 🔥 YiwuGo 搜索代理
// 调用示例：/api/search?q=bag&page=1
app.get("/api/search", async (req, res) => {
  try {
    const { q, page = 1 } = req.query;

    if (!q) {
      return res.status(400).json({
        ok: false,
        error: "Missing query parameter ?q="
      });
    }

    const url = `${BASE}/search/suggest.do?keywords=${encodeURIComponent(q)}&page=${page}`;

    const result = await axios.get(url, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Referer": BASE,
      },
      timeout: 10000 // 增加 timeout 防止 ECONNRESET
    });

    res.json({
      ok: true,
      keyword: q,
      page,
      data: result.data
    });

  } catch (err) {
    res.status(500).json({
      ok: false,
      error: err.toString()
    });
  }
});


// 🚀 Railway 必须绑定动态 PORT（不能写死 8080）
const PORT = process.env.PORT || 8080;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`YiwuGo Proxy running on port ${PORT}`);
});
