import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'
import {
  loadManifests,
  validateModules,
  findIllegalImports,
  buildPagesJson,
  buildRegistryJs,
  buildSlotComponent,
  resolveProfile,
} from '../scripts/gen-modules.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const SRC = path.join(ROOT, 'src')
const readJson = (f) => JSON.parse(fs.readFileSync(path.join(SRC, f), 'utf8'))
const manifests = loadManifests()
const modulesConfig = readJson('config/modules.config.json')
// 大部分测试针对"完整版"，因为它包含全部模块
const enabled = resolveProfile(modulesConfig, 'full').enabled
const personal = resolveProfile(modulesConfig, 'personal').enabled
const { slots } = readJson('config/slots.json')
const appConfig = readJson('config/app.config.json')
const fileExists = (rel) => fs.existsSync(path.join(SRC, rel))
const check = (en, extra = {}) =>
  validateModules({ manifests, enabled: en, slots, contractVersion: 1, fileExists, ...extra })

test('每个配置档的模块组合都符合接口规范', () => {
  for (const name of Object.keys(modulesConfig.profiles)) {
    assert.deepEqual(check(resolveProfile(modulesConfig, name).enabled), [], `配置档 ${name}`)
  }
})

test('个人版不包含登录和评论（不收集手机号），但保留点赞和“我的”页面', () => {
  assert.ok(!personal.includes('auth'))
  assert.ok(!personal.includes('comment'))
  for (const id of ['article', 'video', 'like', 'profile', 'legal']) assert.ok(personal.includes(id), id)
  const json = buildPagesJson({ manifests, enabled: personal, appConfig })
  assert.ok(!json.pages.some((p) => p.path.startsWith('modules/auth/')))
  assert.deepEqual(json.tabBar.list.map((t) => t.text), ['文章', '视频', '我的'])
})

test('未知的配置档名称会报错', () => {
  assert.throws(() => resolveProfile(modulesConfig, 'nope'), /未知的配置档/)
  assert.equal(resolveProfile(modulesConfig).name, modulesConfig.profile)
})

test('没有任何扩展的插槽也能生成合法组件', () => {
  const vue = buildSlotComponent('profile-header', slots['profile-header'], [])
  assert.match(vue, /当前没有模块扩展这个插槽/)
  assert.match(vue, /defineProps\(\{\}\)/)
})

test('卸载 comment：校验通过，插槽里不再有评论组件', () => {
  const en = enabled.filter((m) => m !== 'comment')
  assert.deepEqual(check(en), [])
  const ext = manifests.like.extensions.map((e) => ({ ...e, module: 'like', name: 'LikeLikeButton' }))
  const vue = buildSlotComponent('content-footer', slots['content-footer'], ext)
  assert.match(vue, /LikeLikeButton/)
  assert.doesNotMatch(vue, /Comment/)
})

test('卸载 auth 但保留 comment：报出依赖缺失', () => {
  const errors = check(enabled.filter((m) => m !== 'auth'))
  assert.ok(errors.some((e) => e.includes('comment') && e.includes('auth')), errors.join('\n'))
})

test('启用不存在的模块、契约版本不匹配都会报错', () => {
  assert.ok(check([...enabled, 'ghost']).some((e) => e.includes('ghost')))
  assert.ok(check(enabled, { contractVersion: 2 }).some((e) => e.includes('contractVersion')))
})

test('禁止模块之间直接 import', () => {
  const errs = findIllegalImports({
    id: 'like',
    mockFile: 'mock.js',
    files: {
      'components/A.vue': "import X from '@/modules/comment/components/CommentPanel.vue'",
      'components/B.vue': "import { api } from '@/core'",
      'pages/C.vue': "import y from '../../video/format.js'",
      'mock.js': "import { api } from '@/core'",
    },
  })
  assert.equal(errs.length, 3, errs.join('\n'))
})

test('pages.json：第一个 tab 是首页，tab 按 order 排序', () => {
  const json = buildPagesJson({ manifests, enabled, appConfig })
  assert.equal(json.pages[0].path, 'modules/article/pages/list')
  assert.deepEqual(json.tabBar.list.map((t) => t.text), ['文章', '视频', '我的'])
  const only = buildPagesJson({ manifests, enabled: ['article'], appConfig })
  assert.equal(only.tabBar, undefined, '少于 2 个 tab 时不生成 tabBar')
})

test('cloud 模式下不把 mock 数据打包进 App', () => {
  const js = buildRegistryJs({ manifests, enabled, withMocks: false })
  assert.doesNotMatch(js, /^import /m)
})

test('仓库里提交的生成文件是最新的（改了 module.json 忘记 npm run gen 会失败）', () => {
  const before = {}
  const files = [
    'pages.json',
    'generated/registry.js',
    'generated/setups.js',
    'generated/slots/ContentFooterSlot.vue',
    'generated/slots/ProfileHeaderSlot.vue',
  ]
  for (const f of files) before[f] = fs.readFileSync(path.join(SRC, f), 'utf8')
  const env = { ...process.env, VITE_API_MODE: 'mock' }
  delete env.APP_PROFILE
  execFileSync('node', ['scripts/gen-modules.mjs'], { cwd: ROOT, env })
  for (const f of files) assert.equal(fs.readFileSync(path.join(SRC, f), 'utf8'), before[f], `${f} 已过期`)
})
