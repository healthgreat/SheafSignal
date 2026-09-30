'use strict'
// 统一的返回格式：{ code, message, data }。code === 0 表示成功。
// 前端 src/core/api.js 读取的是同一份 contract.json，两端永远一致。
const contract = require('./contract.json')

const CODES = Object.freeze({ ...contract.codes })

class AppError extends Error {
  constructor(code, message, data) {
    super(message || contract.messages[code] || 'error')
    this.code = code
    this.data = data
  }
}

function ok(data = null) {
  return { code: CODES.OK, message: 'ok', data }
}

function fail(code, message, data = null) {
  return { code, message: message || contract.messages[code] || 'error', data }
}

module.exports = { CODES, AppError, ok, fail, CONTRACT_VERSION: contract.version }
