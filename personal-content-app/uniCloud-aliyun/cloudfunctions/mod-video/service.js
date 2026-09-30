'use strict'
// 视频模块：只存视频的"元数据"（标题、封面、B 站 BV 号），视频文件本身托管在 B 站。
// 这样视频的存储、转码、带宽、视听许可都不由本 App 承担。
const COLLECTION = 'app-video'
const LIST_FIELDS = ['_id', 'title', 'cover', 'duration', 'publish_date']

const pick = (doc, fields) => Object.fromEntries(fields.map((f) => [f, doc[f]]))

module.exports = {
  name: 'video',
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
        return pick(doc, [...LIST_FIELDS, 'bvid', 'description'])
      },
    },
  },
}
