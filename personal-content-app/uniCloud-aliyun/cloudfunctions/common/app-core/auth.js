'use strict'
// 鉴权接口：verify(token, clientInfo) → { uid, role: [] } | null
// 默认实现使用 uni-id-common（DCloud 官方用户体系）。
// 文档：https://doc.dcloud.net.cn/uniCloud/uni-id/summary.html

function createUniIdAuth() {
  return {
    async verify(token, clientInfo) {
      if (!token) return null
      let uniIdCommon
      try {
        uniIdCommon = require('uni-id-common')
      } catch (e) {
        throw new Error('未安装 uni-id-common：请在 HBuilderX 插件市场导入 uni-id-pages，并在本云函数中关联 uni-id-common 公共模块')
      }
      const res = await uniIdCommon.createInstance({ clientInfo }).checkToken(token)
      if (res.errCode) return null
      return { uid: res.uid, role: res.role || [] }
    },
  }
}

module.exports = { createUniIdAuth }
