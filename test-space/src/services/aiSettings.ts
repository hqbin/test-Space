import { getSetting, setSetting } from '@/services/database'

export type AiProvider = 'azure' | 'deepseek' | 'mimo' | 'openai' | 'custom'

export interface AiConfig {
  provider: AiProvider
  apiKey: string
  endpoint: string
  model: string
  maxContextTokens: number
  authMode: 'api-key' | 'bearer'
}

const AI_SETTINGS_KEY = 'ai_config'
const AI_PROVIDERS: AiProvider[] = ['azure', 'deepseek', 'mimo', 'openai', 'custom']

export const AI_PROVIDER_PRESETS: Record<AiProvider, Omit<AiConfig, 'apiKey'>> = {
  azure: {
    provider: 'azure',
    endpoint: 'https://YOUR-RESOURCE.openai.azure.com/openai/v1/chat/completions',
    model: 'gpt-5',
    maxContextTokens: 8000,
    authMode: 'api-key',
  },
  deepseek: {
    provider: 'deepseek',
    endpoint: 'https://api.deepseek.com/chat/completions',
    model: 'deepseek-chat',
    maxContextTokens: 8000,
    authMode: 'bearer',
  },
  mimo: {
    provider: 'mimo',
    endpoint: 'https://api.xiaomimimo.com/v1/chat/completions',
    model: 'mimo-v2.5-pro',
    maxContextTokens: 8000,
    authMode: 'api-key',
  },
  openai: {
    provider: 'openai',
    endpoint: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o-mini',
    maxContextTokens: 8000,
    authMode: 'bearer',
  },
  custom: {
    provider: 'custom',
    endpoint: '',
    model: '',
    maxContextTokens: 8000,
    authMode: 'bearer',
  },
}

const DEFAULT_CONFIG: AiConfig = {
  ...AI_PROVIDER_PRESETS.azure,
  apiKey: '',
}

interface StoredAiSettings {
  activeProvider: AiProvider
  configs: Partial<Record<AiProvider, AiConfig>>
}

function isAiProvider(value: unknown): value is AiProvider {
  return typeof value === 'string' && AI_PROVIDERS.includes(value as AiProvider)
}

function normalizeAiConfig(provider: AiProvider, config?: Partial<AiConfig>): AiConfig {
  const preset = AI_PROVIDER_PRESETS[provider]
  return {
    ...preset,
    ...config,
    provider,
    apiKey: config?.apiKey ?? '',
    authMode: config?.authMode === 'bearer' ? 'bearer' : preset.authMode,
    maxContextTokens: Math.min(32000, Math.max(1000, config?.maxContextTokens ?? preset.maxContextTokens)),
  }
}

function parseStoredAiSettings(raw: string | null): StoredAiSettings {
  if (!raw) {
    return { activeProvider: DEFAULT_CONFIG.provider, configs: { [DEFAULT_CONFIG.provider]: { ...DEFAULT_CONFIG } } }
  }

  try {
    const parsed = JSON.parse(raw) as Partial<StoredAiSettings> & Partial<AiConfig>
    if (parsed.configs && typeof parsed.configs === 'object') {
      const activeProvider = isAiProvider(parsed.activeProvider) ? parsed.activeProvider : DEFAULT_CONFIG.provider
      const configs: Partial<Record<AiProvider, AiConfig>> = {}
      for (const provider of AI_PROVIDERS) {
        if (parsed.configs[provider]) {
          configs[provider] = normalizeAiConfig(provider, parsed.configs[provider])
        }
      }
      if (!configs[activeProvider]) configs[activeProvider] = normalizeAiConfig(activeProvider)
      return { activeProvider, configs }
    }

    const legacyProvider = isAiProvider(parsed.provider) ? parsed.provider : DEFAULT_CONFIG.provider
    return {
      activeProvider: legacyProvider,
      configs: { [legacyProvider]: normalizeAiConfig(legacyProvider, parsed) },
    }
  } catch {
    return { activeProvider: DEFAULT_CONFIG.provider, configs: { [DEFAULT_CONFIG.provider]: { ...DEFAULT_CONFIG } } }
  }
}

async function loadAiSettingsStore(): Promise<StoredAiSettings> {
  return parseStoredAiSettings(await getSetting(AI_SETTINGS_KEY))
}

async function saveAiSettingsStore(store: StoredAiSettings): Promise<void> {
  await setSetting(AI_SETTINGS_KEY, JSON.stringify(store))
}

export async function loadAiConfig(): Promise<AiConfig> {
  const store = await loadAiSettingsStore()
  return normalizeAiConfig(store.activeProvider, store.configs[store.activeProvider])
}

export async function loadAiConfigForProvider(provider: AiProvider): Promise<AiConfig> {
  const store = await loadAiSettingsStore()
  return normalizeAiConfig(provider, store.configs[provider])
}

export async function saveAiConfig(config: AiConfig): Promise<void> {
  const provider = isAiProvider(config.provider) ? config.provider : DEFAULT_CONFIG.provider
  const store = await loadAiSettingsStore()
  store.activeProvider = provider
  store.configs[provider] = normalizeAiConfig(provider, config)
  await saveAiSettingsStore(store)
}

export function isAiConfigured(config: AiConfig): boolean {
  return !!(config.apiKey.trim() && config.endpoint.trim() && config.model.trim())
}
