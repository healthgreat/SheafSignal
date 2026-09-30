<template>
  <view>
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
        <button size="mini" class="btn-primary" @tap="login">登录</button>
      </view>
    </view>

    <view class="card list">
      <view class="item" @tap="open('termsPage')">服务协议</view>
      <view class="item" @tap="open('privacyPage')">隐私政策</view>
    </view>

    <view class="card">
      <view class="muted">已启用模块（API 模式：{{ API_MODE }}）</view>
      <view v-for="m in registry.modules" :key="m.id" class="mod">
        <text>{{ m.name }}</text>
        <text class="muted">{{ m.id }} · v{{ m.version }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { session, registry, requireLogin, API_MODE } from '@/core'

const shortId = computed(() => (session.state.user?.uid || '').slice(-8))

function login() {
  requireLogin()
}

async function logout() {
  await session.logout()
  uni.showToast({ title: '已退出', icon: 'none' })
}

function open(capability) {
  const url = registry.capability(capability)
  if (url) uni.navigateTo({ url })
}
</script>

<style scoped>
.row { display: flex; justify-content: space-between; align-items: center; gap: 24rpx; }
.name { font-size: 34rpx; font-weight: 600; }
.list { padding: 0 28rpx; }
.item { padding: 28rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.item:last-child { border-bottom: none; }
.mod { display: flex; justify-content: space-between; margin-top: 12rpx; }
</style>
