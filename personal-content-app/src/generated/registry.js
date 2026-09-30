// 自动生成：已启用模块清单。请勿手改，运行 npm run gen 重新生成。
import * as mock_article from '@/modules/article/mock.js'
import * as mock_video from '@/modules/video/mock.js'
import * as mock_like from '@/modules/like/mock.js'

export const PROFILE = "personal"

export const MODULES = [
  {
    "id": "legal",
    "name": "法律文本",
    "version": "1.1.0",
    "contractVersion": 1,
    "description": "隐私政策、服务协议。应用商店上架必需。",
    "dependsOn": [],
    "pages": [
      {
        "path": "pages/privacy",
        "title": "隐私政策"
      },
      {
        "path": "pages/terms",
        "title": "服务协议"
      }
    ],
    "provides": {
      "privacyPage": "pages/privacy",
      "termsPage": "pages/terms"
    }
  },
  {
    "id": "profile",
    "name": "我的",
    "version": "1.0.0",
    "contractVersion": 1,
    "description": "“我的”页面：法律文本入口、版本信息。顶部提供 profile-header 插槽，账号等模块可以插入自己的卡片。",
    "dependsOn": [
      "legal"
    ],
    "pages": [
      {
        "path": "pages/index",
        "title": "我的",
        "tab": {
          "text": "我的",
          "order": 90
        }
      }
    ]
  },
  {
    "id": "article",
    "name": "文章",
    "version": "1.0.0",
    "contractVersion": 1,
    "description": "文章列表与详情。详情页底部提供 content-footer 插槽，互动功能由其他模块插入。",
    "dependsOn": [],
    "pages": [
      {
        "path": "pages/list",
        "title": "文章",
        "tab": {
          "text": "文章",
          "order": 10
        },
        "style": {
          "enablePullDownRefresh": true
        }
      },
      {
        "path": "pages/detail",
        "title": ""
      }
    ],
    "api": {
      "cloudObject": "mod-article"
    },
    "mock": "mock.js"
  },
  {
    "id": "video",
    "name": "视频",
    "version": "1.0.0",
    "contractVersion": 1,
    "description": "视频列表与详情。视频文件托管在 B 站，这里只展示元数据并调用 B 站播放器。",
    "dependsOn": [],
    "pages": [
      {
        "path": "pages/list",
        "title": "视频",
        "tab": {
          "text": "视频",
          "order": 20
        },
        "style": {
          "enablePullDownRefresh": true
        }
      },
      {
        "path": "pages/detail",
        "title": ""
      },
      {
        "path": "pages/player",
        "title": "播放"
      }
    ],
    "api": {
      "cloudObject": "mod-video"
    },
    "mock": "mock.js"
  },
  {
    "id": "like",
    "name": "点赞",
    "version": "1.0.0",
    "contractVersion": 1,
    "description": "匿名点赞（按设备去重）。通过 content-footer 插槽挂到任何内容上。",
    "dependsOn": [],
    "pages": [],
    "extensions": [
      {
        "slot": "content-footer",
        "component": "components/LikeButton.vue",
        "order": 10
      }
    ],
    "api": {
      "cloudObject": "mod-like"
    },
    "mock": "mock.js"
  }
]

export const CAPABILITIES = {
  "privacyPage": "/modules/legal/pages/privacy",
  "termsPage": "/modules/legal/pages/terms"
}

export const MOCKS = {
  'article': mock_article,
  'video': mock_video,
  'like': mock_like,
}
