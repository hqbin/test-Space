import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      vue(),
      // 打包分析工具
      visualizer({
        open: mode === 'production',
        filename: 'dist/stats.html'
      }),
      // PWA 已移除 — 内网部署场景下 SW 缓存弊大于利
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        'lodash': 'lodash-es'
      }
    },
    server: {
      port: parseInt(env.VITE_APP_PORT || '2026'),
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://localhost:8080',
          changeOrigin: true,
          // 转发真实客户端IP到后端
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq, req) => {
              const clientIp = req.socket.remoteAddress || ''
              // 将IPv6格式的IPv4地址转换为标准IPv4
              const ip = clientIp.replace(/^::ffff:/, '')
              proxyReq.setHeader('X-Forwarded-For', ip)
              proxyReq.setHeader('X-Real-IP', ip)
            })
          }
        },
        '/ws': {
          target: 'http://localhost:8080',
          changeOrigin: true,
          ws: true
        }
      }
    },
    preview: {
      port: parseInt(env.VITE_APP_PORT || '2026'),
      host: '0.0.0.0'
    },
    // 性能优化配置
    build: {
      // 启用代码分割
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('@element-plus/icons-vue')) {
                return 'element-plus-icons'
              }
              if (id.includes('element-plus')) {
                return 'element-plus'
              }
              if (id.includes('vue-i18n')) {
                return 'vue-i18n'
              }
              if (id.includes('vue') || id.includes('vue-router') || id.includes('pinia') || id.includes('@vue')) {
                return 'vue-vendor'
              }
              if (id.includes('axios')) {
                return 'axios'
              }
              if (id.includes('lodash')) {
                return 'lodash'
              }
            }
          },
          // 更优的代码分割策略
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
        }
      },
      // 压缩配置
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: mode === 'production', // 生产环境移除console
          drop_debugger: true,
          // 更高级的压缩选项
          pure_funcs: ['console.log', 'console.warn', 'console.error'],
          collapse_vars: true,
          reduce_vars: true
        },
        mangle: {
          toplevel: true,
          safari10: true
        }
      },
      // chunk 大小警告限制
      chunkSizeWarningLimit: 500,
      // 生成源映射
      sourcemap: mode !== 'production',
      // 启用CSS代码分割
      cssCodeSplit: true,
      // 预加载
      preload: true,
      // 预缓存
      manifest: true
    },
    // 优化依赖预构建
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'axios', 'element-plus', '@element-plus/icons-vue', 'vue-i18n', 'lodash-es'],
      // 强制预构建
      force: mode === 'production'
    },
    // 开发服务器优化
    dev: {
      // 启用热更新
      hmr: true,
      // 禁用文件系统缓存
      cacheDir: false
    }
  }
})
