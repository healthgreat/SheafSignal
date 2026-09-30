import { test } from 'node:test'
import assert from 'node:assert/strict'
import { core, loadService, invoke, fakeAuth, clock } from './helpers.mjs'

const { createModule, createMemoryStore, createKeywordModeration, CODES } = core

test('article：只返回已发布文章，列表不含正文，按时间倒序', async () => {
  const store = createMemoryStore({
    'app-article': [
      { _id: 'a', title: 'A', content: '<p>a</p>', status: 'published', publish_date: 1 },
      { _id: 'b', title: 'B', content: '<p>b</p>', status: 'published', publish_date: 2 },
      { _id: 'c', title: 'C', content: '<p>c</p>', status: 'draft', publish_date: 3 },
    ],
  })
  const m = createModule(loadService('article'), { store, auth: fakeAuth })
  const list = (await invoke(m, 'list', {})).data
  assert.equal(list.total, 2)
  assert.deepEqual(list.items.map((i) => i._id), ['b', 'a'])
  assert.equal(list.items[0].content, undefined)
  assert.equal((await invoke(m, 'get', { id: 'a' })).data.content, '<p>a</p>')
  assert.equal((await invoke(m, 'get', { id: 'c' })).code, CODES.NOT_FOUND)
})

test('like：按设备去重，重复点击为取消', async () => {
  const m = createModule(loadService('like'), { store: createMemoryStore(), auth: fakeAuth, now: clock() })
  const target = { targetType: 'article', targetId: 'a' }
  assert.deepEqual((await invoke(m, 'toggle', target, { deviceId: 'd1' })).data, { liked: true, count: 1 })
  assert.deepEqual((await invoke(m, 'toggle', target, { deviceId: 'd2' })).data, { liked: true, count: 2 })
  assert.deepEqual((await invoke(m, 'toggle', target, { deviceId: 'd1' })).data, { liked: false, count: 1 })
  const status = (await invoke(m, 'status', { targetType: 'article', targetIds: ['a', 'x'] }, { deviceId: 'd2' })).data
  assert.deepEqual(status, { a: { count: 1, liked: true }, x: { count: 0, liked: false } })
  // 同一个模块可用于任何内容类型（统一接口的意义）
  assert.equal((await invoke(m, 'toggle', { targetType: 'podcast', targetId: 'p1' })).code, CODES.OK)
  assert.equal((await invoke(m, 'toggle', { targetType: 'Bad Type!', targetId: 'p1' })).code, CODES.INVALID_PARAMS)
  assert.equal((await invoke(m, 'toggle', target, { deviceId: '' })).code, CODES.INVALID_PARAMS)
})

function commentModule(now = clock()) {
  const store = createMemoryStore()
  const m = createModule(loadService('comment'), {
    store,
    auth: fakeAuth,
    now,
    moderation: createKeywordModeration(['违禁词']),
  })
  return { m, store, now }
}

const T = { targetType: 'article', targetId: 'a' }

test('comment：必须登录才能评论（后台实名）', async () => {
  const { m } = commentModule()
  assert.equal((await invoke(m, 'create', { ...T, content: 'hi' })).code, CODES.UNAUTHORIZED)
})

test('comment：先审后发，待审评论只有作者本人可见', async () => {
  const { m } = commentModule()
  const created = await invoke(m, 'create', { ...T, content: '好文', nickname: '小明' }, { token: 'u1' })
  assert.equal(created.data.status, 'pending')

  const asOther = (await invoke(m, 'list', T, { token: 'u2' })).data
  assert.equal(asOther.total, 0)
  assert.equal(asOther.minePending.length, 0)

  const asAuthor = (await invoke(m, 'list', T, { token: 'u1' })).data
  assert.equal(asAuthor.minePending[0].content, '好文')
  assert.equal(asAuthor.minePending[0].user_id, undefined, '不向前端暴露 user_id')

  assert.equal((await invoke(m, 'review', { id: created.data.id, decision: 'approved' }, { token: 'u1' })).code, CODES.FORBIDDEN)
  await invoke(m, 'review', { id: created.data.id, decision: 'approved' }, { token: 'boss:admin' })

  const pub = (await invoke(m, 'list', T)).data
  assert.equal(pub.total, 1)
  assert.equal(pub.items[0].nickname, '小明')
})

test('comment：内容审核拦截、频率限制、昵称默认值', async () => {
  const { m, now } = commentModule()
  assert.equal((await invoke(m, 'create', { ...T, content: '含有违禁词' }, { token: 'u1' })).code, CODES.CONTENT_REJECTED)
  const ok = await invoke(m, 'create', { ...T, content: '第一条' }, { token: 'u1' })
  assert.equal(ok.code, CODES.OK)
  assert.equal((await invoke(m, 'create', { ...T, content: '第二条' }, { token: 'u1' })).code, CODES.RATE_LIMITED)
  now.advance(16_000)
  assert.equal((await invoke(m, 'create', { ...T, content: '第二条' }, { token: 'u1' })).code, CODES.OK)
  const mine = (await invoke(m, 'list', T, { token: 'u1' })).data.minePending
  assert.ok(mine.every((c) => c.nickname === '读者'))
})

test('comment：只能删除自己的评论，管理员可以删除任何评论', async () => {
  const { m } = commentModule()
  const { data } = await invoke(m, 'create', { ...T, content: 'x' }, { token: 'u1' })
  assert.equal((await invoke(m, 'remove', { id: data.id }, { token: 'u2' })).code, CODES.FORBIDDEN)
  assert.equal((await invoke(m, 'remove', { id: data.id }, { token: 'u1' })).code, CODES.OK)
  assert.equal((await invoke(m, 'remove', { id: data.id }, { token: 'boss:admin' })).code, CODES.NOT_FOUND)
})
