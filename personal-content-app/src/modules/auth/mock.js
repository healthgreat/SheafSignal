// 本地模拟：任意 11 位手机号 + 验证码 123456 即可登录
const KEY = 'mock_auth_user'
const fail = (code, message) => Object.assign(new Error(message), { code })

export async function sendCode({ mobile }) {
  if (!/^1\d{10}$/.test(mobile || '')) throw fail(40001, '手机号格式不正确')
  return { sent: true, hint: '本地模拟模式：验证码是 123456' }
}

export async function login({ mobile, code }) {
  if (code !== '123456') throw fail(40001, '验证码错误（本地模拟模式请输入 123456）')
  const user = { uid: `mock_${mobile.slice(-4)}`, role: [] }
  uni.setStorageSync(KEY, user)
  return user
}

export async function current() {
  return uni.getStorageSync(KEY) || null
}

export async function logout() {
  uni.removeStorageSync(KEY)
  return null
}
