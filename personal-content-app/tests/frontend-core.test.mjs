import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createApi, createMockTransport, normalize } from '../src/core/api.js'
import { CODES, ApiError } from '../src/core/contract.js'
import { core, loadService, invoke, fakeAuth } from './helpers.mjs'
import * as articleMock from '../src/modules/article/mock.js'
import * as videoMock from '../src/modules/video/mock.js'

test('前后端使用同一份错误码', () => {
  assert.deepEqual(CODES, core.CODES)
})

test('normalize：成功返回 data，失败抛 ApiError', () => {
  assert.equal(normalize({ code: 0, message: 'ok', data: 42 }), 42)
  assert.throws(() => normalize({ code: CODES.NOT_FOUND, message: '没了' }), (e) => e instanceof ApiError && e.code === CODES.NOT_FOUND)
  assert.throws(() => normalize(undefined), (e) => e.code === CODES.INTERNAL)
})

test('api.call：未启用的模块返回 MODULE_UNAVAILABLE', async () => {
  const api = createApi({ transport: async () => ({ code: 0, data: 1 }), isEnabled: (m) => m === 'article' })
  assert.equal(await api.call('article', 'list'), 1)
  await assert.rejects(api.call('comment', 'list'), (e) => e.code === CODES.MODULE_UNAVAILABLE)
})

test('mock 传输层把抛出的业务错误转换成统一格式', async () => {
  const transport = createMockTransport({
    demo: {
      ok: async (p, ctx) => ({ p, ctx }),
      bad: async () => { throw Object.assign(new Error('x'), { code: CODES.FORBIDDEN }) },
    },
  }, () => ({ deviceId: 'd' }))
  const api = createApi({ transport })
  assert.deepEqual(await api.call('demo', 'ok', { a: 1 }), { p: { a: 1 }, ctx: { deviceId: 'd' } })
  await assert.rejects(api.call('demo', 'bad'), (e) => e.code === CODES.FORBIDDEN)
  await assert.rejects(api.call('demo', 'nope'), (e) => e.code === CODES.UNKNOWN_ACTION)
})

test('mock 与云端返回相同的字段（切换 cloud 模式时页面无需改动）', async () => {
  for (const [name, mock, seedId] of [['article', articleMock, 'a1'], ['video', videoMock, 'v1']]) {
    const fromMockList = await mock.list({ page: 1, pageSize: 10 })
    const fromMockGet = await mock.get({ id: seedId })
    const seed = [{ ...fromMockGet, status: 'published', content: '', bvid: 'BV1xxxxxxxxx', description: '' }]
    const cloud = core.createModule(loadService(name), {
      store: core.createMemoryStore({ [`app-${name}`]: seed }),
      auth: fakeAuth,
    })
    const fromCloudList = (await invoke(cloud, 'list', {})).data
    const fromCloudGet = (await invoke(cloud, 'get', { id: seedId })).data
    assert.deepEqual(Object.keys(fromMockList).sort(), Object.keys(fromCloudList).sort(), `${name}.list 外层字段`)
    assert.deepEqual(Object.keys(fromMockList.items[0]).sort(), Object.keys(fromCloudList.items[0]).sort(), `${name}.list 条目字段`)
    assert.deepEqual(Object.keys(fromMockGet).sort(), Object.keys(fromCloudGet).sort(), `${name}.get 字段`)
  }
})
