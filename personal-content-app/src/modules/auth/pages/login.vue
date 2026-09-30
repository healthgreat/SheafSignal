<template>
  <view class="card">
    <view class="title">手机号登录</view>
    <view class="muted">依据相关规定，发表评论需要验证手机号。页面上只显示你自己填写的昵称。</view>

    <input class="field" type="number" maxlength="11" v-model="mobile" placeholder="手机号" />

    <view v-if="captchaImg" class="row">
      <input class="field grow" maxlength="4" v-model="captcha" placeholder="图形验证码" />
      <image class="captcha" :src="captchaImg" mode="aspectFit" @tap="loadCaptcha" />
    </view>

    <view class="row">
      <input class="field grow" type="number" maxlength="6" v-model="code" placeholder="短信验证码" />
      <button class="send" size="mini" :disabled="countdown > 0 || sending" @tap="sendCode">
        {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
      </button>
    </view>
    <view v-if="hint" class="muted">{{ hint }}</view>

    <view class="agree" @tap="agreed = !agreed">
      <view class="box" :class="{ checked: agreed }">{{ agreed ? '✓' : '' }}</view>
      <text>我已阅读并同意</text>
      <text class="link" @tap.stop="open('termsPage')">《服务协议》</text>
      <text>和</text>
      <text class="link" @tap.stop="open('privacyPage')">《隐私政策》</text>
    </view>

    <button class="btn-primary" :disabled="!canSubmit || submitting" @tap="submit">登录</button>
  </view>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { session, registry, toastError } from '@/core'
import { authService } from '../service.js'

const mobile = ref('')
const captcha = ref('')
const captchaImg = ref(null)
const code = ref('')
const hint = ref('')
const agreed = ref(false)
const countdown = ref(0)
const sending = ref(false)
const submitting = ref(false)
let timer = null

const validMobile = computed(() => /^1\d{10}$/.test(mobile.value))
const canSubmit = computed(() => validMobile.value && /^\d{4,6}$/.test(code.value) && agreed.value)

async function loadCaptcha() {
  try {
    captchaImg.value = await authService.createCaptcha()
  } catch (e) {
    toastError(e)
  }
}

onLoad(loadCaptcha)
onUnmounted(() => clearInterval(timer))

function open(capability) {
  const url = registry.capability(capability)
  if (url) uni.navigateTo({ url })
}

async function sendCode() {
  if (!validMobile.value) return uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
  if (captchaImg.value && !captcha.value) return uni.showToast({ title: '请输入图形验证码', icon: 'none' })
  sending.value = true
  try {
    const res = await authService.sendCode(mobile.value, captcha.value)
    hint.value = res?.hint || '验证码已发送'
    countdown.value = 60
    timer = setInterval(() => {
      if (--countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    toastError(e)
    if (captchaImg.value) loadCaptcha()
  } finally {
    sending.value = false
  }
}

async function submit() {
  submitting.value = true
  try {
    await authService.login(mobile.value, code.value)
    await session.refresh()
    uni.showToast({ title: '登录成功' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    toastError(e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.title { font-size: 40rpx; font-weight: 600; margin-bottom: 8rpx; }
.field { border-bottom: 1rpx solid #eee; padding: 20rpx 0; margin-top: 24rpx; }
.row { display: flex; align-items: center; gap: 16rpx; }
.grow { flex: 1; }
.captcha { width: 200rpx; height: 72rpx; margin-top: 24rpx; }
.send { margin-top: 24rpx; }
.agree { display: flex; flex-wrap: wrap; align-items: center; font-size: 24rpx; margin: 32rpx 0; color: #666; }
.link { color: #2b6cb0; }
.box { width: 32rpx; height: 32rpx; border: 2rpx solid #bbb; border-radius: 6rpx; margin-right: 12rpx; font-size: 24rpx; line-height: 32rpx; text-align: center; color: #fff; }
.box.checked { background: #2b6cb0; border-color: #2b6cb0; }
</style>
