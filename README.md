# KOG YiwuGo Proxy

Node.js + Express 后端代理  
支持自动获取 token + 自动刷新 token  
部署在 Railway 使用固定出口 IP。

## Endpoints
- GET /search?q=玩具
- GET /

## Railway 环境变量

YIWUGO_API_BASE=https://opentest.yiwugo.com  
YIWUGO_AUTH_URL=https://opentest.yiwugo.com/oauth/token  
YIWUGO_CLIENT_ID=你的clientId  
YIWUGO_CLIENT_SECRET=你的clientSecret
