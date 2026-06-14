/**
 * 国际化配置
 */

import { zhCN } from './locales/zh-CN'
import { enUS } from './locales/en-US'

export type Locale = 'zh-CN' | 'en-US'

export const locales = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

export const localeNames: Record<Locale, string> = {
  'zh-CN': '简体中文',
  'en-US': 'English',
}

// 默认语言
export const defaultLocale: Locale = 'zh-CN'

// LocalStorage key
export const LOCALE_STORAGE_KEY = 'adb_tool_locale'

/**
 * 获取当前语言
 */
export function getCurrentLocale(): Locale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (stored && (stored === 'zh-CN' || stored === 'en-US')) {
    return stored as Locale
  }
  return defaultLocale
}

/**
 * 设置当前语言
 */
export function setCurrentLocale(locale: Locale): void {
  localStorage.setItem(LOCALE_STORAGE_KEY, locale)
}

/**
 * 获取翻译文本
 */
export function getTranslations(locale: Locale) {
  return locales[locale] || locales[defaultLocale]
}
