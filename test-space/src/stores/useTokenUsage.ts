import { ref } from 'vue'
import * as db from '@/services/database'

export interface TokenUsage {
  promptTokens: number
  completionTokens: number
  totalTokens: number
}

const STORAGE_KEY = 'token_usage'

const promptTokens = ref(0)
const completionTokens = ref(0)
const totalTokens = ref(0)

let loaded = false

export function useTokenUsage() {
  async function loadUsage() {
    if (loaded) return
    loaded = true
    try {
      const raw = await db.getSetting(STORAGE_KEY)
      if (raw) {
        const data = JSON.parse(raw) as TokenUsage
        promptTokens.value = data.promptTokens ?? 0
        completionTokens.value = data.completionTokens ?? 0
        totalTokens.value = data.totalTokens ?? 0
      }
    } catch {}
  }

  function persistUsage() {
    db.setSetting(STORAGE_KEY, JSON.stringify({
      promptTokens: promptTokens.value,
      completionTokens: completionTokens.value,
      totalTokens: totalTokens.value,
    })).catch(() => {})
  }

  function addUsage(usage?: TokenUsage) {
    if (!usage) return
    promptTokens.value += usage.promptTokens
    completionTokens.value += usage.completionTokens
    totalTokens.value += usage.totalTokens
    persistUsage()
  }

  function resetUsage() {
    promptTokens.value = 0
    completionTokens.value = 0
    totalTokens.value = 0
    persistUsage()
  }

  return {
    promptTokens,
    completionTokens,
    totalTokens,
    addUsage,
    resetUsage,
    loadUsage,
  }
}
