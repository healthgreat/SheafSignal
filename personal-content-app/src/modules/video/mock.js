// 本地模拟数据：返回格式与云端 mod-video 完全一致
// ⚠️ bvid 是占位符，请换成你自己在 B 站发布的视频 BV 号
const DAY = 86400000
const now = Date.now()
const VIDEOS = [
  {
    _id: 'v1',
    title: '示例视频：第一支 vlog',
    cover: '',
    duration: 185,
    bvid: 'BV1xxxxxxxxx',
    description: '视频托管在 B 站，这里只保存 BV 号。',
    publish_date: now - 2 * DAY,
    status: 'published',
  },
  {
    _id: 'v2',
    title: '示例视频：读书分享',
    cover: '',
    duration: 642,
    bvid: 'BV1yyyyyyyyy',
    description: '',
    publish_date: now - 5 * DAY,
    status: 'published',
  },
]
const LIST_FIELDS = ['_id', 'title', 'cover', 'duration', 'publish_date']
const pick = (doc, fields) => Object.fromEntries(fields.map((f) => [f, doc[f]]))
const published = () => VIDEOS.filter((v) => v.status === 'published').sort((a, b) => b.publish_date - a.publish_date)

export async function list({ page = 1, pageSize = 10 }) {
  const all = published()
  const items = all.slice((page - 1) * pageSize, page * pageSize).map((d) => pick(d, LIST_FIELDS))
  return { items, page, pageSize, total: all.length }
}

export async function get({ id }) {
  const doc = published().find((v) => v._id === id)
  if (!doc) throw Object.assign(new Error('内容不存在'), { code: 40401 })
  return pick(doc, [...LIST_FIELDS, 'bvid', 'description'])
}
