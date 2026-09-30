// 设备标识：cloud 模式下 uniCloud 会自动把 deviceId 带到云端，这里只给 mock 模式用。
const KEY = 'app_device_id'

export function getDeviceId() {
  try {
    let id = uni.getStorageSync(KEY)
    if (!id) {
      id = `dev_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
      uni.setStorageSync(KEY, id)
    }
    return id
  } catch (e) {
    return 'dev_unknown'
  }
}
