<template>
  <view class="card">
    <view v-if="session.state.user" class="row">
      <view>
        <view class="name">已登录</view>
        <view class="muted">ID：{{ shortId }}</view>
      </view>
      <button size="mini" @tap="logout">退出登录</button>
    </view>
    <view v-else class="row">
      <view>
        <view class="name">未登录</view>
        <view class="muted">浏览和点赞不需要登录，发表评论需要验证手机号</view>
      </view>
      <button size="mini" class="btn-primary" @tap="requireLogin">登录</button>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { session, requireLogin } from '@/core'

const shortId = computed(() => (session.state.user?.uid || '').slice(-8))

async function logout() {
  await session.logout()
  uni.showToast({ title: '已退出', icon: 'none' })
}
</script>

<style scoped>
.row { display: flex; justify-content: space-between; align-items: center; gap: 24rpx; }
.name { font-size: 34rpx; font-weight: 600; }
</style>
