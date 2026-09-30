// 适配器：把 DCloud 官方的 uni-id-co（返回格式是 { errCode, errMsg }）
// 包装成本项目统一的接口风格（成功返回数据，失败抛 ApiError）。
// 以后如果换成别的登录方案（比如微信登录、自建账号），只需要改这个文件。
//
// uni-id-co 文档：https://doc.dcloud.net.cn/uniCloud/uni-id/cloud-object.html
import { api, API_MODE, ApiError, CODES } from '@/core'

const SCENE = 'login-by-sms'

function uniIdCo() {
  return uniCloud.importObject('uni-id-co', { customUI: true })
}

async function wrap(fn) {
  try {
    return await fn()
  } catch (e) {
    throw new ApiError(CODES.INVALID_PARAMS, e.errMsg || e.message || '操作失败')
  }
}

const cloud = {
  // 发送短信前需要图形验证码（防止短信被刷）
  async createCaptcha() {
    const res = await wrap(() => uniIdCo().createCaptcha({ scene: 'send-sms-code' }))
    return res.captchaBase64
  },
  sendCode: (mobile, captcha) => wrap(() => uniIdCo().sendSmsCode({ mobile, captcha, scene: SCENE })),
  // 登录成功后 uniCloud 客户端会自动保存 token
  login: (mobile, code) => wrap(() => uniIdCo().loginBySms({ mobile, code })),
  async current() {
    const info = uniCloud.getCurrentUserInfo()
    return info.uid && info.tokenExpired > Date.now() ? { uid: info.uid, role: info.role || [] } : null
  },
  async logout() {
    await wrap(() => uniIdCo().logout()).catch(() => {})
    uni.removeStorageSync('uni_id_token')
    uni.removeStorageSync('uni_id_token_expired')
  },
}

const mock = {
  createCaptcha: async () => null,
  sendCode: (mobile) => api.call('auth', 'sendCode', { mobile }),
  login: (mobile, code) => api.call('auth', 'login', { mobile, code }),
  current: () => api.call('auth', 'current'),
  logout: () => api.call('auth', 'logout'),
}

export const authService = API_MODE === 'cloud' ? cloud : mock
