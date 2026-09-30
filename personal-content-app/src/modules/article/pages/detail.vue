<template>
  <view v-if="doc">
    <view class="card">
      <view class="title">{{ doc.title }}</view>
      <view class="muted">{{ formatDate(doc.publish_date) }}</view>
      <rich-text class="content" :nodes="doc.content" />
    </view>
    <!-- 扩展插槽：点赞、评论等由各自模块插入；卸载模块后这里自动消失 -->
    <ContentFooterSlot target-type="article" :target-id="doc._id" />
  </view>
  <view v-else-if="error" class="empty">{{ error }}</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, formatDate } from '@/core'
import ContentFooterSlot from '@/generated/slots/ContentFooterSlot.vue'

const doc = ref(null)
const error = ref('')

onLoad(async ({ id }) => {
  try {
    doc.value = await api.call('article', 'get', { id })
    uni.setNavigationBarTitle({ title: doc.value.title })
  } catch (e) {
    error.value = e.message
  }
})
</script>

<style scoped>
.title { font-size: 40rpx; font-weight: 600; margin-bottom: 8rpx; }
.content { display: block; margin-top: 24rpx; font-size: 32rpx; line-height: 1.8; }
</style>
