import axios from 'axios'
import { ElMessage } from 'element-plus'
import { debounce } from 'lodash-es'
import { generateSign } from '@/utils/sign'

// 请求缓存键生成函数（暂时禁用缓存）
// const generateCacheKey = (config) => {
//   const { method, url, params, data } = config
//   return `${method}:${url}:${JSON.stringify(params || {})}:${JSON.stringify(data || {})}`
// }

// 批量请求队列
const requestQueue = new Map()

// 请求重试配置
const MAX_RETRIES = 1
const RETRY_DELAY = 800

// ===== Token 滑动续期相关 =====
// 剩余有效期小于此阈值时主动续签（毫秒）。默认 1 天。
const REFRESH_THRESHOLD_MS = 24 * 60 * 60 * 1000
// 单飞：同一时刻只发一次 refresh，其它请求复用此 Promise
let refreshingPromise = null

// 解析 JWT 的过期时间戳（秒），失败返回 0
function getTokenExp(token) {
  if (!token) return 0
  try {
    const payload = token.split('.')[1]
    if (!payload) return 0
    const json = JSON.parse(
      decodeURIComponent(
        atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
    )
    return Number(json.exp || 0)
  } catch (e) {
    return 0
  }
}

// 调用刷新接口；成功后写回 localStorage 并返回新 token
function doRefresh(reason = 'unknown') {
  if (refreshingPromise) return refreshingPromise
  const oldToken = localStorage.getItem('token')
  if (!oldToken) return Promise.reject(new Error('no token'))
  if (import.meta.env.DEV) {
    console.log(`[auth] 触发 token 续签，原因: ${reason}`)
  }
  refreshingPromise = axios({
    url: '/api/auth/refresh',
    method: 'post',
    headers: { Authorization: `Bearer ${oldToken}` },
    timeout: 10000
  })
    .then(resp => {
      const newToken = resp?.data?.data?.token
      if (newToken) {
        localStorage.setItem('token', newToken)
        if (import.meta.env.DEV) {
          try {
            const exp = JSON.parse(atob(newToken.split('.')[1])).exp
            console.log('[auth] 续签成功，新过期时间:', new Date(exp * 1000).toLocaleString())
          } catch (_) { /* ignore */ }
        }
        return newToken
      }
      throw new Error('refresh response missing token')
    })
    .finally(() => {
      refreshingPromise = null
    })
  return refreshingPromise
}

const request = axios.create({
  baseURL: '/api',
  timeout: 15000  // 15秒超时，减少长时间挂起对页面切换的影响
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 确保config存在
    if (!config) {
      return Promise.reject(new Error('请求配置不能为空'))
    }
    
    // 确保method存在且为字符串
    if (!config.method) {
      config.method = 'get'
    } else if (typeof config.method !== 'string') {
      config.method = String(config.method)
    }
    
    // 确保headers存在
    if (!config.headers) {
      config.headers = {}
    }

    // 添加token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`

      // 滑动续期：token 即将过期时，后台静默换新（不阻塞当前请求）
      // 跳过续签请求和登录/登出请求，避免循环
      const url = config.url || ''
      const skipRefreshCheck =
        config._isRefresh ||
        url.includes('/auth/login') ||
        url.includes('/auth/logout') ||
        url.includes('/auth/refresh')
      if (!skipRefreshCheck) {
        const exp = getTokenExp(token)
        if (exp > 0) {
          const remainMs = exp * 1000 - Date.now()
          // 剩余 < 阈值 且 未过期 时触发续签
          if (remainMs > 0 && remainMs < REFRESH_THRESHOLD_MS) {
            // 静默触发，不等待结果
            doRefresh('剩余有效期不足').catch(() => { /* 静默失败，由 401 兜底 */ })
          }
        }
      }
    }

    // 添加请求签名
    const signKey = localStorage.getItem('signKey')
    if (signKey && config.url) {
      const path = config.url.startsWith('/') ? config.url : '/' + config.url
      const { timestamp, nonce, sign } = generateSign(path, signKey)
      config.headers['X-Timestamp'] = timestamp
      config.headers['X-Nonce'] = nonce
      config.headers['X-Sign'] = sign
    }

    // 检查缓存 - 暂时禁用缓存，避免localforage的问题
    /*
    if (config.method.toLowerCase() === 'get' && config.cache !== false) {
      const cacheKey = generateCacheKey(config)
      try {
        const cachedData = await localforage.getItem(cacheKey)
        if (cachedData) {
          return Promise.resolve({ data: cachedData })
        }
      } catch (error) {
        console.warn('缓存读取失败:', error)
      }
    }
    */

    // 批量请求处理 — 使用 Promise 去重，同一请求只发一次
    if (config.batch) {
      const batchKey = `${config.method}:${config.url}`
      if (requestQueue.has(batchKey)) {
        return requestQueue.get(batchKey)
      }
      
      const pending = axios({ ...config, batch: undefined }).finally(() => {
        requestQueue.delete(batchKey)
      })
      requestQueue.set(batchKey, pending)
      return pending
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    const config = response.config

    // 缓存成功的GET请求 - 暂时禁用缓存，避免localforage的问题
    /*
    if (config && config.method && config.method.toLowerCase() === 'get' && config.cache !== false && res.code === 200) {
      const cacheKey = generateCacheKey(config)
      
      // 修复localforage.setItem的使用方式
      localforage.setItem(cacheKey, res)
        .then(() => {
          // 缓存成功
        })
        .catch(error => {
          console.warn('缓存写入失败:', error)
        })
    }
    */

    if (response.config && response.config.responseType === 'blob') {
      return response
    }
    if (res.code !== 200) {
      // 409 冲突需要返回给调用者处理，不要拦截
      if (res.code === 409) {
        return res
      }
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  async error => {
    const config = error.config

    // 请求重试机制 - 仅对网络错误重试1次，快速失败
    if (config && !error.response && !error.code?.includes('TIMEOUT') && !error.message?.includes('timeout') && (config.retries || 0) < MAX_RETRIES) {
      config.retries = (config.retries || 0) + 1
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY))
      return request(config)
    }

    // 如果是登录接口的401错误，不自动跳转，让登录页面处理
    const isLoginRequest = config && config.url && config.url.includes('/auth/login')
    
    if (error.response) {
      const status = error.response.status
      const detail = error.response.data?.detail || error.response.data?.message
      
      if (status === 401) {
        if (isLoginRequest) {
          // 登录接口的401错误，显示具体错误信息
          ElMessage.error(detail || '用户名或密码错误')
        } else if (config && config._isRefresh) {
          // 续签自身 401：refresh token 已失效，正常踢出登录
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          const currentPath = window.location.pathname + window.location.search
          const redirect = currentPath && currentPath !== '/login' ? `?redirect=${encodeURIComponent(currentPath)}` : ''
          window.location.href = '/login' + redirect
        } else if (config && !config._retriedAfterRefresh && localStorage.getItem('token')) {
          // 其他接口 401 兜底：尝试静默续签，成功则用新 token 重试一次原请求
          config._retriedAfterRefresh = true
          try {
            const newToken = await doRefresh('收到 401')
            if (newToken) {
              if (!config.headers) config.headers = {}
              config.headers.Authorization = `Bearer ${newToken}`
              return request(config)
            }
          } catch (e) {
            // 续签失败，走默认踢出流程
          }
          ElMessage.error('未登录或登录已过期')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          const currentPath = window.location.pathname + window.location.search
          const redirect = currentPath && currentPath !== '/login' ? `?redirect=${encodeURIComponent(currentPath)}` : ''
          window.location.href = '/login' + redirect
        } else {
          // 已重试过一次或本来就没有token，直接踢出
          ElMessage.error('未登录或登录已过期')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          const currentPath = window.location.pathname + window.location.search
          const redirect = currentPath && currentPath !== '/login' ? `?redirect=${encodeURIComponent(currentPath)}` : ''
          window.location.href = '/login' + redirect
        }
      } else if (status === 429) {
        // 429 登录锁定
        ElMessage.error(detail || '操作过于频繁，请稍后重试')
      } else if (status === 403) {
        // 403 禁止访问
        ElMessage.error(detail || '没有权限访问')
      } else if (status === 400) {
        // 400 错误显示具体错误信息
        ElMessage.error(detail || '请求参数错误')
      } else if (status === 404) {
        // 404 错误
        ElMessage.error(detail || '请求的资源不存在')
      } else if (status >= 500) {
        // 服务器错误
        ElMessage.error(detail || '服务器错误，请稍后重试')
      } else {
        // 其他错误
        ElMessage.error(detail || error.message || '请求失败')
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        if (!config?.skipErrorToast) {
          ElMessage.error('请求超时，请稍后重试')
        }
      } else {
        ElMessage.error('网络连接失败，请检查网络')
      }
    } else {
      // 其他错误
      ElMessage.error(error.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

// 清除缓存的方法（暂时禁用）
export const clearCache = async () => {
  // localforage cache disabled
}

// 防抖请求方法
export const debouncedRequest = debounce((config) => {
  return request(config)
}, 300)

// 批量请求方法
export const batchRequest = (config) => {
  return request({ ...config, batch: true })
}

export default request
