<template>
  <view>
    <view v-for="item in items" :key="item._id" class="card item" @tap="open(item._id)">
      <image v-if="item.cover" class="cover" :src="item.cover" mode="aspectFill" />
      <view class="title">{{ item.title }}</view>
      <view v-if="item.summary" class="summary">{{ item.summary }}</view>
      <view class="muted">{{ formatDate(item.publish_date) }}</view>
    </view>
    <view v-if="loaded && !items.length" class="empty">还没有文章</view>
    <view v-if="items.length && noMore" class="empty">— 没有更多了 —</view>
  </view>
</template>

<script setup>
import { usePagedList } from '@/core/usePagedList.js'
import { formatDate } from '@/core'

const { items, loaded, noMore } = usePagedList('article', 'list')

function open(id) {
  uni.navigateTo({ url: `/modules/article/pages/detail?id=${id}` })
}
</script>

<style scoped>
.item .title { font-size: 34rpx; font-weight: 600; }
.item .summary { color: #555; margin: 8rpx 0; }
.cover { width: 100%; height: 300rpx; border-radius: 12rpx; margin-bottom: 16rpx; }
</style>
