// 启动钩子：把本模块注册为核心层 session 的实现，然后读取一次登录状态
import { session } from '@/core'
import { authService } from './service.js'

export default async function setup() {
  session.setProvider({ current: authService.current, logout: authService.logout })
  await session.refresh()
}
