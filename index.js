const express = require("express");
const axios = require("axios");
const app = express();

const BASE = process.env.YIWUGO_API_BASE || "https://opentest.yiwugo.com";

app.get("/", (req, res) => {
  res.json({ ok: true, msg: "YiwuGo Proxy running" });
});

// 🔥 YiwuGo 搜索代理
// 调用示例：/api/search?q=bag&page=1
app.get("/api/search", async (req, res) => {
  try {
    const { q, page = 1 } = req.query;

    const url = `${BASE}/search/suggest.do?keywords=${encodeURIComponent(q)}&page=${page}`;

    const result = await axios.get(url, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Referer": BASE,
      }
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

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log("YiwuGo Proxy running on", PORT));
