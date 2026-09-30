# 上线与上架清单（国内）

> ⚠️ 政策会调整，各应用商店的要求也不完全一样。每一步开始前，请以官方最新的审核指南为准。
> 这里的内容是技术开发者视角的整理，不构成法律意见。

## 阶段 0：决定开发者主体（第 1 周）

- [ ] **个人** 还是 **个体工商户 / 公司**？
  - 个人主体在部分安卓商店、微信小程序中，对"社区 / 评论"类功能有限制。
  - 很多独立开发者会注册个体工商户（注册免费），以它作为开发者主体。

## 阶段 1：资质办理（与开发同时进行，耗时最长，尽早开始）

- [ ] 购买域名（需要实名认证）
- [ ] 开通 uniCloud 服务空间（阿里云版）：https://unicloud.dcloud.net.cn
- [ ] **ICP 备案**：通过云服务商提交，通常 1–3 周
- [ ] **APP 备案**：ICP 备案通过后，在同一服务商处提交。需要 App 名称、包名、签名公钥 / MD5 等信息
- [ ] **软件著作权**：中国版权保护中心官网自行申请免费，大约 1–2 个月（部分商店要求提供）
- [ ] 短信服务：开通短信并申请短信签名和模板（uni-id 短信登录需要）

## 阶段 2：接入真实云端

1. 用 **HBuilderX** 打开 `personal-content-app` 目录，右键 `uniCloud-aliyun` → 关联服务空间。
2. 插件市场导入 **uni-id-pages**，它会带来 `uni-id-co` 和 `uni-id-common`。
   然后在 `uniCloud-aliyun/cloudfunctions/common/uni-id-config/config.json` 里配置 `tokenSecret` 和短信参数。
3. 右键 `common/app-core` → 上传公共模块；对每个 `mod-*` 云对象：右键 → 管理公共模块依赖（勾选 `app-core`、`uni-id-common`）→ 上传部署。
4. 右键 `database` → 上传所有数据库 schema 和索引。
5. `cp .env.example .env`，把其中的 `VITE_API_MODE=mock` 改成 `VITE_API_MODE=cloud`，重新运行。
6. 管理后台：插件市场导入 **uni-admin**（单独一个项目，关联同一个服务空间），
   用它发布文章 / 视频、审核评论（`mod-comment` 的 `pending` / `review` 接口），并给自己的账号设置 `admin` 角色。

## 阶段 3：合规自检（上架前）

- [ ] `src/modules/legal/pages/*.vue` 和 `src/androidPrivacy.json` 里的隐私政策、服务协议已替换为真实内容，
      `androidPrivacy.json` 中的链接指向真实可访问的网页
- [ ] 首次启动先弹出隐私政策，用户同意之前不采集任何信息（`androidPrivacy.json` 已配置）
- [ ] 只申请必要权限（`manifest.json` 已移除相机、读取手机状态等权限，新增权限前请确认确有需要）
- [ ] 评论：后台实名（手机号）、前台自愿（昵称）、先审后发 ✅ 已实现
- [ ] 内容审核：把 `app-core/moderation.js` 的关键词占位实现换成专业内容安全服务
- [ ] 提供账号注销和删除个人信息的途径（隐私政策第四条；需要在 auth 模块补充"注销账号"功能）
- [ ] 视频托管在 B 站，App 内只嵌入 B 站官方外链播放器，不自行存储和分发视频文件

## 阶段 4：打包与上架

- [ ] HBuilderX → 发行 → 原生 App - 云打包（生成 Android APK / AAB 和 iOS IPA）
- [ ] 先上架 1–2 个安卓商店（例如华为、小米），积累审核经验
- [ ] iOS：Apple 开发者账号（99 美元/年），中国区上架时需要填写 APP 备案号
- [ ] 每个商店都需要：App 图标、截图、简介、隐私政策网址、APP 备案号，
      部分商店还需要软著和开发者身份证明
