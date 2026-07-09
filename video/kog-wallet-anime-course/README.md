# KOG Wallet 全球操作视频课程：动漫类型 MP4 制作包

本目录提供一套可直接交给剪辑师、AI 视频工具或本地 `ffmpeg` 生成 MP4 的动漫风课程样片制作包。

> 说明：当前执行环境无法安装或调用 `ffmpeg`，因此仓库内提供的是可生成 MP4 的完整素材与脚本。只要在具备 `ffmpeg` 的环境执行 `./generate_mp4.sh`，即可输出 `kog-wallet-anime-course-preview.mp4`。

## 样片规格

- 文件名：`kog-wallet-anime-course-preview.mp4`
- 类型：动漫风课程预告片 / 课程片头样片
- 时长：约 90 秒
- 画幅：16:9，1920×1080
- 风格：日系未来都市动漫、蓝金科技 UI、全球商家联盟、AI 助手、手机钱包、QR Code
- 用途：YouTube 片头、说明会开场、AI OPC 培训开场、商家招商短片

## 内容结构

1. 全球城市夜景与 KOG Wallet 标题
2. 商家痛点：没客户、广告贵、会员少
3. KOG Wallet 定位：不是银行、不是投资平台
4. 三角色：会员、商家、AI OPC
5. Telegram Bot 下载与启动
6. QR Code 扫码、优惠券折抵、交易完成
7. 商家后台 Dashboard、AI CRM、AI Marketing
8. Merchant Alliance 商家联盟地图
9. 结尾行动：注册、申请商家、加入 AI OPC 培训

## 快速生成 MP4

```bash
cd video/kog-wallet-anime-course
./generate_mp4.sh
```

生成结果：

```text
video/kog-wallet-anime-course/kog-wallet-anime-course-preview.mp4
```

## 交给 AI 视频工具的主 Prompt

```text
Create a 90-second anime-style course preview for "KOG Wallet 全球国度钱包". Use a futuristic global city at night, blue and gold UI, anime characters representing merchants, members and AI OPC operators. Show Telegram bot onboarding, wallet registration, QR code scan, ecosystem coupons, merchant dashboard, AI CRM, AI Marketing and a global Merchant Alliance network. The tone is professional, trustworthy and educational. Include compliance visuals: KOG Wallet is not a bank, not an investment platform, and coupons are ecosystem merchant discounts only. No profit promises, no cash rain, no speculative trading imagery. 16:9, cinematic anime, clean subtitles, premium training course style.
```
