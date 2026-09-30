# 架构说明：模块化 + 统一接口

## 一句话

**每个功能都是一个独立模块；模块之间不互相调用，只通过核心层（`@/core`）提供的统一接口通信。**
所以加一个功能 = 加一个文件夹，删一个功能 = 删配置里的一行，修一个功能 = 只改那一个文件夹。
不同的模块组合保存为"配置档"（profile），例如个人版 `personal` 和完整版 `full`。

```
┌──────────────────────────── 前端（uni-app：App / H5 / 小程序）────────────────────────────┐
│                                                                                          │
│  article   video   like   comment   auth   profile   legal     （modules/ 下的独立模块）   │
│         │                 │               │               │               │          │   │
│         └─────────────────┴───────┬───────┴───────────────┴───────────────┴──────────┘   │
│                                   ▼  只允许 import '@/core'                               │
│   core/  api.call(module, action, params)   session   events   registry   requireLogin   │
│                                   │                                                      │
│                    transport：mock（本地假数据） | cloud（uniCloud 云对象）                   │
└───────────────────────────────────┼──────────────────────────────────────────────────────┘
                                    ▼  统一返回格式 { code, message, data }
┌──────────────────────────── 云端（uniCloud 云对象）──────────────────────────────────────┐
│   mod-article   mod-video   mod-like   mod-comment        （uni-id-co：官方登录）          │
│         └───────────┴───────────┴───────────┘                                            │
│                         ▼  createModule(definition)                                      │
│   common/app-core：返回格式、错误码、参数校验、鉴权、存储抽象、内容审核                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 五条统一接口

| # | 接口 | 定义在哪里 | 作用 |
|---|---|---|---|
| 1 | **模块清单** `module.json` | 每个模块目录 | 声明页面、tab、依赖、插槽扩展、提供的能力、版本号 |
| 2 | **API 契约** `{ code, message, data }` + 错误码 | `app-core/contract.json`（前后端共用这一份） | 所有后端接口返回同一种格式 |
| 3 | **调用方式** `api.call(module, action, params)` | `src/core/api.js` | 所有前端模块用同一种方式调后端 |
| 4 | **扩展插槽** `content-footer`（props：`targetType`、`targetId`）、`profile-header`（无 props） | `src/config/slots.json` | 一个模块把组件"插"进另一个模块的页面，而不需要对方 import 它 |
| 5 | **能力 / 会话 / 事件** `registry.capability()`、`session`、`events` | `src/core/` | 跨模块协作：比如"去登录页"、"当前是谁"、"登录状态变了" |

### module.json 字段

```jsonc
{
  "id": "comment",                 // 必须与目录名一致
  "name": "评论",
  "version": "1.0.0",              // 模块自己的版本号，升级时改这里
  "contractVersion": 1,            // 遵守的接口契约版本；与 app-core 不一致时构建失败
  "dependsOn": ["auth"],           // 依赖的模块；依赖没启用时构建失败
  "pages": [                       // 页面（可选），会自动写进 pages.json
    { "path": "pages/list", "title": "文章", "tab": { "text": "文章", "order": 10 } }
  ],
  "extensions": [                  // 往插槽里插组件（可选）
    { "slot": "content-footer", "component": "components/CommentPanel.vue", "order": 20 }
  ],
  "provides": { "loginPage": "pages/login" },   // 向其他模块提供的能力（可选）
  "api": { "cloudObject": "mod-comment" },     // 对应的云对象
  "mock": "mock.js",               // 本地假数据（可选），不允许 import '@/core'
  "setup": "setup.js"              // App 启动时执行的钩子（可选）
}
```

### 后端：一个 action 的完整写法

```js
// uniCloud-aliyun/cloudfunctions/mod-xxx/service.js
module.exports = {
  name: 'xxx',
  version: '1.0.0',
  actions: {
    list: {
      auth: 'public',                                   // public | user | admin
      params: { page: { type: 'integer', min: 1, default: 1 } },
      async handler({ page }, { store, uid, deviceId, moderation, now, AppError, CODES }) {
        // 只写业务逻辑；返回值自动包装为 { code: 0, message: 'ok', data }
        // 抛 new AppError(CODES.NOT_FOUND) 会自动变成 { code: 40401, message: '内容不存在' }
      },
    },
  },
}
```

`createModule` 统一负责：鉴权 → 参数校验 → 调用 handler → 包装返回值 → 捕获异常（不向客户端泄露内部错误）。
每个模块还自动获得一个 `meta` 接口，返回模块名、版本号和 action 列表，可用于健康检查。

## 自动装配（`npm run gen`）

`scripts/gen-modules.mjs` 在每次 `dev` / `build` 前自动运行：

1. 读取 `src/config/modules.config.json`，按配置档（默认 `profile` 字段，或环境变量 `APP_PROFILE`）确定启用哪些模块。
2. **校验**：id、版本号格式、契约版本、依赖、页面文件是否存在、插槽是否存在、能力是否重复提供，
   以及 **模块之间是否有直接 import**（有就报错）。
3. **生成**：`src/pages.json`、`src/generated/registry.js`、`src/generated/setups.js`、`src/generated/slots/*.vue`。

为什么是"构建前生成"而不是"运行时动态加载"：uni-app 的 `pages.json` 必须是静态文件，
小程序也不支持 `<component :is>`。构建前生成既保留了插拔能力，又兼容三端。

生成的文件会提交进 Git（这样用 HBuilderX 直接打开也能运行），测试会检查它们是否最新。

## 常见操作

### 切换配置档
`APP_PROFILE=full npm run dev:h5` 临时切换；或把 `modules.config.json` 的 `profile` 改成 `full`。
测试会检查每个配置档的模块组合是否都合法。

### 卸载一个模块
在 `src/config/modules.config.json` 对应配置档的 `enabled` 里删掉它，重新运行 `npm run dev:h5`。
页面、tab、插槽里的组件会自动消失。如果有别的模块依赖它，构建会失败并告诉你是谁依赖它。

### 升级一个模块
只改 `src/modules/<id>/` 和 `uniCloud-aliyun/cloudfunctions/mod-<id>/`，并把两边的 `version` 加一。
只要它仍然遵守统一接口（参数、返回字段不变），其他模块完全不受影响。
云端只需要重新上传这一个云对象。

### 新增一个模块（例：收藏 `favorite`）
1. 新建 `src/modules/favorite/module.json`，比如往 `content-footer` 插槽插一个 `FavoriteButton.vue`。
2. 组件里用 `api.call('favorite', 'toggle', { targetType, targetId })`。
3. 新建 `uniCloud-aliyun/cloudfunctions/mod-favorite/`（复制 `mod-like` 改一改）和数据库 schema。
4. 在 `modules.config.json` 需要它的配置档的 `enabled` 里加上 `"favorite"`。

文章、视频页面一行都不用改：它们只认识 `content-footer` 插槽，不认识具体模块。

### 实例：账号卡片是怎么出现在"我的"页面上的
"我的"页面属于 `profile` 模块，它只在顶部放了一个 `profile-header` 插槽，并不知道 `auth` 模块存在。
`auth` 在自己的 `module.json` 里声明 `extensions: [{ slot: 'profile-header', component: 'components/AccountCard.vue' }]`。
所以个人版（不启用 auth）的"我的"页面上就没有登录卡片，完整版上就有，`profile` 模块一行都不用改。

### 新增一种内容（例：播客 `podcast`）
新建 `podcast` 模块，详情页里放 `<ContentFooterSlot target-type="podcast" :target-id="id" />`，
点赞和评论就自动可用。`like`、`comment` 模块一行都不用改，因为它们只认 `targetType + targetId`。

### 更换底层服务
| 想换的东西 | 只改这里 |
|---|---|
| 数据库（阿里云 → 腾讯云 / 自建） | `app-core/store.js` 新增一个适配器 |
| 内容审核（关键词 → 专业服务） | `app-core/moderation.js` |
| 登录方式（短信 → 微信登录） | `src/modules/auth/service.js` + `app-core/auth.js` |
| 视频托管（B 站 → 云点播） | `src/modules/video/format.js` 和播放页 |

## 依赖规则（由构建脚本强制执行）

- 模块只能 import：`@/core`、`@/core/*`、`@/generated/*`、自己目录内的文件。
- 模块**不能** import 其他模块（`@/modules/<别的模块>` 或 `../../别的模块`）。
- `mock.js` 不能 import `@/core`（它被核心层加载，反向引用会形成循环依赖）。
- 云端业务模块只通过 `ctx`（`store`、`moderation`、`uid` 等）访问外部资源，不直接调用 `uniCloud.database()`。
  这也是它们能在 Node 里用内存数据库做单元测试的原因。
