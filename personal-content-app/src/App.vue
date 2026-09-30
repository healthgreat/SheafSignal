<script>
import { SETUPS } from './generated/setups.js'

export default {
  async onLaunch() {
    // 依次执行各模块的启动钩子；某个模块出错不影响其他模块
    for (const { id, run } of SETUPS) {
      try {
        await run()
      } catch (e) {
        console.error(`[setup] 模块 ${id} 启动失败`, e)
      }
    }
  },
}
</script>

<style>
page {
  background-color: #f6f6f6;
  color: #222;
  font-size: 30rpx;
  line-height: 1.6;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  margin: 24rpx;
  padding: 28rpx;
}
.muted {
  color: #8a8a8a;
  font-size: 24rpx;
}
.empty {
  text-align: center;
  color: #aaa;
  padding: 80rpx 0;
}
.btn-primary {
  background: #2b6cb0;
  color: #fff;
  border-radius: 12rpx;
  font-size: 30rpx;
}
.btn-primary[disabled] {
  background: #9dbbdc;
  color: #fff;
}
</style>
