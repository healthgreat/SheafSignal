// 模块之间的通信只走事件，不互相 import。
// 例如：auth 模块登录成功后 emit('session:changed')，comment 模块监听后刷新评论区。
const listeners = new Map()

export const events = {
  on(name, fn) {
    if (!listeners.has(name)) listeners.set(name, new Set())
    listeners.get(name).add(fn)
    return () => events.off(name, fn)
  },
  off(name, fn) {
    listeners.get(name)?.delete(fn)
  },
  emit(name, payload) {
    for (const fn of listeners.get(name) || []) {
      try {
        fn(payload)
      } catch (e) {
        console.error(`[events] ${name}`, e)
      }
    }
  },
}
