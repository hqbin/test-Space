/**
 * SSP 后台接口客户端
 * 只依赖 HTTP 接口，不使用页面自动化。
 */
import * as db from '@/services/database'

export type SspEnv = 'acc' | 'prod'

export const SSP_BASE: Record<SspEnv, string> = {
  acc: 'https://sspportal-acc.zeasn.tv',
  prod: 'https://sspportal.zeasn.tv',
}

export const SSP_SETTINGS = {
  env: 'ssp.env',
  /** 旧版本单份账号，仅用于迁移到 acc 账号槽 */
  email: 'ssp.email',
  password: 'ssp.password',
  remember: 'ssp.remember_password',
  // 会话快照：热更新 / 重启后据此恢复登录态，避免被踢回登录页
  sessionEnv: 'ssp.session_env',
  sessionUser: 'ssp.session_user',
  sessionCookie: 'ssp.session_cookie',
} as const

let currentEnv: SspEnv = 'acc'
let sessionId = ''
let loginUser = ''
/**
 * 登录成功的判定不再只看有没有抓到 PHPSESSID。
 * Tauri 的 http 插件自带持久化 Cookie 罐，服务端在已有会话时不会重复下发 Set-Cookie，
 * 此时 Cookie 罐里的会话仍然有效，必须用受保护接口探活来确认。
 */
let loggedIn = false
/** 串行化探活，避免多个入口同时请求 */
let probing: Promise<boolean> | null = null

let _fetch: typeof fetch | null = null
async function getFetch(): Promise<typeof fetch> {
  if (_fetch) return _fetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    _fetch = mod.fetch as typeof fetch
  } catch {
    _fetch = fetch
  }
  return _fetch!
}

function baseUrl(): string {
  return SSP_BASE[currentEnv]
}

function captureSession(res: Response) {
  try {
    const headers = res.headers as any
    const list: string[] = headers?.getSetCookie?.() ?? []
    const raw = list.length > 0 ? list.join('\n') : (res.headers.get('set-cookie') || '')
    const m = raw.match(/PHPSESSID=([^;,\s]+)/i)
    if (m) sessionId = m[1]
  } catch {
    // 浏览器环境拿不到 Set-Cookie 时忽略
  }
  if (!sessionId && typeof document !== 'undefined') {
    const m = document.cookie.match(/PHPSESSID=([^;,\s]+)/i)
    if (m) sessionId = m[1]
  }
}

function encodeNested(usp: URLSearchParams, key: string, value: any) {
  if (value === undefined || value === null) return
  if (Array.isArray(value)) {
    value.forEach((v) => encodeNested(usp, `${key}[]`, v))
    return
  }
  if (typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) encodeNested(usp, `${key}[${k}]`, v)
    return
  }
  usp.append(key, String(value))
}

// 后台页面用 jQuery 提交表单，嵌套对象会被展开为 material[image_1]=xxx 这种形式
// keepEmpty：审核等接口要带空字符串（平台会提交 memo=），默认仍然跳过空值
function encodeParams(params: Record<string, any>, keepEmpty = false): string {
  const usp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    if (value === '' && !keepEmpty) continue
    if (Array.isArray(value) || typeof value === 'object') {
      encodeNested(usp, key, value)
    } else {
      usp.append(key, String(value))
    }
  }
  return usp.toString()
}

async function rawFetch(url: string, init: RequestInit & { timeoutMs?: number; maxRedirections?: number }): Promise<Response> {
  const f = await getFetch()
  const { timeoutMs, maxRedirections, ...rest } = init
  const controller = new AbortController()
  const timer = timeoutMs ? window.setTimeout(() => controller.abort(), timeoutMs) : null
  try {
    return await f(url, { ...rest, maxRedirections, signal: controller.signal } as any)
  } finally {
    if (timer) window.clearTimeout(timer)
  }
}

async function parseResponse(res: Response): Promise<any> {
  const text = await res.text()
  let json: any
  try {
    json = JSON.parse(text)
  } catch {
    throw new Error(`接口返回非 JSON (HTTP ${res.status})`)
  }
  if (json?.return_code !== 0) {
    const msg = typeof json?.return_msg === 'string' ? json.return_msg : json?.return_msg?.msg
    throw new Error(msg || `接口错误 (${json?.return_code})`)
  }
  return json.return_msg
}

async function apiPost(path: string, params: Record<string, any> = {}, keepEmpty = false): Promise<any> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
  }
  if (sessionId) headers.Cookie = `PHPSESSID=${sessionId}`
  const res = await rawFetch(baseUrl() + path, {
    method: 'POST',
    headers,
    body: encodeParams(params, keepEmpty),
    credentials: 'include',
    timeoutMs: 30000,
  })
  captureSession(res)
  return parseResponse(res)
}

export function getSspEnv(): SspEnv {
  return currentEnv
}

export function getLoginUser(): string {
  return loginUser
}

export function isSspLoggedIn(): boolean {
  return loggedIn
}

/** 清空内存中的会话状态（不落库） */
function resetSessionState() {
  sessionId = ''
  loginUser = ''
  loggedIn = false
  invalidateAdTypes()
  // 定向规则（Custom engine）全量缓存也要清：切环境 / 重新登录后 id 会对不上，回显会变空
  invalidateKeywords()
}

/** 用受保护接口探活：Cookie 罐持有有效会话时即使没抓到 Set-Cookie 也能判定为已登录 */
async function probeSession(): Promise<boolean> {
  if (probing) return probing
  probing = (async () => {
    if (await tryProbe()) return true
    // 显式 Cookie 可能是旧的（服务端轮换过 session id），交给插件 Cookie 罐再试一次
    if (sessionId) {
      sessionId = ''
      if (await tryProbe()) return true
    }
    return false
  })()
  try {
    return await probing
  } finally {
    probing = null
  }
}

async function tryProbe(): Promise<boolean> {
  try {
    const res = await apiPost('/ssp/app/list', paging({ page: 1, size: 1 }))
    return Array.isArray(res?.records)
  } catch {
    return false
  }
}

/** 持久化当前会话，热更新 / 重启后可恢复 */
async function persistSession() {
  try {
    await Promise.all([
      db.setSetting(SSP_SETTINGS.sessionEnv, currentEnv),
      db.setSetting(SSP_SETTINGS.sessionUser, loginUser),
      db.setSetting(SSP_SETTINGS.sessionCookie, sessionId),
    ])
  } catch {
    // 落库失败不影响本次使用
  }
}

/** 清除持久化的会话快照 */
export async function clearSspSession(): Promise<void> {
  try {
    await Promise.all([
      db.setSetting(SSP_SETTINGS.sessionEnv, ''),
      db.setSetting(SSP_SETTINGS.sessionUser, ''),
      db.setSetting(SSP_SETTINGS.sessionCookie, ''),
    ])
  } catch {
    // 忽略
  }
}

export async function sspLogout() {
  resetSessionState()
  await clearSspSession()
}

/**
 * 启动 / 热更新后恢复会话：
 * 1. 读回上次的环境、账号、PHPSESSID；
 * 2. 用受保护接口探活 —— 有效就直接进入已登录态，无效则回登录页。
 */
export async function restoreSspSession(): Promise<{ env: SspEnv; email: string } | null> {
  const [env, user, cookie] = await Promise.all([
    db.getSetting(SSP_SETTINGS.sessionEnv),
    db.getSetting(SSP_SETTINGS.sessionUser),
    db.getSetting(SSP_SETTINGS.sessionCookie),
  ])
  if (!user) return null
  currentEnv = env === 'prod' ? 'prod' : 'acc'
  sessionId = cookie || ''
  invalidateAdTypes()
  const ok = await probeSession()
  if (!ok) {
    resetSessionState()
    return null
  }
  loginUser = user
  loggedIn = true
  // 保存探测后真正生效的 Cookie 值（可能已改为交给插件 Cookie 罐）
  await persistSession()
  return { env: currentEnv, email: user }
}

export async function sspLogin(env: SspEnv, email: string, password: string): Promise<void> {
  currentEnv = env
  resetSessionState()
  // 先访问登录页，让服务端下发会话；不跟随 302，才能拿到 Set-Cookie
  try {
    const res = await rawFetch(baseUrl() + '/ssp/pages/login', {
      method: 'GET',
      credentials: 'include',
      maxRedirections: 0,
      timeoutMs: 20000,
    })
    captureSession(res)
  } catch {
    // 忽略，登录接口仍可建立会话
  }
  const res = await rawFetch(baseUrl() + '/ssp/login/signin', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest',
      ...(sessionId ? { Cookie: `PHPSESSID=${sessionId}` } : {}),
    },
    body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
    credentials: 'include',
    timeoutMs: 20000,
  })
  captureSession(res)
  const data = await parseResponse(res)
  if (!sessionId && typeof data?.sessionid === 'string') sessionId = data.sessionid
  /**
   * 没抓到 Set-Cookie 不等于登录失败：
   * Cookie 罐里可能已经带着本域的 PHPSESSID，服务端会复用该会话而不重新下发 Cookie。
   * 这种情况用受保护接口验证一次即可。
   */
  if (!sessionId) {
    const ok = await probeSession()
    if (!ok) throw new Error('登录成功但未获取到会话（Cookie）')
  }
  loggedIn = true
  loginUser = email
  await persistSession()
}

// ── 媒体 / 广告位 / 广告 ─────────────────────────────────────────

export interface SspMedia {
  id: string
  name: string
  ad_zone?: number
  status?: string
  [key: string]: any
}

export interface SspZone {
  id: string
  name: string
  appid?: string
  ad_type?: string
  ad_type_id?: string
  description?: string
  screen?: string
  [key: string]: any
}

export interface SspOrder {
  id: string
  name: string
  campaign_id?: string
  campaign_name?: string
  ad_type?: string
  material?: string
  files?: any
  click_url?: string
  target_app?: string
  target_plat?: string
  locids?: string
  locids_text?: string
  begin_date?: string
  end_date?: string
  status?: string
  verify_status?: string
  verify_reason?: string
  target_keyword?: string
  cam_target_keyword?: string
  [key: string]: any
}

export interface SspPageResult<T> {
  total: number
  records: T[]
}

/**
 * 后台分页参数名是 `size`，`pagesize` 会被后端直接忽略（不传 size 时返回全量）。
 * 这里统一把 pagesize 归一化为 size，避免「每页条数」和翻页失效。
 */
function paging(params: Record<string, any> = {}): Record<string, any> {
  const out: Record<string, any> = { ...params }
  const size = out.pagesize ?? out.size
  delete out.pagesize
  if (size !== undefined && size !== null && size !== '') out.size = size
  return out
}

export async function listMedias(params: { name?: string; page?: number; pagesize?: number } = {}): Promise<SspPageResult<SspMedia>> {
  const size = Number(params.pagesize ?? 200) || 200
  const all: SspMedia[] = []
  let total = 0
  let pageNo = 1
  // 逐页拉取：单页上限受后端限制时也能拿到全部媒体，而不是只显示第一页
  for (;;) {
    const res: SspPageResult<SspMedia> = await apiPost('/ssp/app/list', paging({ page: pageNo, size, name: params.name }))
    const recs = res?.records ?? []
    total = Number(res?.total ?? recs.length)
    all.push(...recs)
    if (!recs.length || all.length >= total || pageNo >= 50) break
    pageNo++
  }
  // 后端若忽略 page 会返回重复数据，这里按 id 去重兜底
  const map = new Map<string, SspMedia>()
  for (const m of all) map.set(String(m.id), m)
  const records = Array.from(map.values())
  return { total: Math.max(total, records.length), records }
}

export async function listZones(appid: string): Promise<SspPageResult<SspZone>> {
  const res = await apiPost('/ssp/loc/list', paging({ appid, page: 1, pagesize: 500 }))
  const records: SspZone[] = res?.records ?? []
  // 后端有时忽略 appid 直接返回全量广告位，这里按 appid 兜底过滤，避免出现其它媒体的广告位
  const scoped = records.filter((z) => {
    const a = z?.appid
    return a === undefined || a === null || a === '' || String(a) === String(appid)
  })
  const hasAppScope = scoped.length !== records.length
  if (hasAppScope) return { total: scoped.length, records: scoped }
  return { total: Number(res?.total ?? records.length), records }
}

/** 后端把 total 等分页字段返回成字符串，统一归一化成数字，避免调用方直接比较时出错 */
function normalizePage<T>(res: any): SspPageResult<T> {
  const records: T[] = Array.isArray(res?.records) ? res.records : []
  const total = Number(res?.total)
  return { total: Number.isFinite(total) ? total : records.length, records }
}

export async function listOrders(params: Record<string, any> = {}): Promise<SspPageResult<SspOrder>> {
  return normalizePage<SspOrder>(await apiPost('/ssp/order/list', paging({ page: 1, pagesize: 50, ...params })))
}

export async function getOrder(id: string): Promise<SspOrder | null> {
  const res = await listOrders({ id, page: 1, pagesize: 1 })
  return res.records?.[0] ?? null
}

export interface SspKeyword {
  id: string
  keycode?: string
  keytext?: string
  valuecode?: string[] | string
  valuetext?: string
  name?: string
  enable?: string
  order_count?: string
  matching?: string
  looklike?: string
  keywordtype?: string
  keywordop?: string
  type?: string
  [key: string]: any
}

export interface SspKeywordPage extends SspPageResult<SspKeyword> {}
export interface SspKeywordQuery {
  /** 按标签值搜索（MAC 等），后端是按 valuecode 模糊匹配 */
  value?: string
  /** 按标签说明 / 标签值说明搜索 */
  name?: string
  page?: number
  pagesize?: number
}

export async function listKeywords(params: SspKeywordQuery = {}): Promise<SspKeywordPage> {
  const res = await apiPost('/ssp/keyword/list', paging({ page: 1, pagesize: 100, ...params }))
  return { total: Number(res?.total ?? (res?.records?.length || 0)), records: res?.records ?? [] }
}

export async function searchKeywords(value: string): Promise<SspKeyword[]> {
  const res = await listKeywords({ value, page: 1, pagesize: 50 })
  return res.records
}

/** 全量规则缓存：编辑广告时把 target_keyword 的 id 还原成可读名称 */
let allKeywordsCache: SspKeyword[] | null = null

export function invalidateKeywords() {
  allKeywordsCache = null
}

export async function listAllKeywords(force = false): Promise<SspKeyword[]> {
  if (allKeywordsCache && !force) return allKeywordsCache
  const all: SspKeyword[] = []
  let pageNo = 1
  for (;;) {
    const res = await listKeywords({ page: pageNo, pagesize: 500 })
    all.push(...res.records)
    if (!res.records.length || all.length >= res.total || pageNo >= 20) break
    pageNo++
  }
  const map = new Map<string, SspKeyword>()
  all.forEach((k) => map.set(String(k.id), k))
  allKeywordsCache = Array.from(map.values())
  return allKeywordsCache
}

export async function keywordsByIds(ids: string[], force = false): Promise<SspKeyword[]> {
  if (!ids.length) return []
  let all = await listAllKeywords(force)
  let map = new Map(all.map((k) => [String(k.id), k]))
  // 有 id 在缓存里找不到（新建规则后没刷新 / 切过环境）时，强制重拉一次再匹配
  if (ids.some((id) => !map.has(String(id)))) {
    all = await listAllKeywords(true)
    map = new Map(all.map((k) => [String(k.id), k]))
  }
  return ids.map((id) => map.get(String(id))).filter(Boolean) as SspKeyword[]
}

export interface NewKeywordInput {
  /** 编辑时传已有 id，新建传 0 / 留空 */
  id?: string | number
  /** 标签参数，如 mac / devicemac */
  keycode: string
  /** 标签说明 */
  keytext: string
  /** 规则值（多个用逗号分隔） */
  valuecode: string
  /** 值说明 */
  valuetext: string
  /** 匹配方式：0 精确 / 1 模糊 */
  looklike?: 0 | 1
  /** 值类型：1 数字 / 2 字符 */
  keywordtype?: string
  /** 匹配操作符（后台默认 1） */
  keywordop?: string
}

/**
 * 新建 / 修改定向规则（Custom engine）。
 * 字段与后台 `/ssp/pages/keywordadd` 的 COND 结构一致，接口为 `/ssp/keyword/add`，
 * 带 id 即为修改。
 */
export async function saveKeyword(input: NewKeywordInput): Promise<void> {
  await apiPost('/ssp/keyword/add', {
    id: input.id ?? 0,
    keycode: input.keycode.trim(),
    keytext: input.keytext.trim(),
    valuecode: input.valuecode.trim(),
    valuetext: input.valuetext.trim(),
    looklike: input.looklike ?? 0,
    keywordtype: input.keywordtype || '2',
    keywordop: input.keywordop || '1',
  })
  invalidateKeywords()
}

export async function createKeyword(input: NewKeywordInput): Promise<void> {
  await saveKeyword({ ...input, id: 0 })
}

/** 删除定向规则（Custom engine） */
export async function deleteKeyword(id: string): Promise<void> {
  await apiPost('/ssp/keyword/delete', { id })
  invalidateKeywords()
}

// ── 写操作 ─────────────────────────────────────────────────────

export async function updateOrderAction(id: string, action: 'play' | 'pause' | 'delete'): Promise<void> {
  await apiPost('/ssp/order/opt', { id, action })
}

/** 待审核广告列表（对应后台 Ad verify → Self ad verification） */
export async function listPendingOrders(params: Record<string, any> = {}): Promise<SspPageResult<SspOrder>> {
  return normalizePage<SspOrder>(await apiPost('/ssp/order/checklist', paging({ page: 1, pagesize: 100, ...params })))
}

export async function verifyOrder(id: string, action: 'play' | 'reject', memo = ''): Promise<void> {
  // 平台提交时会带 memo（哪怕是空串），这里保持一致，避免审核动作被后端判为缺参
  await apiPost('/ssp/order/checkopt', { id, action, memo }, true)
}

export interface SspUploadedFile {
  file_id: string
  file_path: string
}

export async function uploadMaterial(file: File, plat: string): Promise<SspUploadedFile> {
  const form = new FormData()
  form.append('file', file)
  form.append('plat', plat || '')
  const headers: Record<string, string> = { 'X-Requested-With': 'XMLHttpRequest' }
  if (sessionId) headers.Cookie = `PHPSESSID=${sessionId}`
  const res = await rawFetch(baseUrl() + '/ssp/order/upload', {
    method: 'POST',
    headers,
    body: form,
    credentials: 'include',
    timeoutMs: 60000,
  })
  captureSession(res)
  const data = await parseResponse(res)
  if (!data?.file_id) throw new Error('上传成功但未返回 file_id')
  return { file_id: String(data.file_id), file_path: String(data.file_path || '') }
}

// 字段结构与后台 orderadd 页面的 COND 保持一致（页面直接回填原记录字段）
function buildOrderCond(order: SspOrder, material: Record<string, any>): Record<string, any> {
  return {
    id: Number(order.id || 0),
    campaign_id: Number(order.campaign_id || 0),
    name: order.name,
    ad_type: order.ad_type,
    material,
    click_url: order.click_url ?? '',
    click_monitor_url: order.click_monitor_url ?? '',
    pv_monitor_url: order.pv_monitor_url ?? '',
    begin_date: order.begin_date,
    end_date: order.end_date,
    price_mode: order.price_mode ?? '',
    cpt_type: order.cpt_type ?? '0',
    count_type: order.count_type ?? 0,
    unit_price: order.unit_price ?? '',
    cpm_percent: order.cpm_percent ?? '',
    max_amount: order.max_amount ?? '',
    class: order.class ?? '',
    total_budget: order.total_budget ?? '',
    day_budget: order.day_budget ?? '',
    extend_target: order.extend_target ?? 0,
    target_area: order.target_area ?? '',
    target_time: order.target_time ?? '',
    target_week: order.target_week ?? '',
    target_nettype: order.target_nettype ?? '',
    target_phone: order.target_phone ?? '',
    target_app: order.target_app ?? '',
    target_audience: order.target_audience ?? '',
    target_os: order.target_os ?? '',
    target_plat: order.target_plat ?? '',
    target_loc: order.locids ?? '',
    target_keyword: order.target_keyword ?? '',
    target_tag: order.target_tag ?? '',
    target_brand_tag: '',
    target_tv_brand: '',
    freq_count: order.freq_count ?? 0,
    freq_period: order.freq_period ?? 0,
    freq_period_count: order.freq_period_count ?? 0,
    freq_flag: order.freq_flag ?? 0,
    play_speed: order.play_speed ?? 0,
    dates: order.dates ?? '',
    weights: order.weights ?? 0,
    monitor_order: order.monitor_order ?? '',
    target_area_type: order.target_area_type ?? 2,
    target_custom: order.target_custom ?? '',
    target_custom_type: order.target_custom_type ?? 0,
    memo: order.memo ?? '',
    disable_adflag: order.disable_adflag ?? '',
    external: order.external ?? '',
    is_google_image_ad: order.is_google_image_ad ?? 0,
    head_script: order.head_script ?? '',
    body_script: order.body_script ?? '',
    industry: order.industry ?? 0,
    macro: order.macro ?? '',
    script_ad: '',
  }
}

/** 修改已有广告的素材内容（仅 ACC 环境使用） */
export async function saveOrderMaterial(order: SspOrder, material: Record<string, any>): Promise<void> {
  const mat = { ...material }
  // 后台页面在非 external 时会清空 ad_format
  if (String(order.external ?? '0') !== '1') mat.ad_format = ''
  await apiPost('/ssp/order/add', buildOrderCond(order, mat))
}

/**
 * 编辑已有广告：以原记录为底，覆盖传入字段后整体提交。
 * 字段名与后台 orderadd 表单保持一致（campaign_id / ad_type / click_url / class / target_app / locids ...）。
 */
export async function updateOrder(order: SspOrder, patch: Record<string, any>): Promise<void> {
  const merged: SspOrder = { ...order, ...patch } as SspOrder
  const mat = { ...parseMaterial(order), ...(patch.material || {}) }
  if (String(merged.external ?? '0') !== '1') mat.ad_format = ''
  await apiPost('/ssp/order/add', buildOrderCond(merged, mat))
}

export function materialPreviewUrl(env: SspEnv, path?: string): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return SSP_BASE[env] + (path.startsWith('/') ? path : `/${path}`)
}

export function parseMaterial(order: SspOrder | null): Record<string, any> {
  if (!order?.material) return {}
  try {
    const obj = JSON.parse(order.material)
    return obj && typeof obj === 'object' ? obj : {}
  } catch {
    return {}
  }
}

export interface SspCredential {
  email: string
  password: string
}

/** 每个环境各存一份账号，切换环境时跟着切账号 */
function credKeys(env: SspEnv) {
  return { email: `ssp.${env}.email`, password: `ssp.${env}.password` }
}

export async function loadSspCredential(env: SspEnv): Promise<SspCredential> {
  const k = credKeys(env)
  const [email, password] = await Promise.all([db.getSetting(k.email), db.getSetting(k.password)])
  return { email: email || '', password: password || '' }
}

export async function saveSspCredential(env: SspEnv, email: string, password: string): Promise<void> {
  const k = credKeys(env)
  await Promise.all([
    db.setSetting(k.email, email),
    db.setSetting(k.password, password),
    db.setSetting(SSP_SETTINGS.env, env),
  ])
}

export async function saveSspEnv(env: SspEnv): Promise<void> {
  try {
    await db.setSetting(SSP_SETTINGS.env, env)
  } catch {
    // 忽略
  }
}

export async function loadSspPrefs(): Promise<{
  env: SspEnv
  accounts: Record<SspEnv, SspCredential>
}> {
  const [env, acc, prod, legacyEmail, legacyPassword] = await Promise.all([
    db.getSetting(SSP_SETTINGS.env),
    loadSspCredential('acc'),
    loadSspCredential('prod'),
    db.getSetting(SSP_SETTINGS.email),
    db.getSetting(SSP_SETTINGS.password),
  ])
  // 旧版本只有一份账号：迁移到 ACC 槽，用户不用重新输一遍
  if (!acc.email && legacyEmail) {
    acc.email = legacyEmail
    acc.password = legacyPassword || ''
    await saveSspCredential('acc', acc.email, acc.password)
  }
  return {
    env: env === 'prod' ? 'prod' : 'acc',
    accounts: { acc, prod },
  }
}


// ── Campaign / 广告主 ─────────────────────────────────────────

export interface SspCampaign {
  id: string
  name: string
  advertiserid?: string
  advname?: string
  status?: string
  Demandpartner?: string
  begin_date?: string
  end_date?: string
  adcount?: string
  [key: string]: any
}

export interface SspAdvertiser {
  id: string
  name: string
  [key: string]: any
}

export async function listCampaigns(): Promise<SspCampaign[]> {
  const res = await apiPost('/ssp/campaign/list', paging({ page: 1, pagesize: 1000 }))
  return res.records ?? []
}

export async function listAdvertisers(): Promise<SspAdvertiser[]> {
  const res = await apiPost('/ssp/advertiser/list', paging({ page: 1, pagesize: 500 }))
  return res.records ?? []
}

export async function campaignAction(id: string, action: 'play' | 'pause' | 'delete'): Promise<void> {
  await apiPost('/ssp/campaign/opt', { id, action })
}

export interface NewCampaignInput {
  name: string
  advertiserid: string
  demandPartner: string
  beginDate: string
  endDate: string
  description?: string
}

/** 返回新建 Campaign 的 id */
export async function createCampaign(input: NewCampaignInput): Promise<string> {
  // 与后台 `campaignadd` 的 COND 完全一致。必须保留空串提交：
  // 缺省的 total_budget / day_budget 会以 NULL 入库，直接触发
  // `Column 'day_budget' cannot be null` 而创建失败。
  const id = await apiPost(
    '/ssp/campaign/add',
    {
      id: 0,
      name: input.name,
      description: input.description ?? '',
      begin_date: input.beginDate,
      end_date: input.endDate,
      total_budget: '',
      rate: 1.0,
      day_budget: '',
      advertiserid: input.advertiserid,
      Demandpartner: input.demandPartner,
      extsn: '',
      target_area: [],
      target_keyword: [],
      target_time: [],
      target_phone: [],
      target_app: [],
      target_os: [],
      target_tag: [],
      target_audience: [],
      target_custom: '',
      freq_count: 0,
      freq_period: 0,
      freq_period_count: 0,
      freq_flag: 0,
      booked_budget: 0,
      target_area_type: 2,
      target_tv_brand: '',
      // 后台从页面变量 typeTab 带入，固定 0（普通 Campaign）
      outdoor_flag: 0,
    },
    true,
  )
  return String(id ?? '')
}

// ── 广告类型（从 orderadd 页面读取） ───────────────────────

export interface SspAdType {
  key: string
  text?: string
  sub_text?: string
  id?: string
  size?: string
  info: Record<string, any>
}

export interface SspDictItem {
  id: string | number
  text: string
}

/** orderadd 页面内联的 `var dict`，包含 ad_format / class / price_mode 等枚举 */
export type SspOrderDict = Record<string, SspDictItem[]>

interface OrderMeta {
  adTypes: SspAdType[]
  dict: SspOrderDict
}

let orderMetaCache: OrderMeta | null = null

/** 会话或环境切换后必须失效，避免沿用上一环境的广告类型字典 */
export function invalidateAdTypes() {
  orderMetaCache = null
}

/**
 * 从 `[` 开始按括号配对截取完整的 JS 字面量（跳过字符串与注释）。
 * orderadd 页面的 `var adtype` 可能是多行格式化输出，不能只截到行尾。
 */
function sliceBalanced(src: string, start: number): string | null {
  let depth = 0
  let quote = ''
  for (let i = start; i < src.length; i++) {
    const ch = src[i]
    if (quote) {
      if (ch === '\\') { i++; continue }
      if (ch === quote) quote = ''
      continue
    }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue }
    if (ch === '/' && src[i + 1] === '/') {
      const nl = src.indexOf('\n', i)
      if (nl < 0) return null
      i = nl
      continue
    }
    if (ch === '/' && src[i + 1] === '*') {
      const end = src.indexOf('*/', i + 2)
      if (end < 0) return null
      i = end + 1
      continue
    }
    if (ch === '[' || ch === '{' || ch === '(') depth++
    else if (ch === ']' || ch === '}' || ch === ')') {
      depth--
      if (depth === 0) return src.slice(start, i + 1)
      if (depth < 0) return null
    }
  }
  return null
}

/** 依次尝试严格 JSON → 去注释/尾逗号 → 单引号 → JS 表达式求值 */
function parseLooseValue<T = any>(raw: string): T {
  try { return JSON.parse(raw) } catch { /* 继续 */ }
  const noComment = raw
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:'"\\])\/\/[^\n]*/g, '$1')
  const noTrailing = noComment.replace(/,\s*([\]}])/g, '$1')
  try { return JSON.parse(noTrailing) } catch { /* 继续 */ }
  try { return JSON.parse(noTrailing.replace(/'/g, '"')) } catch { /* 继续 */ }
  // 页面本身用 JS 字面量声明，兜底按表达式求值（Tauri CSP 为 null，允许）
  const fn = new Function(`"use strict";return (${raw});`)
  return fn() as T
}

/**
 * 一次抓取 orderadd 页面，同时拿到
 * - `var adtype`：广告类型（三级联动 + 素材字段）
 * - `var dict`：ad_format / class / price_mode 等下拉字典
 * 页面 600KB，避免为了两份数据抓两次。
 */
export async function loadOrderMeta(force = false): Promise<OrderMeta> {
  if (orderMetaCache && !force) return orderMetaCache
  const headers: Record<string, string> = {}
  if (sessionId) headers.Cookie = `PHPSESSID=${sessionId}`
  const res = await rawFetch(baseUrl() + '/ssp/pages/orderadd', {
    method: 'GET',
    headers,
    credentials: 'include',
    timeoutMs: 30000,
  })
  captureSession(res)
  const html = await res.text()
  const decl = /var\s+adtype\s*=/.exec(html)
  if (!decl) throw new Error('未找到广告类型定义（会话可能已失效）')
  const arrStart = html.indexOf('[', decl.index + decl[0].length - 1)
  if (arrStart < 0) throw new Error('未找到广告类型定义（会话可能已失效）')
  const raw = sliceBalanced(html, arrStart)
  if (!raw) throw new Error('广告类型定义不完整（页面结构可能已变更）')
  let list: SspAdType[]
  try {
    list = parseLooseValue<SspAdType[]>(raw)
  } catch (e) {
    console.warn('[ssp] adtype 解析失败', raw.slice(0, 400), e)
    throw new Error('广告类型解析失败（页面结构可能已变更）')
  }
  const valid = (Array.isArray(list) ? list : []).filter((x) => x && typeof x === 'object' && x.key)
  if (!valid.length) {
    console.warn('[ssp] adtype 解析结果为空', raw.slice(0, 400))
    throw new Error('广告类型列表为空（页面结构可能已变更）')
  }
  orderMetaCache = { adTypes: valid, dict: parseOrderDict(html) }
  return orderMetaCache
}

function parseOrderDict(html: string): SspOrderDict {
  const decl = /var\s+dict\s*=\s*\{/.exec(html)
  if (!decl) return {}
  const start = html.indexOf('{', decl.index + decl[0].length - 1)
  if (start < 0) return {}
  const raw = sliceBalanced(html, start)
  if (!raw) return {}
  try {
    const val = parseLooseValue<SspOrderDict>(raw)
    return val && typeof val === 'object' ? val : {}
  } catch (e) {
    console.warn('[ssp] dict 解析失败', raw.slice(0, 200), e)
    return {}
  }
}

export async function loadAdTypes(force = false): Promise<SspAdType[]> {
  return (await loadOrderMeta(force)).adTypes
}

export async function loadOrderDict(force = false): Promise<SspOrderDict> {
  return (await loadOrderMeta(force)).dict
}

/** 素材字段：info 中的对象项，例如 image_1 / video_1 */
export function materialFieldsOf(adType?: SspAdType): Record<string, any>[] {
  const info = adType?.info || {}
  return Object.entries(info)
    .filter(([, v]) => v && typeof v === 'object')
    .map(([key, v]: any) => ({ key, ...v }))
}

// ── 广告类型的三个下拉：category(text) → sub category(sub_text) → size(key) ──

export interface AdTypeLevel {
  /** 下拉显示值（第一级 text / 第二级 sub_text / 第三级 size） */
  value: string
  label: string
  /** 第三级才有：真正的 ad_type key */
  key?: string
}

/** 第一级：广告形式大类，如 Banner / Video / Splash */
export function adTypeLevel1(list: SspAdType[]): AdTypeLevel[] {
  const seen = new Map<string, AdTypeLevel>()
  list.forEach((t) => {
    const v = String(t.text ?? '')
    if (!seen.has(v)) seen.set(v, { value: v, label: v || '-' })
  })
  return Array.from(seen.values())
}

/** 第二级：子类，由第一级过滤 */
export function adTypeLevel2(list: SspAdType[], level1: string): AdTypeLevel[] {
  const seen = new Map<string, AdTypeLevel>()
  list.filter((t) => String(t.text ?? '') === level1).forEach((t) => {
    const v = String(t.sub_text ?? '')
    if (!seen.has(v)) seen.set(v, { value: v, label: v || '-' })
  })
  return Array.from(seen.values())
}

/** 第三级：具体类型，值就是 ad_type key，展示 size */
export function adTypeLevel3(list: SspAdType[], level1: string, level2: string): AdTypeLevel[] {
  const seen = new Map<string, AdTypeLevel>()
  list
    .filter((t) => String(t.text ?? '') === level1 && String(t.sub_text ?? '') === level2)
    .forEach((t) => {
      if (seen.has(t.key)) return
      seen.set(t.key, { value: t.key, label: String(t.size || t.key) })
    })
  return Array.from(seen.values())
}

// ── 广告位 / 媒体（新建广告时与后台一致的联动口径） ───────────

export interface SspAppOption {
  id: string
  name: string
}

/**
 * 后台 orderadd 的 Assigned media 选项来自 `/ssp/order/selectapps`，
 * 会随 Campaign / 广告类型变化。没有 ad_type 时退回全量媒体列表。
 */
export async function listOrderApps(camid: string, adtype: string): Promise<SspAppOption[]> {
  if (!adtype) {
    const res = await listMedias({ page: 1, pagesize: 500 })
    return res.records.map((m) => ({ id: String(m.id), name: m.name || `#${m.id}` }))
  }
  const res = await apiPost('/ssp/order/selectapps', { camid: camid || '', adtype })
  return (res?.records ?? []).map((r: any) => ({ id: String(r.id), name: String(r.text ?? r.name ?? r.id) }))
}

/**
 * Assigned zone 选项来自 `/ssp/order/selectlocs`，
 * 只返回所选媒体下、与该广告类型匹配的广告位。
 */
export async function listOrderZones(adtype: string, appIds: string[]): Promise<SspZone[]> {
  if (!adtype || !appIds.length) return []
  const res = await apiPost('/ssp/order/selectlocs', { adtype, appid: appIds.join(',') })
  return (res?.records ?? []).map((r: any) => ({
    id: String(r.id),
    name: String(r.text ?? r.name ?? r.id),
    appid: r.appid !== undefined ? String(r.appid) : undefined,
    ad_type: r.ad_type,
  }))
}

// ── 新建广告 ─────────────────────────────────────────────

export interface NewOrderInput {
  campaignId: string
  name: string
  adType: string
  material: Record<string, any>
  clickUrl?: string
  appIds: string[]
  locIds: string[]
  beginDate: string
  endDate: string
  keywordId?: string | string[]
  /** 定向方式：0 自定义定向（默认，广告级媒体/广告位/MAC 生效）/ 1 继承 Campaign */
  extendTarget?: 0 | 1
  priceMode?: string
  adClass?: string
  /** Ad icon：0 展示角标，1 不展示 */
  disableAdflag?: string
  /** Is external：'0' 否 / '1' 是 */
  external?: string
  /** 外部广告格式（external=1 时生效），如 VAST / Google IMA / whaletvplus / Teads image */
  adFormat?: string
}

export function buildNewOrderParams(input: NewOrderInput): Record<string, any> {
  const material = input.adFormat ? { ...input.material, ad_format: input.adFormat } : { ...input.material }
  return {
    id: 0,
    campaign_id: Number(input.campaignId || 0),
    name: input.name,
    ad_type: input.adType,
    material,
    click_url: input.clickUrl ?? '',
    click_monitor_url: '',
    pv_monitor_url: '',
    begin_date: input.beginDate,
    end_date: input.endDate,
    price_mode: input.priceMode || 'CPT',
    unit_price: '',
    cpm_percent: '',
    max_amount: '',
    class: input.adClass ?? '',
    total_budget: '',
    day_budget: '',
    // 0 = Custom targeting（广告自带媒体 / 广告位 / Custom engine 定向）
    // 1 = Inherit campaign（继承 Campaign，会忽略广告级定向，包括指定 MAC）
    // 本工具的编辑器一定会给广告配媒体与广告位，所以默认走自定义定向
    extend_target: input.extendTarget ?? 0,
    target_area: '',
    target_time: '',
    target_week: '',
    target_nettype: '',
    target_phone: '',
    target_app: input.appIds.join(';'),
    target_audience: '',
    target_os: '',
    target_plat: '3;;',
    target_loc: input.locIds.join(';'),
    target_keyword: input.keywordId ?? '',
    target_tag: '',
    target_brand_tag: '',
    target_tv_brand: '',
    freq_count: 0,
    freq_period: 0,
    freq_period_count: 0,
    freq_flag: 0,
    play_speed: 0,
    dates: '',
    weights: 0,
    monitor_order: '',
    target_area_type: 2,
    memo: '',
    disable_adflag: input.disableAdflag ?? '1',
    external: input.external ?? '0',
    is_google_image_ad: 0,
    head_script: '',
    body_script: '',
    industry: 0,
    macro: '',
    script_ad: '',
  }
}

export async function createOrder(input: NewOrderInput): Promise<void> {
  // 与后台表单一致：空字段也提交（否则 total_budget / day_budget 会以 NULL 入库报错）
  await apiPost('/ssp/order/add', buildNewOrderParams(input), true)
}

// ── 本地模板 ────────────────────────────────────────────

export interface SspTemplateAd {
  name: string
  ad_type: string
  material: Record<string, any>
  click_url?: string
  ad_class?: string
  price_mode?: string
}

export interface SspTemplate {
  id: string
  name: string
  demandPartner: string
  advertiserid: string
  ads: SspTemplateAd[]
  updatedAt: string
}

const TEMPLATES_KEY = 'ssp.templates'

export async function loadTemplates(): Promise<SspTemplate[]> {
  const raw = await db.getSetting(TEMPLATES_KEY)
  if (!raw) return []
  try {
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export async function saveTemplates(list: SspTemplate[]): Promise<void> {
  await db.setSetting(TEMPLATES_KEY, JSON.stringify(list))
}
