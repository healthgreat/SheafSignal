<template>
  <!-- web-view 会铺满整个页面，嵌入 B 站官方外链播放器 -->
  <web-view v-if="src" :src="src" />
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { playerUrl } from '../format.js'

const src = ref('')
onLoad(({ bvid }) => {
  src.value = playerUrl(bvid)
})
</script>
