// 通用分页列表：任何模块的 list 接口只要遵守 { items, total } 的返回约定，都可以直接复用
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import { api, toastError } from './index.js'

export function usePagedList(module, action, { pageSize = 10, params = {} } = {}) {
  const items = ref([])
  const loaded = ref(false)
  const noMore = ref(false)
  let page = 0
  let loading = false

  async function load(reset = false) {
    if (loading || (noMore.value && !reset)) return
    loading = true
    try {
      const next = reset ? 1 : page + 1
      const res = await api.call(module, action, { ...params, page: next, pageSize })
      items.value = reset ? res.items : [...items.value, ...res.items]
      page = next
      noMore.value = items.value.length >= res.total
    } catch (e) {
      toastError(e)
    } finally {
      loading = false
      loaded.value = true
    }
  }

  onLoad(() => load(true))
  onPullDownRefresh(async () => {
    await load(true)
    uni.stopPullDownRefresh()
  })
  onReachBottom(() => load())

  return { items, loaded, noMore, reload: () => load(true) }
}
