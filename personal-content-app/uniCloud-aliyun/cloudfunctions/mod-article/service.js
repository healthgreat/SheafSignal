'use strict'
// 文章模块：只负责"读"。发布、编辑在管理后台（uni-admin / uniCloud 控制台）完成。
const COLLECTION = 'app-article'
const LIST_FIELDS = ['_id', 'title', 'summary', 'cover', 'publish_date']

const pick = (doc, fields) => Object.fromEntries(fields.map((f) => [f, doc[f]]))

module.exports = {
  name: 'article',
  version: '1.0.0',
  actions: {
    list: {
      auth: 'public',
      params: {
        page: { type: 'integer', min: 1, default: 1 },
        pageSize: { type: 'integer', min: 1, max: 50, default: 10 },
      },
      async handler({ page, pageSize }, { store }) {
        const col = store.collection(COLLECTION)
        const where = { status: 'published' }
        const [docs, total] = await Promise.all([
          col.find({ where, orderBy: ['publish_date', 'desc'], skip: (page - 1) * pageSize, limit: pageSize }),
          col.count(where),
        ])
        return { items: docs.map((d) => pick(d, LIST_FIELDS)), page, pageSize, total }
      },
    },
    get: {
      auth: 'public',
      params: { id: { type: 'string', required: true, max: 64 } },
      async handler({ id }, { store, AppError, CODES }) {
        const doc = await store.collection(COLLECTION).get(id)
        if (!doc || doc.status !== 'published') throw new AppError(CODES.NOT_FOUND)
        return pick(doc, [...LIST_FIELDS, 'content'])
      },
    },
  },
}
