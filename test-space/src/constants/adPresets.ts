/**
 * 广告配置资源预设。
 *
 * 数据全部来自《4.2 广告配置方法》：
 *  - 素材预设：VAST / m3u8 / Google Ad Manager / MP4 / 图片（含尺寸说明）
 *  - 跳转链接预设：mp4 视频、deeplink 视频、应用、网址、图片 五种 landing JSON
 *
 * 素材预设通过 `accepts` 与广告类型字段的 `ext` 对齐，避免给图片位推荐视频。
 */

export type MaterialPresetKind = 'vast' | 'm3u8' | 'google' | 'mp4' | 'image'

export interface MaterialPreset {
  id: string
  kind: MaterialPresetKind
  zh: string
  en: string
  url: string
  /** 尺寸 / 时长等提示 */
  note?: string
  /** 可匹配的素材字段扩展名（小写，不含点） */
  accepts: string[]
}

/** 视频类字段才能用 VAST / 广告平台链接 */
const STREAM_EXT = ['mp4', 'm3u8']
const IMAGE_EXT = ['jpg', 'jpeg', 'png', 'gif', 'webp']

export const MATERIAL_PRESETS: MaterialPreset[] = [
  // ── VAST ──────────────────────────────────────────────
  {
    id: 'vast_springserve',
    kind: 'vast',
    zh: 'VAST · SpringServe',
    en: 'VAST · SpringServe',
    note: '1920×630 / 15-60s',
    url: 'https://tv.springserve.com/vast/634959?w=1920&h=630&ifa_type=ppid&gdpr_consent=1&gdpr=1&dnt=0&ic=[cat]&pod_max_dur=60&max_dur=60&min_dur=5&ap=1&mute=0&prodq=1&brand_name=Philips&app_bundle=20006335&app_name=PhilipsSmartTVPortal&app_store_url=https%3A%2F%2Fwww.zeasn.tv%2Fwhaleeco%2Fappstore%2Fdetail%3Fappid%3D20006335&language=[menu_language]&did=[whale_ad_id]&tv_model=[platform_id]&url=[src_page_url]&ua=[device_user_agent]&device_make=Philips&cb=[rnd]&content_genre=[genre]&rating=TV-G&userid=[device_id]&ifa_type=[ifa_type]',
    accepts: STREAM_EXT,
  },
  // ── m3u8 ──────────────────────────────────────────────
  {
    id: 'm3u8_springserve',
    kind: 'm3u8',
    zh: 'm3u8 · SpringServe 测试流',
    en: 'm3u8 · SpringServe test stream',
    note: '12s / QwestTV',
    url: 'https://d1bln19q4qkv4c.cloudfront.net/v1/master/5bb30b269f83d6c44f720981f63d8cdf6d94b837/test-springserve-688229/manual/12s_QWEST/12s_QWEST.m3u8?ads.app_name=WhaleLive&ads.app_bundle=20006184&ads.app_store_url=https%3A%2F%2Fwww.zeasn.com%2Fwhaleeco%2Fappstore%2Fdetail%3Fappid%3D20006184&ads.channel_name=QwestTV%20Classical&ads.wl_channel_id=5527&ads.ic=[cat]&ads.content_genre=[genre]&ads.content_id=5527&ads.content_title=QwestTV%20Classical&ads.gdpr_consent=[whale_gdpr_consent]&ads.gdpr=[whale_gdpr]&ads.dnt=[device_dnt]&ads.lmt=[device_lmt]&ads.did=[whale_ad_id]&ads.tv_language=[menu_language]&ads.tv_model=[platform_id]&ads.tv_domain=whalelive.zeasn.tv%2Fwhalelive_web%2F&ads.cb=[rnd]&ads.device_make=[tv_brand]&ads.brand_name=[tv_brand]&ads.userid=[device_id]&ifa_type=[ifa_type]&ads.givn=[google_pal]&ads.sid=[session_id]',
    accepts: ['m3u8'],
  },
  // ── Google Ad Manager ─────────────────────────────────
  {
    id: 'google_gam',
    kind: 'google',
    zh: 'Google Ad Manager',
    en: 'Google Ad Manager',
    note: 'VAST / 400×300 · 640×480',
    url: 'https://pubads.g.doubleclick.net/gampad/ads?iu=/21866217861/DEV_Philips_CTV&description_url=https%3A%2F%2Fwww.zeasn.tv%2Fabout%3Fid%3D43&tfcd=0&npa=0&sz=400x300%7C640x480&cust_params=platformid%3D[platform_id]%26cntry%3D99%26tvbrand%3D[tv_brand]%26tvdomain%3Dzeasn%26rdtype%3Dppid%26timerinterval%3D3&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&vpa=auto&vconp=1&vpmute=0&nofb=1&pp=MP4Creative&correlator=',
    accepts: STREAM_EXT,
  },
  // ── MP4 ───────────────────────────────────────────────
  {
    id: 'mp4_benz',
    kind: 'mp4',
    zh: 'MP4 · 奔驰',
    en: 'MP4 · Benz',
    note: '1920×630',
    url: 'http://img.l.zeasn.tv/4202/174477281667ff1ed07f45a.mp4',
    accepts: ['mp4'],
  },
  {
    id: 'mp4_beer',
    kind: 'mp4',
    zh: 'MP4 · 啤酒',
    en: 'MP4 · Beer',
    note: '1920×1080',
    url: 'https://staticssp.zeasn.tv/4282/1745638907680c55fb93c05.mp4',
    accepts: ['mp4'],
  },
  {
    id: 'mp4_11min_a',
    kind: 'mp4',
    zh: 'MP4 · 11 分钟',
    en: 'MP4 · 11 min',
    note: '≈11 min',
    url: 'https://staticssp.zeasn.tv/4235/17921371656ad1d7cddeeea.mp4',
    accepts: ['mp4'],
  },
  {
    id: 'mp4_11min_b',
    kind: 'mp4',
    zh: 'MP4 · 11 分钟 (2)',
    en: 'MP4 · 11 min (2)',
    note: '≈11 min',
    url: 'https://staticssp.zeasn.tv/4235/17895254146aa9fda69ea3d.mp4',
    accepts: ['mp4'],
  },
  {
    id: 'mp4_125s',
    kind: 'mp4',
    zh: 'MP4 · 125 秒',
    en: 'MP4 · 125s',
    note: '125s',
    url: 'https://staticssp.zeasn.tv/4235/17888663566a9fef347636b.mp4',
    accepts: ['mp4'],
  },
  // ── 图片 ──────────────────────────────────────────────
  {
    id: 'img_1920_630_a',
    kind: 'image',
    zh: '图片 · 1920×630 (JPG)',
    en: 'Image · 1920×630 (JPG)',
    note: '1920×630',
    url: 'http://img.l.zeasn.tv/4186/66da79607f1e6.jpg',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_1920_630_b',
    kind: 'image',
    zh: '图片 · 1920×630 (PNG)',
    en: 'Image · 1920×630 (PNG)',
    note: '1920×630',
    url: 'http://img.l.zeasn.tv/4202/67ff3eaac8ef9.png',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_1700_360_a',
    kind: 'image',
    zh: '图片 · 1700×360 (JPG)',
    en: 'Image · 1700×360 (JPG)',
    note: '1700×360',
    url: 'https://staticssp.zeasn.tv/2520/6ab3a621206d0.jpg',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_1700_360_b',
    kind: 'image',
    zh: '图片 · 1700×360 (PNG)',
    en: 'Image · 1700×360 (PNG)',
    note: '1700×360',
    url: 'https://staticssp.zeasn.tv/4486/6a9e2199d85f3.png',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_other_a',
    kind: 'image',
    zh: '图片 · 其它尺寸 (JPG)',
    en: 'Image · Other size (JPG)',
    note: '非 1920×630',
    url: 'http://img.l.zeasn.tv/4183/66b9b7643c781.jpg',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_other_b',
    kind: 'image',
    zh: '图片 · 其它尺寸 (PNG)',
    en: 'Image · Other size (PNG)',
    note: '非 1920×630',
    url: 'http://img.l.zeasn.tv/4202/67d9700e54a53.png',
    accepts: IMAGE_EXT,
  },
  {
    id: 'img_other_gif',
    kind: 'image',
    zh: '图片 · 其它尺寸 (GIF)',
    en: 'Image · Other size (GIF)',
    note: 'GIF 动图',
    url: 'http://img.l.zeasn.tv/4202/67d7b857d1d1e.gif',
    accepts: IMAGE_EXT,
  },
]

export const PRESET_KIND_LABEL: Record<MaterialPresetKind, { zh: string; en: string }> = {
  vast: { zh: 'VAST', en: 'VAST' },
  m3u8: { zh: 'm3u8', en: 'm3u8' },
  google: { zh: 'Google', en: 'Google' },
  mp4: { zh: 'MP4', en: 'MP4' },
  image: { zh: '图片', en: 'Image' },
}

/** 按素材字段的 ext（如 "mp4,m3u8,jpg"）筛选可用的预设 */
export function presetsForExt(ext?: string): MaterialPreset[] {
  const tokens = String(ext || '')
    .toLowerCase()
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  if (!tokens.length) return []
  return MATERIAL_PRESETS.filter((p) => p.accepts.some((a) => tokens.includes(a)))
}

// ── 跳转链接（landing） ─────────────────────────────────

export type LandingType = 'none' | 'video' | 'deeplink' | 'app' | 'web' | 'picture'

/**
 * 界面上可选的类型：
 * 预设 5 种 + `custom`（后台存的是纯链接或别的结构，认不出预设时保留原文，不能再显示「无跳转」）。
 */
export type LandingUiType = LandingType | 'custom'

export interface LandingOption {
  key: LandingUiType
  zh: string
  en: string
  /** 是否需要包名 */
  needPkg: boolean
  /** 是否需要 url */
  needUrl: boolean
  /** 示例 URL */
  sampleUrl?: string
  /** 示例包名 */
  samplePkg?: string
}

/**
 * 5 种链接的示例值（单一来源，选项与组件都从这里取）。
 * 文档《4.2 广告配置方法》逐字对应，改这里即可。
 */
export const LANDING_SAMPLES: Record<string, { url?: string; pkg?: string }> = {
  video: { url: 'https://staticssp.zeasn.tv/4235/1735526604677208cc92368.mp4' },
  deeplink: {
    url: 'https://www.youtube.com/watch?v=ZkvjSYwq0Qw',
    pkg: 'com.google.android.youtube.tv',
  },
  app: { pkg: 'com.zeasn.tv.cast' },
  web: { url: 'https://www.1688.com/zw/hamlet.html?scene=6&cosite=bingjj_pz' },
  picture: { url: 'http://img.l.zeasn.tv/4080/6465e9cace648.jpg' },
}

export const LANDING_OPTIONS: LandingOption[] = [
  { key: 'none', zh: '无跳转', en: 'No landing', needPkg: false, needUrl: false },
  {
    key: 'video',
    zh: 'MP4 视频',
    en: 'MP4 video',
    needPkg: false,
    needUrl: true,
    sampleUrl: LANDING_SAMPLES.video.url,
  },
  {
    key: 'deeplink',
    zh: '视频 Deeplink',
    en: 'Video deeplink',
    needPkg: true,
    needUrl: true,
    sampleUrl: LANDING_SAMPLES.deeplink.url,
    samplePkg: LANDING_SAMPLES.deeplink.pkg,
  },
  {
    key: 'app',
    zh: '应用',
    en: 'App',
    needPkg: true,
    needUrl: false,
    samplePkg: LANDING_SAMPLES.app.pkg,
  },
  {
    key: 'web',
    zh: '网址',
    en: 'Website',
    needPkg: false,
    needUrl: true,
    sampleUrl: LANDING_SAMPLES.web.url,
  },
  {
    key: 'picture',
    zh: '图片',
    en: 'Picture',
    needPkg: false,
    needUrl: true,
    sampleUrl: LANDING_SAMPLES.picture.url,
  },
]

/** 认不出预设结构时用的「原文」档，保证下拉框不会把已配置的链接显示成「无跳转」 */
export const LANDING_CUSTOM_OPTION: LandingOption = {
  key: 'custom',
  zh: '原文',
  en: 'Raw',
  needPkg: false,
  needUrl: false,
}

export function landingOption(type: LandingUiType): LandingOption {
  if (type === 'custom') return LANDING_CUSTOM_OPTION
  return LANDING_OPTIONS.find((o) => o.key === type) || LANDING_OPTIONS[0]
}

/** 把后台返回的任意形态（字符串 / 对象 / 数组）转成可编辑的原文 */
export function landingText(raw: unknown): string {
  if (raw === null || raw === undefined) return ''
  if (typeof raw === 'string') return raw.trim()
  if (typeof raw === 'number' || typeof raw === 'boolean') return String(raw)
  try {
    return JSON.stringify(raw)
  } catch {
    return ''
  }
}

/** 生成后台要求的 landing JSON 字符串 */
export function buildLanding(type: LandingUiType, url = '', pkg = ''): string {
  const u = url.trim()
  const p = pkg.trim()
  switch (type) {
    case 'video':
      return u ? JSON.stringify({ landing_type: 'video', landing_data: { url: u } }) : ''
    case 'deeplink':
      return u || p ? JSON.stringify({ landing_type: 'deeplink', landing_data: { pkg: p, url: u } }) : ''
    case 'app':
      return p ? JSON.stringify({ landing_type: 'app', landing_data: { pkg: p } }) : ''
    case 'web':
      return u ? JSON.stringify({ landing_type: 'web', landing_data: { url: u } }) : ''
    case 'picture':
      return u ? JSON.stringify({ landing_type: 'picture', landing_data: { url: u } }) : ''
    default:
      return ''
  }
}

// ── 反解：后台的 click_url 可能不是标准 landing JSON ──────────
//
// 后台「Click URL」只有一个输入框，运营常常直接粘贴一条链接（甚至整段带引号/转义的文本），
// 也见过对象、数组、二次编码等形态。这里统一做「尽力识别」，识别不出来就落到 `custom`，
// 让界面显示原文而不是误报「无跳转」。

/** 类型别名归一：`Website` / `url` / `h5` 都按网址处理 */
const TYPE_ALIAS: Record<string, LandingType> = {
  none: 'none',
  '0': 'none',
  video: 'video',
  mp4: 'video',
  m3u8: 'video',
  videomp4: 'video',
  deeplink: 'deeplink',
  deeplinkvideo: 'deeplink',
  deep: 'deeplink',
  deeplink2: 'deeplink',
  app: 'app',
  application: 'app',
  package: 'app',
  pkg: 'app',
  apk: 'app',
  web: 'web',
  website: 'web',
  webpage: 'web',
  url: 'web',
  uri: 'web',
  link: 'web',
  h5: 'web',
  browser: 'web',
  picture: 'picture',
  image: 'picture',
  img: 'picture',
  pic: 'picture',
  photo: 'picture',
}

const URL_KEYS = ['url', 'link', 'landingurl', 'clickurl', 'targeturl', 'downloadurl', 'href', 'jumpurl']
const PKG_KEYS = ['pkg', 'package', 'packagename', 'apppkg', 'bundle', 'bundlename', 'apk', 'packageid']
const TYPE_KEYS = ['landingtype', 'landing', 'type', 'linktype', 'jumptype', 'clicktype']
const DATA_KEYS = ['landingdata', 'data', 'landinginfo', 'linkdata', 'params', 'detail']

function normKey(k: string) {
  return String(k || '').toLowerCase().replace(/[^a-z0-9]/g, '')
}

function normType(v: unknown): LandingType | null {
  const key = normKey(String(v ?? ''))
  if (!key) return null
  return TYPE_ALIAS[key] ?? null
}

/** 按归一化后的键名取字段，兼容 landing_type / landingType / landingtype */
function pick(obj: any, keys: string[]): any {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return undefined
  const map = new Map<string, any>()
  Object.keys(obj).forEach((k) => map.set(normKey(k), obj[k]))
  for (const k of keys) {
    const v = map.get(normKey(k))
    if (v !== undefined && v !== null && v !== '') return v
  }
  return undefined
}

/** 去掉 HTML 实体 / URL 编码等外层包裹 */
function normalizeText(raw: string): string {
  let text = String(raw ?? '').trim()
  if (!text) return ''
  if (/&quot;|&#34;|&#39;|&amp;|&lt;|&gt;/.test(text)) {
    text = text
      .replace(/&quot;|&#34;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .trim()
  }
  if (/^%7B|^%5B/i.test(text)) {
    try { text = decodeURIComponent(text).trim() } catch { /* 保持原样 */ }
  }
  return text
}

/** 解析 JSON，容忍二次编码、单引号 / 尾逗号的 PHP 风格输出 */
function tryJson(text: string): any {
  const t = text.trim()
  if (!t) return undefined
  if (!/^["'[{]|^&quot;|^%7B/i.test(t)) return undefined
  try { return JSON.parse(t) } catch { /* 继续尝试 */ }
  try {
    const once = JSON.parse(t)
    if (typeof once === 'string') {
      try { return JSON.parse(once) } catch { return once }
    }
    return once
  } catch { /* 继续尝试 */ }
  try {
    const loose = t
      .replace(/'/g, '"')
      .replace(/,\s*([}\]])/g, '$1')
      .replace(/([{,]\s*)([A-Za-z_$][\w$]*)\s*:/g, '$1"$2":')
    return JSON.parse(loose)
  } catch {
    return undefined
  }
}

/** 逐层剥开字符串 / 数组包裹，拿到真正的对象 */
function unwrap(value: any, depth = 0): any {
  if (depth > 4) return value
  if (typeof value === 'string') {
    const text = normalizeText(value)
    if (!text) return ''
    const parsed = tryJson(text)
    if (parsed === undefined) return text
    return unwrap(parsed, depth + 1)
  }
  if (Array.isArray(value)) {
    const first = value.find((v) => v !== null && v !== undefined && v !== '')
    return first === undefined ? '' : unwrap(first, depth + 1)
  }
  return value
}

const VIDEO_EXT = /\.(mp4|m3u8|mpd|mov|webm|flv)(?:$|[?#])/i
const IMAGE_EXT_RE = /\.(jpe?g|png|gif|webp|bmp|svg)(?:$|[?#])/i

/** 有链接没类型时按内容猜：视频 / 图片 / 网址 / 自定义 scheme */
function inferType(url: string, pkg: string): LandingType | null {
  const u = String(url || '').trim()
  if (u) {
    if (VIDEO_EXT.test(u)) return 'video'
    if (IMAGE_EXT_RE.test(u)) return 'picture'
    if (/^https?:\/\//i.test(u)) return 'web'
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(u)) return 'deeplink'
    if (/^www\./i.test(u)) return 'web'
    // 域名样（含点号 + 可选的端口/路径）
    if (/^[\w-]+(\.[\w-]+)+(?::\d+)?(?:[/?#]|$)/.test(u)) return 'web'
    return null
  }
  return pkg.trim() ? 'app' : null
}

function looksLikePackage(text: string) {
  const t = text.trim()
  if (!t || /[/\s:]/.test(t)) return false
  // 域名（www.xxx.com）优先按网址理解，不能当成包名
  if (/^www\./i.test(t)) return false
  return /^[A-Za-z][\w-]*(?:\.[\w-]+){2,}$/.test(t)
}

function fromPlainText(text: string): { type: LandingUiType; url: string; pkg: string } | null {
  const t = normalizeText(text)
  if (!t) return null
  if (looksLikePackage(t)) return { type: 'app', url: '', pkg: t }
  const inferred = inferType(t, '')
  if (inferred) return { type: inferred, url: t, pkg: '' }
  return { type: 'custom', url: '', pkg: '' }
}

/**
 * 反解后台返回的 click_url（编辑回显 / 复制广告共用）。
 *
 * 返回 null 表示确实没有配置（空值）；
 * 返回 `custom` 表示有值但不是预设结构，界面应保留原文编辑，不能显示成「无跳转」。
 */
export function parseLanding(raw?: unknown): { type: LandingUiType; url: string; pkg: string } | null {
  if (raw === null || raw === undefined) return null
  const unwrapped = unwrap(raw)
  if (typeof unwrapped === 'string') return fromPlainText(unwrapped)
  if (!unwrapped || typeof unwrapped !== 'object') return null

  let url = landingText(pick(unwrapped, URL_KEYS))
  let pkg = landingText(pick(unwrapped, PKG_KEYS))
  let type = normType(pick(unwrapped, TYPE_KEYS))

  const data = pick(unwrapped, DATA_KEYS)
  if (data !== undefined) {
    const inner = unwrap(data)
    if (inner && typeof inner === 'object') {
      url = url || landingText(pick(inner, URL_KEYS))
      pkg = pkg || landingText(pick(inner, PKG_KEYS))
      type = type || normType(pick(inner, TYPE_KEYS))
    } else if (typeof inner === 'string') {
      url = url || inner.trim()
    }
  }

  if (type === 'none') return { type: 'none', url: '', pkg: '' }
  if (type) return { type, url, pkg }
  const inferred = inferType(url, pkg)
  if (inferred) return { type: inferred, url, pkg }
  return { type: 'custom', url: '', pkg: '' }
}
