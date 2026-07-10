# KOG Wallet Web App

KOG Wallet Web App 是 KOG 互助交换系统的线上入口，包含：

- 前台一页式申请网站
- 买方、卖方、商家、教会、非盈利机构、时间银行成员申请入口
- 可交换货物、服务、时间、空间、现金、权益登记
- 地方团队联系与审核流程
- 地方 80% / KOG 总部 20% 分配记录
- 100% KCOINs 供应记录
- 后台管理页面与 SQLite 资料库

## 启动方式

```bash
python3 server.py
```

Railway / Render / VPS 使用同一个启动命令。

## 主要网址

- `/`：前台申请入口
- `/admin.html`：后台管理
- `/api/health`：健康检查

## 管理员帐号

默认 Demo：

```text
username: wenscenter
password: KOG.ONE.2026July
```

正式上线前必须在平台环境变量中更换密码：

```bash
KOG_ADMIN_USERNAME=wenscenter
KOG_ADMIN_PASSWORD=<replace-with-new-private-password>
```

## 合规提醒

KCOINs / K.NTD 在本系统中作为生态权益、优惠券、互助交换与记录单位，不应表述为固定投资收益或保证现金兑付。涉及证券、金融商品、投资合约、收益权等申请，系统会进入合规审查，不走普通互助交换流程。
