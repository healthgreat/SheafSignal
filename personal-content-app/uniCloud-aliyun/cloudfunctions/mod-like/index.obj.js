'use strict'
// 云对象入口：只负责把模块定义接入统一接口层，业务逻辑全部在 service.js
const { createModule } = require('app-core')
module.exports = createModule(require('./service'))
