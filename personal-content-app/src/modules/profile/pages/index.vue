<template>
  <view>
    <!-- 扩展插槽：启用 auth 模块时，这里会出现登录 / 账号卡片 -->
    <ProfileHeaderSlot />

    <view class="card list">
      <view class="item" @tap="open('termsPage')">服务协议</view>
      <view class="item" @tap="open('privacyPage')">隐私政策</view>
    </view>

    <view class="card">
      <view class="muted">配置档：{{ PROFILE }} · API 模式：{{ API_MODE }}</view>
      <view v-for="m in registry.modules" :key="m.id" class="mod">
        <text>{{ m.name }}</text>
        <text class="muted">{{ m.id }} · v{{ m.version }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { registry, API_MODE, PROFILE } from '@/core'
import ProfileHeaderSlot from '@/generated/slots/ProfileHeaderSlot.vue'

function open(capability) {
  const url = registry.capability(capability)
  if (url) uni.navigateTo({ url })
}
</script>

<style scoped>
.list { padding: 0 28rpx; }
.item { padding: 28rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.item:last-child { border-bottom: none; }
.mod { display: flex; justify-content: space-between; margin-top: 12rpx; }
</style>
