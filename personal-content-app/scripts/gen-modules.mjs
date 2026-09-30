#!/usr/bin/env node
// 模块装配脚本：config/modules.config.json + 各模块 module.json → 自动生成的"胶水代码"
//
// 用哪个配置档：默认读 modules.config.json 的 "profile"，也可以临时指定：
//   APP_PROFILE=full npm run dev:h5
//
// 生成物（都在 src/ 下，不要手改，改了也会被覆盖）：
//   pages.json                    页面路由与底部 tab
//   generated/registry.js         已启用模块清单、mock、能力（capabilities）
//   generated/setups.js           各模块的启动钩子
//   generated/slots/*.vue         扩展插槽组件（静态 import，所以小程序端也能用）
//
// 为什么用"生成"而不是运行时动态加载？
//   uni-app 的 pages.json 必须是静态文件；小程序也不支持 <component :is> 动态组件。
//   把"装配"放到构建前完成，既保留了插拔式的模块化，又兼容 App / H5 / 小程序三端。

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const SRC = path.join(ROOT, 'src')
const CONTRACT = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'uniCloud-aliyun/cloudfunctions/common/app-core/contract.json'), 'utf8'),
)

const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'))
const toPascal = (s) => s.replace(/(^|-)([a-z])/g, (_, __, c) => c.toUpperCase())

// ---------- 读取 ----------

export function loadManifests(modulesDir = path.join(SRC, 'modules')) {
  const manifests = {}
  for (const dir of fs.readdirSync(modulesDir)) {
    const file = path.join(modulesDir, dir, 'module.json')
    if (fs.existsSync(file)) manifests[dir] = { ...readJson(file), __dir: dir }
  }
  return manifests
}

// ---------- 校验：模块必须遵守统一接口规范 ----------

export function validateModules({ manifests, enabled, slots, contractVersion, fileExists }) {
  const errors = []
  const seenPages = new Set()
  const seenCapabilities = new Map()

  for (const id of enabled) {
    const m = manifests[id]
    if (!m) {
      errors.push(`已启用的模块 "${id}" 不存在（src/modules/${id}/module.json）`)
      continue
    }
    const where = `模块 ${id}`
    if (m.id !== id) errors.push(`${where}: module.json 的 id "${m.id}" 必须与目录名一致`)
    if (!/^[a-z][a-z0-9-]*$/.test(id)) errors.push(`${where}: id 只能用小写字母、数字、连字符`)
    if (!/^\d+\.\d+\.\d+$/.test(m.version || '')) errors.push(`${where}: version 必须是 x.y.z 格式`)
    if (m.contractVersion !== contractVersion) {
      errors.push(`${where}: contractVersion=${m.contractVersion}，但当前接口契约版本是 ${contractVersion}`)
    }
    for (const dep of m.dependsOn || []) {
      if (!enabled.includes(dep)) errors.push(`${where}: 依赖模块 "${dep}"，但它没有启用`)
    }
    for (const page of m.pages || []) {
      const full = `modules/${id}/${page.path}`
      if (seenPages.has(full)) errors.push(`${where}: 页面 ${full} 重复声明`)
      seenPages.add(full)
      if (!fileExists(`${full}.vue`)) errors.push(`${where}: 页面文件 src/${full}.vue 不存在`)
    }
    for (const ext of m.extensions || []) {
      if (!slots[ext.slot]) errors.push(`${where}: 插槽 "${ext.slot}" 未在 config/slots.json 中定义`)
      if (!fileExists(`modules/${id}/${ext.component}`)) {
        errors.push(`${where}: 扩展组件 src/modules/${id}/${ext.component} 不存在`)
      }
    }
    for (const [cap, page] of Object.entries(m.provides || {})) {
      if (seenCapabilities.has(cap)) {
        errors.push(`${where}: 能力 "${cap}" 已由模块 ${seenCapabilities.get(cap)} 提供，不能重复提供`)
      }
      seenCapabilities.set(cap, id)
      if (!(m.pages || []).some((p) => p.path === page)) {
        errors.push(`${where}: provides.${cap} 指向的页面 "${page}" 没有在 pages 中声明`)
      }
    }
    if (m.mock && !fileExists(`modules/${id}/${m.mock}`)) errors.push(`${where}: mock 文件 ${m.mock} 不存在`)
    if (m.setup && !fileExists(`modules/${id}/${m.setup}`)) errors.push(`${where}: setup 文件 ${m.setup} 不存在`)
  }
  return errors
}

// ---------- 校验：模块之间禁止互相 import ----------
// 模块只能 import '@/core'、'@/generated' 和自己目录里的文件。
// mock.js 还不能 import '@/core'（它被核心层加载，反向 import 会形成循环依赖）。

const IMPORT_RE = /(?:import\s[^'"]*?from\s*|import\s*\(\s*|import\s+)['"]([^'"]+)['"]/g

export function findIllegalImports({ id, files, mockFile }) {
  const errors = []
  for (const [file, source] of Object.entries(files)) {
    for (const [, spec] of source.matchAll(IMPORT_RE)) {
      const other = spec.match(/^@\/modules\/([^/]+)/)
      if (other && other[1] !== id) {
        errors.push(`模块 ${id}: ${file} 直接 import 了模块 ${other[1]}（${spec}），请改为通过 @/core 通信`)
      }
      if (spec.startsWith('../') && path.posix.normalize(path.posix.join(path.posix.dirname(file), spec)).startsWith('..')) {
        errors.push(`模块 ${id}: ${file} 用相对路径引用了模块目录之外的文件（${spec}），请改用 @/core`)
      }
      if (file === mockFile && spec.startsWith('@/core')) {
        errors.push(`模块 ${id}: ${file} 不能 import @/core（mock 由核心层加载，会造成循环依赖）`)
      }
    }
  }
  return errors
}

function readModuleFiles(dir) {
  const files = {}
  const walk = (rel) => {
    for (const entry of fs.readdirSync(path.join(dir, rel), { withFileTypes: true })) {
      const r = rel ? `${rel}/${entry.name}` : entry.name
      if (entry.isDirectory()) walk(r)
      else if (/\.(js|mjs|vue)$/.test(entry.name)) files[r] = fs.readFileSync(path.join(dir, r), 'utf8')
    }
  }
  walk('')
  return files
}

// ---------- 生成 ----------

export function buildPagesJson({ manifests, enabled, appConfig }) {
  const pages = []
  const tabs = []
  for (const id of enabled) {
    for (const page of manifests[id].pages || []) {
      const pagePath = `modules/${id}/${page.path}`
      pages.push({ path: pagePath, style: { navigationBarTitleText: page.title || '', ...(page.style || {}) } })
      if (page.tab) tabs.push({ pagePath, text: page.tab.text, order: page.tab.order ?? 100 })
    }
  }
  tabs.sort((a, b) => a.order - b.order)
  // 第一个 tab 页就是 App 启动后的首页
  if (tabs.length) {
    const home = pages.findIndex((p) => p.path === tabs[0].pagePath)
    pages.unshift(...pages.splice(home, 1))
  }
  const json = { pages, globalStyle: appConfig.globalStyle }
  // uni-app 要求 tabBar 至少 2 项
  if (tabs.length >= 2) {
    json.tabBar = { ...appConfig.tabBar, list: tabs.map(({ pagePath, text }) => ({ pagePath, text })) }
  }
  return json
}

export function buildSlotComponent(slotName, slotDef, extensions) {
  const sorted = [...extensions].sort((a, b) => (a.order ?? 100) - (b.order ?? 100))
  const props = slotDef.props.map((p) => `:${p.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}="${p}"`).join(' ')
  const tags = sorted.map((e) => `    <${e.name}${props ? ` ${props}` : ''} />`).join('\n')
  const imports = sorted.map((e) => `import ${e.name} from '@/modules/${e.module}/${e.component}'`).join('\n')
  const propDefs = slotDef.props.map((p) => `\n  ${p}: { type: String, required: true },`).join('')
  return `<!-- 自动生成：插槽 "${slotName}"（${slotDef.description}）。请勿手改，运行 npm run gen 重新生成。 -->
<template>
  <view class="ext-slot ext-slot--${slotName}">
${tags || '    <!-- 当前没有模块扩展这个插槽 -->'}
  </view>
</template>

<script setup>
${imports}

defineProps({${propDefs}${propDefs ? '\n' : ''}})
</script>
`
}

// 生成物拆成两个文件，保证依赖方向是单向的（避免循环 import）：
//   registry.js  ← 只被核心层 import；里面的 mock.js 不允许 import '@/core'
//   setups.js    ← 只被 App.vue import；setup.js 可以放心 import '@/core'
const ident = (id) => id.replace(/-/g, '_')

function enabledList(manifests, enabled) {
  return enabled.map((id) => {
    const { __dir, ...m } = manifests[id]
    return m
  })
}

export function buildRegistryJs({ manifests, enabled, withMocks, profile = '' }) {
  const list = enabledList(manifests, enabled)
  const capabilities = {}
  for (const m of list) {
    for (const [cap, page] of Object.entries(m.provides || {})) capabilities[cap] = `/modules/${m.id}/${page}`
  }
  const mockMods = withMocks ? list.filter((m) => m.mock) : []
  const imports = mockMods.map((m) => `import * as mock_${ident(m.id)} from '@/modules/${m.id}/${m.mock}'`)
  const mocks = mockMods.map((m) => `  '${m.id}': mock_${ident(m.id)},`)
  return `// 自动生成：已启用模块清单。请勿手改，运行 npm run gen 重新生成。
${imports.join('\n')}

export const PROFILE = ${JSON.stringify(profile)}

export const MODULES = ${JSON.stringify(list, null, 2)}

export const CAPABILITIES = ${JSON.stringify(capabilities, null, 2)}

export const MOCKS = {
${mocks.join('\n')}
}
`
}

export function buildSetupsJs({ manifests, enabled }) {
  const setupMods = enabledList(manifests, enabled).filter((m) => m.setup)
  const imports = setupMods.map((m) => `import setup_${ident(m.id)} from '@/modules/${m.id}/${m.setup}'`)
  const setups = setupMods.map((m) => `  { id: '${m.id}', run: setup_${ident(m.id)} },`)
  return `// 自动生成：各模块的启动钩子，按 modules.config.json 中的顺序在 App 启动时执行。请勿手改。
${imports.join('\n')}

export const SETUPS = [
${setups.join('\n')}
]
`
}

// ---------- 配置档（profile）：同一套代码，按上架主体启用不同的模块组合 ----------

export function resolveProfile(config, requested) {
  const name = requested || config.profile
  const profile = config.profiles && config.profiles[name]
  if (!profile) {
    const known = Object.keys(config.profiles || {}).join(', ')
    throw new Error(`未知的配置档 "${name}"（可选：${known}）`)
  }
  return { name, enabled: profile.enabled, description: profile.description || '' }
}

// ---------- 读取环境变量（决定是否打包 mock 数据） ----------

function readApiMode() {
  if (process.env.VITE_API_MODE) return process.env.VITE_API_MODE
  let mode = 'mock'
  for (const f of ['.env', '.env.local']) {
    const file = path.join(ROOT, f)
    if (!fs.existsSync(file)) continue
    const m = fs.readFileSync(file, 'utf8').match(/^\s*VITE_API_MODE\s*=\s*(\w+)/m)
    if (m) mode = m[1]
  }
  return mode
}

// ---------- 主流程 ----------

export function generate() {
  let profile
  try {
    profile = resolveProfile(readJson(path.join(SRC, 'config/modules.config.json')), process.env.APP_PROFILE)
  } catch (e) {
    console.error(`✗ ${e.message}`)
    process.exit(1)
  }
  const { enabled } = profile
  const { slots } = readJson(path.join(SRC, 'config/slots.json'))
  const appConfig = readJson(path.join(SRC, 'config/app.config.json'))
  const manifests = loadManifests()
  const fileExists = (rel) => fs.existsSync(path.join(SRC, rel))

  const errors = validateModules({ manifests, enabled, slots, contractVersion: CONTRACT.version, fileExists })
  for (const id of enabled.filter((m) => manifests[m])) {
    const files = readModuleFiles(path.join(SRC, 'modules', id))
    errors.push(...findIllegalImports({ id, files, mockFile: manifests[id].mock }))
  }
  if (errors.length) {
    console.error('✗ 模块校验失败：\n' + errors.map((e) => `  - ${e}`).join('\n'))
    process.exit(1)
  }

  const apiMode = readApiMode()
  const outDir = path.join(SRC, 'generated')
  fs.rmSync(outDir, { recursive: true, force: true })
  fs.mkdirSync(path.join(outDir, 'slots'), { recursive: true })

  const pagesJson = buildPagesJson({ manifests, enabled, appConfig })
  fs.writeFileSync(
    path.join(SRC, 'pages.json'),
    '// 自动生成：请勿手改。页面来自各模块的 module.json，运行 npm run gen 重新生成。\n' +
      JSON.stringify(pagesJson, null, 2) +
      '\n',
  )

  fs.writeFileSync(
    path.join(outDir, 'registry.js'),
    buildRegistryJs({ manifests, enabled, withMocks: apiMode !== 'cloud', profile: profile.name }),
  )
  fs.writeFileSync(path.join(outDir, 'setups.js'), buildSetupsJs({ manifests, enabled }))

  for (const [slotName, slotDef] of Object.entries(slots)) {
    const extensions = enabled.flatMap((id) =>
      (manifests[id].extensions || [])
        .filter((e) => e.slot === slotName)
        .map((e) => ({ ...e, module: id, name: `${toPascal(id)}${path.basename(e.component, '.vue')}` })),
    )
    fs.writeFileSync(
      path.join(outDir, 'slots', `${toPascal(slotName)}Slot.vue`),
      buildSlotComponent(slotName, slotDef, extensions),
    )
  }

  console.log(
    `✓ 配置档 ${profile.name}：已装配 ${enabled.length} 个模块（${enabled.join(', ')}），API 模式：${apiMode}，` +
      `页面 ${pagesJson.pages.length} 个，tab ${pagesJson.tabBar?.list.length || 0} 个`,
  )
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  generate()
}
