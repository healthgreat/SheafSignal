// 核心层对外只暴露这一个入口。模块只能 import '@/core'，不能 import 别的模块。
import { createApi, createCloudTransport, createMockTransport } from './api.js'
import { session } from './session.js'
import { getDeviceId } from './device.js'
import { MODULES, MOCKS, CAPABILITIES } from '../generated/registry.js'

export { CODES, ApiError, messageOf } from './contract.js'
export { events } from './events.js'
export { session }

export const API_MODE = import.meta.env.VITE_API_MODE === 'cloud' ? 'cloud' : 'mock'

const byId = Object.fromEntries(MODULES.map((m) => [m.id, m]))

export const registry = {
  modules: MODULES,
  isEnabled: (id) => id in byId,
  get: (id) => byId[id],
  capability: (name) => CAPABILITIES[name],
}

const transport =
  API_MODE === 'cloud'
    ? createCloudTransport((id) => byId[id]?.api?.cloudObject || `mod-${id}`)
    : createMockTransport(MOCKS, () => ({ deviceId: getDeviceId(), user: session.user }))

export const api = createApi({ transport, isEnabled: registry.isEnabled })

// 统一的错误提示
export function toastError(e) {
  uni.showToast({ title: e?.message || '出错了', icon: 'none' })
}

// 统一的日期格式化
export function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 需要登录的操作统一调这个：未登录则跳到"提供 loginPage 能力"的模块页面
export function requireLogin() {
  if (session.isLoggedIn()) return true
  const page = CAPABILITIES.loginPage
  if (page) uni.navigateTo({ url: page })
  else uni.showToast({ title: '登录功能未启用', icon: 'none' })
  return false
}
