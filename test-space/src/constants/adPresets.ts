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

export interface LandingOption {
  key: LandingType
  zh: string
  en: string
  /** 是否需要包名 */
  needPkg: boolean
  /** 是否需要 url */
  needUrl: boolean
  /** 示例值 */
  sample?: string
}

export const LANDING_OPTIONS: LandingOption[] = [
  { key: 'none', zh: '无跳转', en: 'No landing', needPkg: false, needUrl: false },
  {
    key: 'video',
    zh: 'MP4 视频',
    en: 'MP4 video',
    needPkg: false,
    needUrl: true,
    sample: 'https://staticssp.zeasn.tv/4235/1735526604677208cc92368.mp4',
  },
  {
    key: 'deeplink',
    zh: '视频 Deeplink',
    en: 'Video deeplink',
    needPkg: true,
    needUrl: true,
    sample: 'https://www.youtube.com/watch?v=ZkvjSYwq0Qw',
  },
  { key: 'app', zh: '应用', en: 'App', needPkg: true, needUrl: false, sample: 'com.zeasn.tv.cast' },
  { key: 'web', zh: '网址', en: 'Website', needPkg: false, needUrl: true, sample: 'https://www.1688.com' },
  {
    key: 'picture',
    zh: '图片',
    en: 'Picture',
    needPkg: false,
    needUrl: true,
    sample: 'http://img.l.zeasn.tv/4080/6465e9cace648.jpg',
  },
]

export function landingOption(type: LandingType): LandingOption {
  return LANDING_OPTIONS.find((o) => o.key === type) || LANDING_OPTIONS[0]
}

/** 生成后台要求的 landing JSON 字符串 */
export function buildLanding(type: LandingType, url = '', pkg = ''): string {
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

/** 解析已有 landing JSON，用于复制广告时回填表单 */
export function parseLanding(raw?: string): { type: LandingType; url: string; pkg: string } | null {
  const text = String(raw || '').trim()
  if (!text) return null
  try {
    const obj = JSON.parse(text)
    const type = String(obj?.landing_type || '') as LandingType
    if (!LANDING_OPTIONS.some((o) => o.key === type) || type === 'none') return null
    const data = obj?.landing_data || {}
    return { type, url: String(data.url || ''), pkg: String(data.pkg || '') }
  } catch {
    return null
  }
}
