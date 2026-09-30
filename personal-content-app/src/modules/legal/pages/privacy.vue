<template>
  <view class="card legal">
    <view class="h1">隐私政策</view>
    <view class="muted">更新日期：请填写 · 生效日期：请填写</view>
    <view class="warn">⚠️ 这是模板，上架前必须根据实际情况修改，并建议请专业人士审阅。</view>

    <view class="h2">一、我们收集哪些信息</view>
    <!-- 下面的条款会根据当前启用的模块自动显示或隐藏，保证隐私政策与实际功能一致 -->
    <view class="p">· 浏览文章和视频：不需要注册，不收集你的个人身份信息。</view>
    <view v-if="has('like')" class="p">· 点赞：为防止重复点赞，会使用设备标识（deviceId）进行去重，不与你的身份关联。</view>
    <view v-if="has('auth')" class="p">· 登录：使用手机号和短信验证码登录，手机号用于身份验证。</view>
    <view v-if="has('comment')" class="p">· 发表评论：依据《互联网跟帖评论服务管理规定》，需要验证手机号（后台实名）；页面上只显示你自行填写的昵称。</view>

    <view class="h2">二、信息如何使用和保存</view>
    <view v-if="has('auth')" class="p">手机号仅用于身份验证，不会公开展示，也不会提供给第三方（法律法规另有规定的除外）。</view>
    <view class="p">数据存储于中国境内的云服务器。</view>

    <view class="h2">三、第三方服务</view>
    <view class="p">· uniCloud（DCloud）：提供云数据库{{ has('auth') ? '与短信验证' : '' }}服务。</view>
    <view v-if="has('video')" class="p">· 哔哩哔哩：视频由哔哩哔哩播放器提供，播放时适用其隐私政策。</view>

    <view class="h2">四、你的权利</view>
    <view v-if="has('auth')" class="p">你可以随时删除自己的评论，或联系我们注销账号、删除个人信息。</view>
    <view v-else class="p">本应用不要求注册账号。如对点赞记录等数据有疑问，可以联系我们删除。</view>

    <view class="h2">五、联系我们</view>
    <view class="p">邮箱：请填写</view>
  </view>
</template>

<script setup>
import { registry } from '@/core'

const has = (id) => registry.isEnabled(id)
</script>

<style scoped>
.legal .h1 { font-size: 40rpx; font-weight: 600; margin-bottom: 8rpx; }
.legal .h2 { font-size: 32rpx; font-weight: 600; margin-top: 32rpx; }
.legal .p { margin-top: 12rpx; }
.legal .warn { margin-top: 16rpx; padding: 16rpx; background: #fff7e6; color: #ad6800; border-radius: 8rpx; font-size: 26rpx; }
</style>
