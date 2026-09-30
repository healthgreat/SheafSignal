import { defineConfig } from 'vite'
import uniPlugin from '@dcloudio/vite-plugin-uni'

// 本项目 package.json 声明了 "type": "module"，而 vite-plugin-uni 是 CommonJS 包，
// 它的导出会挂在 default 上，这里做一次兼容。
const uni = uniPlugin.default || uniPlugin

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [uni()],
})
