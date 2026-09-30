'use strict'
// 点赞模块：不需要登录，按设备去重。
// 它不关心被点赞的是什么——文章、视频、以后新增的任何内容类型，
// 只要传入 targetType + targetId 就能用。这就是"统一接口"让模块可复用的地方。
const COLLECTION = 'app-like'
const TARGET = {
  targetType: { type: 'string', required: true, pattern: '^[a-z][a-z0-9-]{1,30}$' },
}

module.exports = {
  name: 'like',
  version: '1.0.0',
  actions: {
    toggle: {
      auth: 'public',
      params: { ...TARGET, targetId: { type: 'string', required: true, max: 64 } },
      async handler({ targetType, targetId }, { store, deviceId, now, AppError, CODES }) {
        if (!deviceId) throw new AppError(CODES.INVALID_PARAMS, '无法识别设备')
        const col = store.collection(COLLECTION)
        const key = { target_type: targetType, target_id: targetId, device_id: deviceId }
        const removed = await col.remove(key)
        if (!removed) await col.insert({ ...key, create_date: now() })
        const count = await col.count({ target_type: targetType, target_id: targetId })
        return { liked: !removed, count }
      },
    },
    status: {
      auth: 'public',
      params: { ...TARGET, targetIds: { type: 'array', required: true, max: 50 } },
      async handler({ targetType, targetIds }, { store, deviceId }) {
        const col = store.collection(COLLECTION)
        const result = {}
        for (const id of targetIds) {
          const base = { target_type: targetType, target_id: String(id) }
          const [count, mine] = await Promise.all([
            col.count(base),
            deviceId ? col.count({ ...base, device_id: deviceId }) : 0,
          ])
          result[id] = { count, liked: mine > 0 }
        }
        return result
      },
    },
  },
}
