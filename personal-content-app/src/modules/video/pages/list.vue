<template>
  <view>
    <view v-for="item in items" :key="item._id" class="card item" @tap="open(item._id)">
      <view class="cover">
        <image v-if="item.cover" class="cover-img" :src="item.cover" mode="aspectFill" />
        <text v-else class="play">▶</text>
        <text v-if="item.duration" class="duration">{{ formatDuration(item.duration) }}</text>
      </view>
      <view class="title">{{ item.title }}</view>
      <view class="muted">{{ formatDate(item.publish_date) }}</view>
    </view>
    <view v-if="loaded && !items.length" class="empty">还没有视频</view>
    <view v-if="items.length && noMore" class="empty">— 没有更多了 —</view>
  </view>
</template>

<script setup>
import { usePagedList } from '@/core/usePagedList.js'
import { formatDate } from '@/core'
import { formatDuration } from '../format.js'

const { items, loaded, noMore } = usePagedList('video', 'list')

function open(id) {
  uni.navigateTo({ url: `/modules/video/pages/detail?id=${id}` })
}
</script>

<style scoped>
.cover { position: relative; height: 360rpx; border-radius: 12rpx; background: linear-gradient(135deg, #2b6cb0, #553c9a); display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 16rpx; }
.cover-img { width: 100%; height: 100%; }
.play { color: #fff; font-size: 80rpx; }
.duration { position: absolute; right: 16rpx; bottom: 12rpx; color: #fff; font-size: 24rpx; background: rgba(0, 0, 0, 0.5); padding: 2rpx 12rpx; border-radius: 8rpx; }
.title { font-size: 32rpx; font-weight: 600; }
</style>
