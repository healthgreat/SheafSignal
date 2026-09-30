// 本地模拟数据：返回格式与云端 mod-article 完全一致
const DAY = 86400000
const now = Date.now()
const ARTICLES = [
  {
    _id: 'a1',
    title: '写在开始：为什么我要做这个小站',
    summary: '把自己的文字和视频放在一个地方，慢慢积累。',
    cover: '',
    publish_date: now - 1 * DAY,
    status: 'published',
    content:
      '<p>这是一篇示例文章。正文使用 HTML 存储，在 App 里用 <b>rich-text</b> 组件渲染。</p><p>你可以在管理后台（uni-admin）里编辑文章，发布后这里会自动显示。</p>',
  },
  {
    _id: 'a2',
    title: '秋天的第一场雨',
    summary: '雨落下来的时候，城市突然安静了。',
    cover: '',
    publish_date: now - 3 * DAY,
    status: 'published',
    content: '<p>雨落下来的时候，城市突然安静了。</p><p>（示例美文，替换成你自己的内容即可。）</p>',
  },
  {
    _id: 'a3',
    title: '草稿：还没写完的一篇',
    summary: '',
    cover: '',
    publish_date: now,
    status: 'draft',
    content: '<p>草稿不会出现在列表里。</p>',
  },
]
const LIST_FIELDS = ['_id', 'title', 'summary', 'cover', 'publish_date']
const pick = (doc, fields) => Object.fromEntries(fields.map((f) => [f, doc[f]]))
const published = () => ARTICLES.filter((a) => a.status === 'published').sort((a, b) => b.publish_date - a.publish_date)

export async function list({ page = 1, pageSize = 10 }) {
  const all = published()
  const items = all.slice((page - 1) * pageSize, page * pageSize).map((d) => pick(d, LIST_FIELDS))
  return { items, page, pageSize, total: all.length }
}

export async function get({ id }) {
  const doc = published().find((a) => a._id === id)
  if (!doc) throw Object.assign(new Error('内容不存在'), { code: 40401 })
  return pick(doc, [...LIST_FIELDS, 'content'])
}
