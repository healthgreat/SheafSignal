<template>
  <view class="card comments">
    <view class="head">评论 <text class="muted">{{ total }}</text></view>

    <view v-if="session.state.user" class="editor">
      <input class="nick" v-model="nickname" maxlength="20" placeholder="昵称（选填，默认“读者”）" />
      <!-- editorKey 变化时重建输入框：uni H5 的 textarea 在聚焦状态下不响应外部清空 -->
      <textarea
        :key="editorKey"
        class="input"
        :value="content"
        maxlength="500"
        auto-height
        placeholder="写下你的想法…"
        @input="content = $event.detail.value"
      />
      <view class="actions">
        <text class="muted">{{ content.length }}/500 · 审核通过后公开显示</text>
        <button size="mini" class="btn-primary" :disabled="!content.trim() || submitting" @tap="submit">发表</button>
      </view>
    </view>
    <view v-else class="login-tip" @tap="requireLogin">登录后发表评论 ›</view>

    <view v-for="c in minePending" :key="c._id" class="item pending">
      <view class="meta"><text class="nick-text">{{ c.nickname }}</text><text class="badge">审核中，仅自己可见</text></view>
      <view>{{ c.content }}</view>
    </view>
    <view v-for="c in items" :key="c._id" class="item">
      <view class="meta"><text class="nick-text">{{ c.nickname }}</text><text class="muted">{{ formatDate(c.create_date) }}</text></view>
      <view>{{ c.content }}</view>
    </view>
    <view v-if="loaded && !items.length && !minePending.length" class="empty">还没有评论</view>
  </view>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { api, session, events, requireLogin, toastError, formatDate } from '@/core'

const props = defineProps({
  targetType: { type: String, required: true },
  targetId: { type: String, required: true },
})

const items = ref([])
const minePending = ref([])
const total = ref(0)
const loaded = ref(false)
const content = ref('')
const nickname = ref(uni.getStorageSync('comment_nickname') || '')
const submitting = ref(false)
const editorKey = ref(0)

async function load() {
  try {
    const res = await api.call('comment', 'list', { targetType: props.targetType, targetId: props.targetId })
    items.value = res.items
    minePending.value = res.minePending
    total.value = res.total
  } catch (e) {
    console.warn('[comment] list', e)
  } finally {
    loaded.value = true
  }
}

async function submit() {
  submitting.value = true
  try {
    await api.call('comment', 'create', {
      targetType: props.targetType,
      targetId: props.targetId,
      content: content.value,
      nickname: nickname.value,
    })
    uni.setStorageSync('comment_nickname', nickname.value)
    content.value = ''
    editorKey.value++
    uni.showToast({ title: '已提交，审核通过后显示', icon: 'none' })
    await load()
  } catch (e) {
    toastError(e)
  } finally {
    submitting.value = false
  }
}

// 通过事件得知登录状态变化，而不是直接依赖 auth 模块
const off = events.on('session:changed', load)
onUnmounted(off)
watch(() => props.targetId, load, { immediate: true })
</script>

<style scoped>
.head { font-size: 32rpx; font-weight: 600; margin-bottom: 16rpx; }
.editor { border: 1rpx solid #eee; border-radius: 12rpx; padding: 16rpx; margin-bottom: 16rpx; }
.nick { font-size: 26rpx; border-bottom: 1rpx solid #f0f0f0; padding-bottom: 12rpx; margin-bottom: 12rpx; }
.input { width: 100%; min-height: 120rpx; font-size: 28rpx; }
.actions { display: flex; justify-content: space-between; align-items: center; margin-top: 12rpx; }
.login-tip { color: #2b6cb0; padding: 20rpx 0; }
.item { padding: 20rpx 0; border-top: 1rpx solid #f3f3f3; }
.meta { display: flex; justify-content: space-between; margin-bottom: 6rpx; }
.nick-text { font-weight: 600; font-size: 26rpx; }
.pending { opacity: 0.7; }
.badge { font-size: 22rpx; color: #ad6800; }
</style>
