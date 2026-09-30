<template>
  <view v-if="doc">
    <view class="card">
      <view class="cover" @tap="play">
        <image v-if="doc.cover" class="cover-img" :src="doc.cover" mode="aspectFill" />
        <text class="play">▶</text>
      </view>
      <view class="title">{{ doc.title }}</view>
      <view class="muted">{{ formatDate(doc.publish_date) }} · {{ formatDuration(doc.duration) }}</view>
      <view v-if="doc.description" class="desc">{{ doc.description }}</view>
    </view>
    <ContentFooterSlot target-type="video" :target-id="doc._id" />
  </view>
  <view v-else-if="error" class="empty">{{ error }}</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, formatDate } from '@/core'
import ContentFooterSlot from '@/generated/slots/ContentFooterSlot.vue'
import { formatDuration, webUrl } from '../format.js'

const doc = ref(null)
const error = ref('')

onLoad(async ({ id }) => {
  try {
    doc.value = await api.call('video', 'get', { id })
    uni.setNavigationBarTitle({ title: doc.value.title })
  } catch (e) {
    error.value = e.message
  }
})

function play() {
  // #ifdef MP-WEIXIN
  // 小程序的 web-view 只能打开已配置的业务域名，无法内嵌 B 站播放器，改为复制链接
  uni.setClipboardData({ data: webUrl(doc.value.bvid) })
  return
  // #endif
  uni.navigateTo({ url: `/modules/video/pages/player?bvid=${doc.value.bvid}` })
}
</script>

<style scoped>
.cover { position: relative; height: 380rpx; border-radius: 12rpx; background: linear-gradient(135deg, #2b6cb0, #553c9a); display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 20rpx; }
.cover-img { position: absolute; width: 100%; height: 100%; }
.play { position: relative; color: #fff; font-size: 96rpx; }
.title { font-size: 36rpx; font-weight: 600; }
.desc { margin-top: 16rpx; color: #555; }
</style>
