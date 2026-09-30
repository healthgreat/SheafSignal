import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
export const core = require('../uniCloud-aliyun/cloudfunctions/common/app-core')
export const loadService = (name) => require(`../uniCloud-aliyun/cloudfunctions/mod-${name}/service.js`)

// 模拟一次云对象调用：带上设备号 / token，就像真实客户端一样
export function invoke(cloudObject, action, params, { deviceId = 'dev-1', token = '' } = {}) {
  const self = { getClientInfo: () => ({ deviceId }), getUniIdToken: () => token }
  return cloudObject[action].call(self, params)
}

// 测试用的鉴权：token 形如 "uid" 或 "uid:admin"
export const fakeAuth = {
  async verify(token) {
    if (!token) return null
    const [uid, role] = token.split(':')
    return { uid, role: role ? [role] : [] }
  },
}

export function clock(start = 1_000_000) {
  let t = start
  const now = () => t
  now.advance = (ms) => (t += ms)
  return now
}
