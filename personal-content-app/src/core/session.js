// 会话接口：任何模块都可以问"当前是谁登录"，但不需要知道登录是怎么实现的。
// 具体的登录实现由 auth 模块通过 setSessionProvider() 注册进来。
import { reactive } from 'vue'
import { events } from './events.js'

const state = reactive({ user: null })
let provider = null

export const session = {
  state,
  get user() {
    return state.user
  },
  isLoggedIn() {
    return !!state.user
  },
  setProvider(p) {
    provider = p
  },
  async refresh() {
    state.user = provider ? await provider.current() : null
    events.emit('session:changed', state.user)
    return state.user
  },
  async logout() {
    if (provider) await provider.logout()
    return session.refresh()
  },
}
