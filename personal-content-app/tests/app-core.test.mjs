import { test } from 'node:test'
import assert from 'node:assert/strict'
import { core, invoke, fakeAuth } from './helpers.mjs'

const { createModule, CODES, AppError, createMemoryStore } = core

function demo(overrides = {}) {
  return createModule(
    {
      name: 'demo',
      version: '1.2.3',
      actions: {
        echo: { auth: 'public', params: { text: { type: 'string', required: true, max: 5 } }, handler: (p) => p },
        whoami: { auth: 'user', handler: (_, ctx) => ({ uid: ctx.uid, deviceId: ctx.deviceId }) },
        secret: { auth: 'admin', handler: () => 'ok' },
        boom: { auth: 'public', handler: () => { throw new Error('db password leaked') } },
        missing: { auth: 'public', handler: (_, { AppError, CODES }) => { throw new AppError(CODES.NOT_FOUND) } },
      },
    },
    { store: createMemoryStore(), auth: fakeAuth, ...overrides },
  )
}

test('成功时统一返回 { code: 0, message, data }', async () => {
  const res = await invoke(demo(), 'echo', { text: ' hi ' })
  assert.deepEqual(res, { code: CODES.OK, message: 'ok', data: { text: 'hi' } })
})

test('参数校验失败统一返回 INVALID_PARAMS', async () => {
  assert.equal((await invoke(demo(), 'echo', {})).code, CODES.INVALID_PARAMS)
  assert.equal((await invoke(demo(), 'echo', { text: 'toolong' })).code, CODES.INVALID_PARAMS)
  assert.equal((await invoke(demo(), 'echo', { text: 123 })).code, CODES.INVALID_PARAMS)
})

test('鉴权等级：public / user / admin', async () => {
  const m = demo()
  assert.equal((await invoke(m, 'whoami', {})).code, CODES.UNAUTHORIZED)
  assert.deepEqual((await invoke(m, 'whoami', {}, { token: 'u1', deviceId: 'd9' })).data, { uid: 'u1', deviceId: 'd9' })
  assert.equal((await invoke(m, 'secret', {}, { token: 'u1' })).code, CODES.FORBIDDEN)
  assert.equal((await invoke(m, 'secret', {}, { token: 'u1:admin' })).data, 'ok')
})

test('业务错误原样返回，未知异常不泄露内部信息', async () => {
  assert.equal((await invoke(demo(), 'missing', {})).code, CODES.NOT_FOUND)
  const origError = console.error
  console.error = () => {}
  const res = await invoke(demo(), 'boom', {})
  console.error = origError
  assert.equal(res.code, CODES.INTERNAL)
  assert.doesNotMatch(res.message, /password/)
})

test('每个模块自动获得 meta 接口', async () => {
  const res = await invoke(demo(), 'meta', {})
  assert.equal(res.data.module, 'demo')
  assert.equal(res.data.version, '1.2.3')
  assert.equal(res.data.actions.secret.auth, 'admin')
})

test('模块定义不合规时立即报错', () => {
  assert.throws(() => createModule({ name: 'x', actions: { a: { handler() {} } } }), /auth/)
  assert.throws(() => createModule({ name: 'x', actions: { _a: { auth: 'public', handler() {} } } }), /_/)
  assert.throws(() => createModule({ name: 'x', actions: { meta: { auth: 'public', handler() {} } } }), /保留/)
  assert.ok(new AppError(CODES.NOT_FOUND).message)
})

test('所有业务云对象都能被 createModule 正常装配', async () => {
  const { loadService } = await import('./helpers.mjs')
  for (const name of ['article', 'video', 'like', 'comment']) {
    const def = loadService(name)
    assert.equal(def.name, name)
    const obj = createModule(def, { store: createMemoryStore(), auth: fakeAuth })
    assert.equal((await invoke(obj, 'meta', {})).data.module, name)
  }
})
