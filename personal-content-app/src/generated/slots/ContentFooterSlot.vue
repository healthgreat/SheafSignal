<!-- 自动生成：插槽 "content-footer"（文章/视频详情页底部（点赞、评论等互动功能））。请勿手改，运行 npm run gen 重新生成。 -->
<template>
  <view class="ext-slot ext-slot--content-footer">
    <LikeLikeButton :target-type="targetType" :target-id="targetId" />
  </view>
</template>

<script setup>
import LikeLikeButton from '@/modules/like/components/LikeButton.vue'

defineProps({
  targetType: { type: String, required: true },
  targetId: { type: String, required: true },
})
</script>
