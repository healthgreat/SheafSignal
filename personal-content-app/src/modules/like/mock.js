// 本地模拟：内存中的点赞记录，逻辑与云端 mod-like 一致
const records = []
const count = (t, id) => records.filter((r) => r.t === t && r.id === id).length

export async function toggle({ targetType, targetId }, { deviceId }) {
  const i = records.findIndex((r) => r.t === targetType && r.id === targetId && r.dev === deviceId)
  if (i >= 0) records.splice(i, 1)
  else records.push({ t: targetType, id: targetId, dev: deviceId })
  return { liked: i < 0, count: count(targetType, targetId) }
}

export async function status({ targetType, targetIds }, { deviceId }) {
  const out = {}
  for (const id of targetIds) {
    out[id] = {
      count: count(targetType, id),
      liked: records.some((r) => r.t === targetType && r.id === id && r.dev === deviceId),
    }
  }
  return out
}
