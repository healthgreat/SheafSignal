'use strict'
// 存储抽象：业务模块只认识下面这组方法，不直接调用 uniCloud 数据库 API。
// 以后换数据库（阿里云 → 腾讯云 → 自建 MongoDB），只需要新写一个适配器。
//
//   collection(name) → {
//     find({ where, orderBy: [field, 'asc'|'desc'], skip, limit }) → docs[]
//     count(where) → number
//     get(id) → doc | null
//     insert(doc) → id
//     update(id, patch) → void
//     remove(where) → 删除条数
//   }
//
// where 只支持两种写法：{ field: value }（相等）和 { field: { $in: [...] } }。

function matches(doc, where = {}) {
  return Object.entries(where).every(([key, cond]) => {
    if (cond && typeof cond === 'object' && Array.isArray(cond.$in)) {
      return cond.$in.includes(doc[key])
    }
    return doc[key] === cond
  })
}

// 内存实现：单元测试用，也可以用于本地脚本
function createMemoryStore(seed = {}) {
  const tables = new Map(Object.entries(seed).map(([k, rows]) => [k, rows.map((r) => ({ ...r }))]))
  let seq = 0
  const table = (name) => {
    if (!tables.has(name)) tables.set(name, [])
    return tables.get(name)
  }
  return {
    collection(name) {
      const rows = table(name)
      return {
        async find({ where = {}, orderBy, skip = 0, limit = 20 } = {}) {
          let list = rows.filter((d) => matches(d, where))
          if (orderBy) {
            const [field, dir = 'asc'] = orderBy
            const sign = dir === 'desc' ? -1 : 1
            list = [...list].sort((a, b) => (a[field] > b[field] ? sign : a[field] < b[field] ? -sign : 0))
          }
          return list.slice(skip, skip + limit).map((d) => ({ ...d }))
        },
        async count(where = {}) {
          return rows.filter((d) => matches(d, where)).length
        },
        async get(id) {
          const doc = rows.find((d) => d._id === id)
          return doc ? { ...doc } : null
        },
        async insert(doc) {
          const _id = doc._id || `mem_${++seq}`
          rows.push({ ...doc, _id })
          return _id
        },
        async update(id, patch) {
          const doc = rows.find((d) => d._id === id)
          if (doc) Object.assign(doc, patch)
        },
        async remove(where = {}) {
          let removed = 0
          for (let i = rows.length - 1; i >= 0; i--) {
            if (matches(rows[i], where)) {
              rows.splice(i, 1)
              removed++
            }
          }
          return removed
        },
      }
    },
  }
}

// uniCloud 云数据库实现：线上环境使用
function createUniCloudStore(db) {
  const cmd = db.command
  const translate = (where = {}) => {
    const out = {}
    for (const [key, cond] of Object.entries(where)) {
      out[key] = cond && typeof cond === 'object' && Array.isArray(cond.$in) ? cmd.in(cond.$in) : cond
    }
    return out
  }
  return {
    collection(name) {
      const col = db.collection(name)
      return {
        async find({ where = {}, orderBy, skip = 0, limit = 20 } = {}) {
          let q = col.where(translate(where))
          if (orderBy) q = q.orderBy(orderBy[0], orderBy[1] || 'asc')
          const res = await q.skip(skip).limit(limit).get()
          return res.data
        },
        async count(where = {}) {
          const res = await col.where(translate(where)).count()
          return res.total
        },
        async get(id) {
          const res = await col.doc(id).get()
          return res.data && res.data[0] ? res.data[0] : null
        },
        async insert(doc) {
          const res = await col.add(doc)
          return res.id
        },
        async update(id, patch) {
          await col.doc(id).update(patch)
        },
        async remove(where = {}) {
          const res = await col.where(translate(where)).remove()
          return res.deleted
        },
      }
    },
  }
}

module.exports = { createMemoryStore, createUniCloudStore }
