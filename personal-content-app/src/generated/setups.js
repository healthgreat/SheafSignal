// 自动生成：各模块的启动钩子，按 modules.config.json 中的顺序在 App 启动时执行。请勿手改。
import setup_auth from '@/modules/auth/setup.js'

export const SETUPS = [
  { id: 'auth', run: setup_auth },
]
