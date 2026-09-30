// 统一的 API 客户端。所有模块都用同一种方式调用后端：
//
//   const data = await api.call('article', 'list', { page: 1 })
//
// - 成功：直接返回 data
// - 失败：抛出 ApiError（带 code 和中文提示）
//
// "传输层"（transport）可以替换：mock（本地假数据）或 cloud（uniCloud 云对象）。
// 页面和组件完全不知道自己连的是哪一种，这就是可以随时切换、随时替换的原因。
import { ApiError, CODES } from './contract.js'

export function normalize(envelope) {
  if (!envelope || typeof envelope.code !== 'number') {
    throw new ApiError(CODES.INTERNAL, '返回格式不符合接口契约')
  }
  if (envelope.code !== CODES.OK) throw new ApiError(envelope.code, envelope.message, envelope.data)
  return envelope.data
}

// cloud 传输层：模块 article → 云对象 mod-article（名字由 module.json 的 api.cloudObject 决定）
export function createCloudTransport(resolveCloudObject) {
  const cache = new Map()
  return async (module, action, params) => {
    const name = resolveCloudObject(module)
    if (!cache.has(name)) cache.set(name, uniCloud.importObject(name, { customUI: true }))
    const obj = cache.get(name)
    if (typeof obj[action] !== 'function') throw new ApiError(CODES.UNKNOWN_ACTION)
    try {
      return await obj[action](params)
    } catch (e) {
      // 网络错误、云函数超时等非业务错误
      console.error(`[api] ${module}.${action}`, e)
      throw new ApiError(CODES.INTERNAL, '网络异常，请稍后重试')
    }
  }
}

// mock 传输层：直接调用各模块 mock.js 里的函数，模拟出与云端完全相同的返回格式
export function createMockTransport(mocks, getContext = () => ({})) {
  return async (module, action, params) => {
    const handler = mocks[module] && mocks[module][action]
    if (!handler) return { code: CODES.UNKNOWN_ACTION, message: `mock 未实现 ${module}.${action}`, data: null }
    try {
      const data = await handler(params || {}, getContext())
      return { code: CODES.OK, message: 'ok', data: data === undefined ? null : data }
    } catch (e) {
      return { code: e.code || CODES.INTERNAL, message: e.message, data: null }
    }
  }
}

export function createApi({ transport, isEnabled = () => true }) {
  return {
    async call(module, action, params = {}) {
      if (!isEnabled(module)) throw new ApiError(CODES.MODULE_UNAVAILABLE)
      return normalize(await transport(module, action, params))
    },
  }
}
