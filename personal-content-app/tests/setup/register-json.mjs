// 让 Node 能像 Vite 一样直接 import .json（测试前端 core 代码时需要）
import { register } from 'node:module'

register(
  'data:text/javascript,' +
    encodeURIComponent(`
export async function load(url, context, next) {
  if (url.endsWith('.json')) return next(url, { ...context, importAttributes: { type: 'json' } })
  return next(url, context)
}
`),
)
