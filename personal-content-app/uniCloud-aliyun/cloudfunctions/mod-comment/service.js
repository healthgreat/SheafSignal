'use strict'
// 评论模块：遵循"后台实名、前台自愿"——
//   发评论必须登录（手机号验证），但页面上只显示读者自己填的昵称。
// 所有评论"先审后发"：机器审核通过后进入 pending，管理员人工通过后才公开显示。
// 与点赞模块一样，通过 targetType + targetId 挂在任何内容上。
const COLLECTION = 'app-comment'
const MIN_INTERVAL_MS = 15 * 1000
const TARGET = {
  targetType: { type: 'string', required: true, pattern: '^[a-z][a-z0-9-]{1,30}$' },
  targetId: { type: 'string', required: true, max: 64 },
}
const PUBLIC_FIELDS = ['_id', 'nickname', 'content', 'create_date', 'status']
const pick = (doc) => Object.fromEntries(PUBLIC_FIELDS.map((f) => [f, doc[f]]))

module.exports = {
  name: 'comment',
  version: '1.0.0',
  actions: {
    list: {
      auth: 'public',
      params: {
        ...TARGET,
        page: { type: 'integer', min: 1, default: 1 },
        pageSize: { type: 'integer', min: 1, max: 50, default: 20 },
      },
      async handler({ targetType, targetId, page, pageSize }, { store, uid }) {
        const col = store.collection(COLLECTION)
        const base = { target_type: targetType, target_id: targetId }
        const where = { ...base, status: 'approved' }
        const [docs, total, mine] = await Promise.all([
          col.find({ where, orderBy: ['create_date', 'desc'], skip: (page - 1) * pageSize, limit: pageSize }),
          col.count(where),
          // 自己还在审核中的评论，只有自己能看到
          uid ? col.find({ where: { ...base, user_id: uid, status: 'pending' }, orderBy: ['create_date', 'desc'] }) : [],
        ])
        return { items: docs.map(pick), total, page, pageSize, minePending: mine.map(pick) }
      },
    },
    create: {
      auth: 'user',
      params: {
        ...TARGET,
        content: { type: 'string', required: true, min: 1, max: 500 },
        nickname: { type: 'string', max: 20, default: '读者' },
      },
      async handler({ targetType, targetId, content, nickname }, { store, uid, moderation, now, AppError, CODES }) {
        const col = store.collection(COLLECTION)
        const [last] = await col.find({ where: { user_id: uid }, orderBy: ['create_date', 'desc'], limit: 1 })
        if (last && now() - last.create_date < MIN_INTERVAL_MS) throw new AppError(CODES.RATE_LIMITED)

        const verdict = await moderation.check(`${nickname}\n${content}`)
        if (!verdict.pass) throw new AppError(CODES.CONTENT_REJECTED, verdict.reason)

        const id = await col.insert({
          target_type: targetType,
          target_id: targetId,
          user_id: uid,
          nickname,
          content,
          status: 'pending',
          create_date: now(),
        })
        return { id, status: 'pending' }
      },
    },
    remove: {
      auth: 'user',
      params: { id: { type: 'string', required: true, max: 64 } },
      async handler({ id }, { store, uid, role, AppError, CODES }) {
        const col = store.collection(COLLECTION)
        const doc = await col.get(id)
        if (!doc) throw new AppError(CODES.NOT_FOUND)
        if (doc.user_id !== uid && !role.includes('admin')) throw new AppError(CODES.FORBIDDEN)
        await col.remove({ _id: id })
        return { id }
      },
    },
    // ---- 以下为管理员接口 ----
    pending: {
      auth: 'admin',
      params: { page: { type: 'integer', min: 1, default: 1 } },
      async handler({ page }, { store }) {
        const docs = await store
          .collection(COLLECTION)
          .find({ where: { status: 'pending' }, orderBy: ['create_date', 'asc'], skip: (page - 1) * 50, limit: 50 })
        return { items: docs.map((d) => ({ ...pick(d), target_type: d.target_type, target_id: d.target_id })) }
      },
    },
    review: {
      auth: 'admin',
      params: {
        id: { type: 'string', required: true, max: 64 },
        decision: { type: 'string', required: true, enum: ['approved', 'rejected'] },
      },
      async handler({ id, decision }, { store, uid, now, AppError, CODES }) {
        const col = store.collection(COLLECTION)
        if (!(await col.get(id))) throw new AppError(CODES.NOT_FOUND)
        await col.update(id, { status: decision, reviewer_id: uid, review_date: now() })
        return { id, status: decision }
      },
    },
  },
}
