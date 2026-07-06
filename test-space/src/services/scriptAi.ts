/**
 * Script AI service — generates/modifies BAT or Python scripts via the configured LLM.
 * Keeps business logic out of NoteAiPanel so it stays testable and replaceable.
 */
import type { AiConfig } from '@/services/aiSettings'
import { type AiChatMessage, resolveSystemRole } from '@/services/noteAi'

export interface ScriptAiResult {
  /** Target script type, decided by AI based on the request */
  scriptType: 'bat' | 'py'
  /** Script name suggested by AI (without extension) */
  name: string
  /** The generated/modified code (no markdown fences) */
  code: string
  /** Short human-readable summary of what was done */
  description: string
}

export interface ScriptAiRequest {
  config: AiConfig
  question: string
  /** Currently active type tab in the editor */
  scriptType: 'bat' | 'py'
  /** Content already in the editor (empty string = new script) */
  currentContent: string
  /** Names of other scripts in the library (for import/call awareness) */
  existingScriptNames: string[]
  /** Conversation history (last few turns) */
  history: AiChatMessage[]
}

// ── Internal fetch helper (reuse Tauri HTTP plugin when available) ──────────
let _tauriFetch: typeof fetch | null = null
async function getFetch(): Promise<typeof fetch> {
  if (_tauriFetch) return _tauriFetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    _tauriFetch = mod.fetch
  } catch {
    _tauriFetch = fetch
  }
  return _tauriFetch!
}

async function callApi(config: AiConfig, messages: AiChatMessage[]): Promise<any> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (config.authMode === 'api-key') {
    headers['api-key'] = config.apiKey.trim()
  } else {
    headers['Authorization'] = `Bearer ${config.apiKey.trim()}`
  }

  const body: Record<string, unknown> = {
    model: config.model.trim(),
    messages,
  }

  // Do NOT set temperature or max_completion_tokens — let the deployment use its defaults.
  // temperature: Azure deployments often reject non-default values.
  // max_completion_tokens: omitting lets the model use its deployment default (typically 4096+).

  if (config.provider === 'mimo') {
    body.stream = false
  }

  const f = await getFetch()
  const res = await f(config.endpoint.trim(), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })

  const text = await res.text()
  let json: any
  try { json = JSON.parse(text) } catch {
    throw new Error(`API 返回非 JSON (HTTP ${res.status}): ${text.slice(0, 300)}`)
  }
  if (!res.ok) {
    const errMsg = json.error?.message || json.error?.code || json.error || json.message || `HTTP ${res.status}`
    throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg))
  }
  return json
}

// ── Prompt builders ──────────────────────────────────────────────────────────

function buildSystemPrompt(req: ScriptAiRequest): string {
  const scriptTypeName = req.scriptType === 'py' ? 'Python' : 'BAT (Windows Batch)'
  const scriptTypeHeader = req.scriptType === 'py' ? 'py' : 'bat'

  const existingNamesBlock = req.existingScriptNames.length > 0
    ? `\nExisting scripts in the library (can be imported/called):\n${req.existingScriptNames.map(n => `- ${n}`).join('\n')}`
    : ''

  const currentBlock = req.currentContent.trim()
    ? `\nCurrent editor content (modify this based on user request):\n\`\`\`\n${req.currentContent}\n\`\`\``
    : '\nThe editor is currently empty — generate a new script from scratch.'

  return `You are a script-writing assistant for software testers on Windows.
The user has selected ${scriptTypeName} mode. You MUST generate a ${scriptTypeName} script. Do NOT use PowerShell, Python, or any other language.
${currentBlock}
${existingNamesBlock}

Reply using EXACTLY this format — no extra text before or after:
SCRIPT_TYPE: ${scriptTypeHeader}
SCRIPT_NAME: <short_filename_no_spaces_no_extension>
DESCRIPTION: <one sentence in the user's language>
\`\`\`
<complete runnable ${scriptTypeName} script here>
\`\`\`

Additional rules:
- The script must be complete and directly runnable.
- Do NOT add environment checks (e.g. checking if adb, python, or other tools are installed). Assume the environment is already set up correctly. Only add such checks if the user explicitly asks for them.
- For BAT: always start with these two lines at the top:
  @echo off
  chcp 65001 >nul
  This ensures UTF-8 encoding so Chinese characters in echo/rem lines display and execute correctly. Use only ASCII punctuation in echo statements — never Chinese/fullwidth punctuation (，。！？：；) or arrow symbols (->, =>) as they can still cause issues. Do not use PowerShell syntax.
- For Python: use only stdlib unless the user explicitly requests third-party packages. Use plain \`import <name>\` for importing other scripts in the library.
- Reply in the same language the user writes in. Comments can use the user's language.`
}
// ── Robust JSON extraction ───────────────────────────────────────────────────

/**
 * Extract a JSON object from a model response that may contain surrounding text,
 * markdown fences, or explanatory prose.
 *
 * Strategy (in order):
 *   1. Try parsing the whole response as-is
 *   2. Extract content from ```json ... ``` fence
 *   3. Extract content from ``` ... ``` fence (any language tag)
 *   4. Find the first { ... } block spanning to the last }
 */
function extractJson(raw: string): string | null {
  const s = raw.trim()

  // 1. Try raw
  try { JSON.parse(s); return s } catch {}

  // 2. ```json fence
  const jsonFence = s.match(/```json\s*([\s\S]*?)```/i)
  if (jsonFence?.[1]) {
    const candidate = jsonFence[1].trim()
    try { JSON.parse(candidate); return candidate } catch {}
  }

  // 3. Any ``` fence
  const anyFence = s.match(/```(?:\w*)\s*([\s\S]*?)```/)
  if (anyFence?.[1]) {
    const candidate = anyFence[1].trim()
    try { JSON.parse(candidate); return candidate } catch {}
  }

  // 4. First { to last }
  const first = s.indexOf('{')
  const last = s.lastIndexOf('}')
  if (first !== -1 && last > first) {
    const candidate = s.slice(first, last + 1)
    try { JSON.parse(candidate); return candidate } catch {}
  }

  return null
}

// ── BAT echo sanitizer ───────────────────────────────────────────────────────

/**
 * Post-process AI-generated BAT scripts:
 * 1. Ensure chcp 65001 is present so cmd.exe uses UTF-8 (prevents Chinese chars
 *    from being misinterpreted as command tokens on GBK terminals).
 * 2. Replace fullwidth punctuation and problematic arrow sequences in echo/rem/:: lines.
 */
function sanitizeBatEchoLines(code: string): string {
  const FULLWIDTH_MAP: [RegExp, string][] = [
    [/：/g, ':'],
    [/，/g, ','],
    [/。/g, '.'],
    [/！/g, '!'],
    [/？/g, '?'],
    [/；/g, ';'],
    [/（/g, '('],
    [/）/g, ')'],
    [/【/g, '['],
    [/】/g, ']'],
    [/「/g, '"'],
    [/」/g, '"'],
    [/『/g, "'"],
    [/』/g, "'"],
    [/->/g, ' to '],
    [/=>/g, ' to '],
  ]

  const lines = code.split('\n').map(line => {
    if (!/^\s*(echo\s+|rem\s|::)/i.test(line)) return line
    let result = line
    for (const [pattern, replacement] of FULLWIDTH_MAP) {
      result = result.replace(pattern, replacement)
    }
    return result
  })

  // Inject "chcp 65001 >nul" after the first "@echo off" line if not already present
  const hasChcp = lines.some(l => /chcp\s+65001/i.test(l))
  if (!hasChcp) {
    const echoOffIdx = lines.findIndex(l => /^\s*@?echo\s+off/i.test(l))
    if (echoOffIdx !== -1) {
      lines.splice(echoOffIdx + 1, 0, 'chcp 65001 >nul')
    }
  }

  return lines.join('\n')
}

// ── Parse structured response ────────────────────────────────────────────────

/**
 * Parse the structured text format:
 *
 * SCRIPT_TYPE: bat
 * SCRIPT_NAME: my_script
 * DESCRIPTION: Does something useful
 * ```
 * @echo off
 * ...
 * ```
 *
 * Falls back to JSON extraction (legacy / model deviation), then raw code.
 */
function parseResult(raw: string, fallbackType: 'bat' | 'py'): ScriptAiResult {
  const s = raw.trim()

  // ── Strategy 1: structured header format ─────────────────────
  const typeMatch = s.match(/^SCRIPT_TYPE:\s*(bat|py)/im)
  const nameMatch = s.match(/^SCRIPT_NAME:\s*(.+)/im)
  const descMatch = s.match(/^DESCRIPTION:\s*(.+)/im)

  // Extract code block (content between first ``` and last ```)
  const fenceMatch = s.match(/```(?:\w*)?\n?([\s\S]*?)```/)
  const fencedCode = fenceMatch?.[1]?.trim() ?? ''

  if (typeMatch && fencedCode) {
    const scriptType: 'bat' | 'py' = typeMatch[1] === 'py' ? 'py' : 'bat'
    const name = nameMatch?.[1]?.trim().replace(/[<>:"/\\|?*\s]/g, '_') || 'ai_script'
    const description = descMatch?.[1]?.trim() || ''
    const code = scriptType === 'bat' ? sanitizeBatEchoLines(fencedCode) : fencedCode
    return { scriptType, name, code, description }
  }

  // ── Strategy 2: legacy JSON (model ignored new format) ───────
  const jsonStr = extractJson(s)
  if (jsonStr) {
    try {
      const obj = JSON.parse(jsonStr) as Partial<ScriptAiResult>
      const scriptType: 'bat' | 'py' =
        obj.scriptType === 'py' || obj.scriptType === 'bat' ? obj.scriptType : fallbackType
      const name = typeof obj.name === 'string' && obj.name.trim()
        ? obj.name.trim().replace(/[<>:"/\\|?*\s]/g, '_')
        : 'ai_script'
      let code = typeof obj.code === 'string' ? obj.code.trim() : ''
      const description = typeof obj.description === 'string' ? obj.description.trim() : ''
      if (code) {
        if (scriptType === 'bat') code = sanitizeBatEchoLines(code)
        return { scriptType, name, code, description }
      }
    } catch {}
  }

  // ── Strategy 3: bare code fence without headers ───────────────
  if (fencedCode) {
    const looksLikePy = /^#!.*python|^import |^def |^class /m.test(fencedCode)
    const detectedType = looksLikePy ? 'py' : fallbackType
    const code = detectedType === 'bat' ? sanitizeBatEchoLines(fencedCode) : fencedCode
    return { scriptType: detectedType, name: 'ai_script', code, description: '' }
  }

  // ── Strategy 4: entire response is raw code ───────────────────
  const looksLikePy = /^#!.*python|^import |^def |^class /m.test(s)
  const looksLikeBat = /@echo\s+off|^::|\bsetlocal\b/im.test(s)
  const detectedType = looksLikePy ? 'py' : looksLikeBat ? 'bat' : fallbackType
  const rawCode = detectedType === 'bat' ? sanitizeBatEchoLines(s) : s
  return { scriptType: detectedType, name: 'ai_script', code: rawCode, description: '' }
}

// ── Main export ──────────────────────────────────────────────────────────────

export async function callScriptAi(req: ScriptAiRequest): Promise<ScriptAiResult> {
  const systemPrompt = buildSystemPrompt(req)
  const systemRole = resolveSystemRole(req.config)

  const messages: AiChatMessage[] = [
    { role: systemRole, content: systemPrompt },
    ...req.history.slice(-4),
    { role: 'user', content: req.question },
  ]

  // Retry once on server-side 5xx errors (Azure occasionally returns 500 transiently)
  let lastError: Error | null = null
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      if (attempt > 0) await new Promise(r => setTimeout(r, 1500))
      const json = await callApi(req.config, messages)
      const raw: string = json.choices?.[0]?.message?.content || json.choices?.[0]?.text || ''
      if (!raw.trim()) throw new Error('AI returned an empty response')
      return parseResult(raw, req.scriptType)
    } catch (e: any) {
      lastError = e
      // Only retry on transient server errors, not on auth/quota/bad-request errors
      const msg: string = e?.message || ''
      const isTransient = msg.includes('internal error') || msg.includes('500') || msg.includes('503') || msg.includes('502')
      if (!isTransient) throw e
    }
  }
  throw lastError!
}
