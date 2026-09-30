<template>
  <view class="card like">
    <view class="btn" :class="{ on: liked }" @tap="toggle">
      <text class="icon">{{ liked ? '♥' : '♡' }}</text>
      <text>{{ liked ? '已赞' : '点赞' }}</text>
      <text v-if="count" class="count">{{ count }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api, toastError } from '@/core'

// 插槽统一约定的 props：targetType + targetId
const props = defineProps({
  targetType: { type: String, required: true },
  targetId: { type: String, required: true },
})

const liked = ref(false)
const count = ref(0)
let busy = false

async function load() {
  try {
    const res = await api.call('like', 'status', { targetType: props.targetType, targetIds: [props.targetId] })
    const s = res[props.targetId] || { liked: false, count: 0 }
    liked.value = s.liked
    count.value = s.count
  } catch (e) {
    // 点赞状态加载失败不影响阅读，静默处理
    console.warn('[like] status', e)
  }
}

async function toggle() {
  if (busy) return
  busy = true
  try {
    const res = await api.call('like', 'toggle', { targetType: props.targetType, targetId: props.targetId })
    liked.value = res.liked
    count.value = res.count
  } catch (e) {
    toastError(e)
  } finally {
    busy = false
  }
}

watch(() => props.targetId, load, { immediate: true })
</script>

<style scoped>
.like { display: flex; justify-content: center; }
.btn { display: flex; align-items: center; gap: 12rpx; padding: 12rpx 48rpx; border: 2rpx solid #ddd; border-radius: 48rpx; color: #666; }
.btn.on { border-color: #e53e3e; color: #e53e3e; }
.icon { font-size: 36rpx; }
.count { font-size: 26rpx; }
</style>
