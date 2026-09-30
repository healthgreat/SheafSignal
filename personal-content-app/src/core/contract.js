// 前端与云端共用同一份接口契约（错误码 + 默认提示语），唯一来源在 app-core。
import contract from '../../uniCloud-aliyun/cloudfunctions/common/app-core/contract.json'

export const CONTRACT_VERSION = contract.version
export const CODES = Object.freeze({ ...contract.codes })

export function messageOf(code) {
  return contract.messages[String(code)] || '出错了'
}

export class ApiError extends Error {
  constructor(code, message, data = null) {
    super(message || messageOf(code))
    this.code = code
    this.data = data
  }
}
