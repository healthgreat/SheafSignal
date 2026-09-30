// 本地模拟：逻辑与云端 mod-comment 一致（登录才能评论、先审后发）
// 为了方便预览，mock 模式下提交 5 秒后自动"审核通过"
const comments = [
  { _id: 'c1', target_type: 'article', target_id: 'a1', user_id: 'u0', nickname: '路过的读者', content: '写得真好，期待更新！', status: 'approved', create_date: Date.now() - 3600e3 },
]
let seq = 1
const fail = (code, message) => Object.assign(new Error(message), { code })
const pick = ({ _id, nickname, content, create_date, status }) => ({ _id, nickname, content, create_date, status })

export async function list({ targetType, targetId, page = 1, pageSize = 20 }, { user }) {
  const base = (c) => c.target_type === targetType && c.target_id === targetId
  const approved = comments.filter((c) => base(c) && c.status === 'approved').sort((a, b) => b.create_date - a.create_date)
  const minePending = user ? comments.filter((c) => base(c) && c.user_id === user.uid && c.status === 'pending') : []
  return {
    items: approved.slice((page - 1) * pageSize, page * pageSize).map(pick),
    total: approved.length,
    page,
    pageSize,
    minePending: minePending.map(pick),
  }
}

export async function create({ targetType, targetId, content, nickname }, { user }) {
  if (!user) throw fail(40101, '请先登录')
  if (!content || !content.trim()) throw fail(40001, '评论内容不能为空')
  const doc = {
    _id: `c${++seq}`,
    target_type: targetType,
    target_id: targetId,
    user_id: user.uid,
    nickname: (nickname || '').trim() || '读者',
    content: content.trim(),
    status: 'pending',
    create_date: Date.now(),
  }
  comments.push(doc)
  setTimeout(() => (doc.status = 'approved'), 5000)
  return { id: doc._id, status: 'pending' }
}

export async function remove({ id }, { user }) {
  const i = comments.findIndex((c) => c._id === id)
  if (i < 0) throw fail(40401, '内容不存在')
  if (!user || comments[i].user_id !== user.uid) throw fail(40301, '没有权限')
  comments.splice(i, 1)
  return { id }
}
