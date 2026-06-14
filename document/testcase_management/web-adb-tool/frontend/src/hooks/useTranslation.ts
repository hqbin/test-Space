/**
 * 翻译 Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { getCurrentLocale, setCurrentLocale, getTranslations, Locale } from '../i18n'
import type { TranslationKeys } from '../i18n/locales/zh-CN'

/**
 * 使用翻译的 Hook
 */
export function useTranslation() {
  const [locale, setLocale] = useState<Locale>(getCurrentLocale())
  const [translations, setTranslations] = useState<TranslationKeys>(getTranslations(locale))

  // 更新语言
  const changeLocale = useCallback((newLocale: Locale) => {
    setLocale(newLocale)
    setCurrentLocale(newLocale)
    setTranslations(getTranslations(newLocale))
    
    // 触发自定义事件，通知其他组件语言已更改
    window.dispatchEvent(new CustomEvent('localeChange', { detail: newLocale }))
  }, [])

  // 监听语言变化事件
  useEffect(() => {
    const handleLocaleChange = (event: CustomEvent<Locale>) => {
      const newLocale = event.detail
      setLocale(newLocale)
      setTranslations(getTranslations(newLocale))
    }

    window.addEventListener('localeChange', handleLocaleChange as EventListener)
    return () => {
      window.removeEventListener('localeChange', handleLocaleChange as EventListener)
    }
  }, [])

  return {
    locale,
    t: translations,
    changeLocale,
  }
}
