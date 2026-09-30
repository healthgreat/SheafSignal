'use strict'
// 极简参数校验。每个 action 用同一种 schema 写法声明参数，
// 不合法时统一抛 INVALID_PARAMS，业务代码里不需要再手写校验。
const { AppError, CODES } = require('./errors')

function checkType(value, type) {
  if (type === 'array') return Array.isArray(value)
  if (type === 'integer') return Number.isInteger(value)
  return typeof value === type
}

function validate(params, schema = {}) {
  const input = params && typeof params === 'object' ? params : {}
  const out = {}
  for (const [key, rule] of Object.entries(schema)) {
    let value = input[key]
    if (value === undefined || value === null || value === '') {
      if (rule.required) throw new AppError(CODES.INVALID_PARAMS, `缺少参数 ${key}`)
      if (rule.default !== undefined) out[key] = rule.default
      continue
    }
    if (!checkType(value, rule.type)) {
      throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 应为 ${rule.type}`)
    }
    if (rule.type === 'string') {
      value = value.trim()
      if (rule.min !== undefined && value.length < rule.min) {
        throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 太短`)
      }
      if (rule.max !== undefined && value.length > rule.max) {
        throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 太长（最多 ${rule.max} 字）`)
      }
      if (rule.pattern && !new RegExp(rule.pattern).test(value)) {
        throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 格式不正确`)
      }
    }
    if (rule.type === 'integer' || rule.type === 'number') {
      if (rule.min !== undefined && value < rule.min) throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 过小`)
      if (rule.max !== undefined && value > rule.max) throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 过大`)
    }
    if (rule.type === 'array' && rule.max !== undefined && value.length > rule.max) {
      throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 最多 ${rule.max} 项`)
    }
    if (rule.enum && !rule.enum.includes(value)) {
      throw new AppError(CODES.INVALID_PARAMS, `参数 ${key} 取值不在允许范围`)
    }
    out[key] = value
  }
  return out
}

module.exports = { validate }
