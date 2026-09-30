'use strict'
// 内容审核接口：check(text) → { pass: boolean, reason?: string }
//
// 这里的关键词过滤只是占位实现。正式上线前请换成专业的内容安全服务，
// 例如 DCloud 插件市场的 uni-sec-check（对接微信内容安全）、阿里云内容安全、腾讯云天御。
// 替换时只改这一个文件（或在 createModule 里注入新的 moderation），业务模块完全不用动。

const DEFAULT_BLOCKLIST = ['赌博', '代开发票', '加微信领取']

function createKeywordModeration(blocklist = DEFAULT_BLOCKLIST) {
  return {
    async check(text) {
      const hit = blocklist.find((word) => text.includes(word))
      return hit ? { pass: false, reason: `包含敏感词` } : { pass: true }
    },
  }
}

module.exports = { createKeywordModeration }
