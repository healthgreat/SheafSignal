export function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = String(sec % 60).padStart(2, '0')
  return `${m}:${s}`
}

export function playerUrl(bvid) {
  return `https://player.bilibili.com/player.html?bvid=${encodeURIComponent(bvid)}&autoplay=0`
}

export function webUrl(bvid) {
  return `https://www.bilibili.com/video/${encodeURIComponent(bvid)}`
}
