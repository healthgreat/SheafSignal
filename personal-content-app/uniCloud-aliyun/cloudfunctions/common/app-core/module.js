'use strict'
// createModule：把一个业务模块的定义变成一个标准的 uniCloud 云对象。
//
// 每个业务模块只需要写"定义"，不用关心返回格式、校验、鉴权、异常处理：
//
//   module.exports = createModule({
//     name: 'like',
//     version: '1.0.0',
//     actions: {
//       toggle: {
//         auth: 'public',                 // public | user | admin
//         params: { targetId: { type: 'string', required: true } },
//         async handler(params, ctx) { ... return data }
//       }
//     }
//   })
//
// 所有 action 的返回值都会被统一包装成 { code, message, data }。
// 每个模块还会自动获得一个 meta action，用于健康检查和版本查询。

const { AppError, CODES, ok, fail, CONTRACT_VERSION } = require('./errors')
const { validate } = require('./validate')
const { createUniCloudStore } = require('./store')
const { createKeywordModeration } = require('./moderation')
const { createUniIdAuth } = require('./auth')

const AUTH_LEVELS = ['public', 'user', 'admin']

function defaultDeps() {
  let store
  return {
    // 懒加载：只有在云端运行时才存在全局 uniCloud
    get store() {
      if (!store) store = createUniCloudStore(uniCloud.database()) // eslint-disable-line no-undef
      return store
    },
    auth: createUniIdAuth(),
    moderation: createKeywordModeration(),
    now: () => Date.now(),
  }
}

function createModule(definition, overrides = {}) {
  const { name, version = '0.0.0', actions = {} } = definition
  if (!name) throw new Error('createModule: 缺少 name')
  if ('meta' in actions) throw new Error(`createModule(${name}): meta 是保留的 action 名`)
  for (const [actionName, action] of Object.entries(actions)) {
    if (actionName.startsWith('_')) throw new Error(`createModule(${name}): action 不能以 _ 开头`)
    if (!AUTH_LEVELS.includes(action.auth)) {
      throw new Error(`createModule(${name}.${actionName}): auth 必须是 ${AUTH_LEVELS.join('/')}`)
    }
    if (typeof action.handler !== 'function') throw new Error(`createModule(${name}.${actionName}): 缺少 handler`)
  }

  const base = defaultDeps()
  const deps = {
    get store() {
      return overrides.store || base.store
    },
    auth: overrides.auth || base.auth,
    moderation: overrides.moderation || base.moderation,
    now: overrides.now || base.now,
  }

  const cloudObject = {}

  for (const [actionName, action] of Object.entries(actions)) {
    cloudObject[actionName] = async function (rawParams) {
      try {
        const clientInfo = (this && this.getClientInfo && this.getClientInfo()) || {}
        const token = (this && this.getUniIdToken && this.getUniIdToken()) || ''

        let user = null
        if (action.auth !== 'public' || token) {
          user = await deps.auth.verify(token, clientInfo).catch((e) => {
            if (action.auth === 'public') return null
            throw e
          })
        }
        if (action.auth !== 'public' && !user) throw new AppError(CODES.UNAUTHORIZED)
        if (action.auth === 'admin' && !user.role.includes('admin')) throw new AppError(CODES.FORBIDDEN)

        const params = validate(rawParams, action.params)
        const ctx = {
          module: name,
          action: actionName,
          uid: user ? user.uid : null,
          role: user ? user.role : [],
          deviceId: clientInfo.deviceId || null,
          clientInfo,
          store: deps.store,
          moderation: deps.moderation,
          now: deps.now,
          AppError,
          CODES,
        }
        const data = await action.handler(params, ctx)
        return ok(data === undefined ? null : data)
      } catch (err) {
        if (err instanceof AppError) return fail(err.code, err.message, err.data)
        console.error(`[${name}.${actionName}]`, err)
        return fail(CODES.INTERNAL)
      }
    }
  }

  cloudObject.meta = async function () {
    return ok({
      module: name,
      version,
      contractVersion: CONTRACT_VERSION,
      actions: Object.fromEntries(Object.entries(actions).map(([k, a]) => [k, { auth: a.auth }])),
    })
  }

  return cloudObject
}

module.exports = { createModule }
