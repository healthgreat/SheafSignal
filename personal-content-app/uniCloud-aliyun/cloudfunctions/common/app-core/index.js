'use strict'
// app-core：所有业务云对象共享的统一接口层（uniCloud 公共模块）
const errors = require('./errors')
const { validate } = require('./validate')
const { createModule } = require('./module')
const { createMemoryStore, createUniCloudStore } = require('./store')
const { createKeywordModeration } = require('./moderation')
const { createUniIdAuth } = require('./auth')

module.exports = {
  ...errors,
  validate,
  createModule,
  createMemoryStore,
  createUniCloudStore,
  createKeywordModeration,
  createUniIdAuth,
}
