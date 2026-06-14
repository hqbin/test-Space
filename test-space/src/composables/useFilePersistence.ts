export interface FileContent {
  id?: string
  version?: string
  name: string
  cases: any[]
  ruleSetId?: string
  tags?: string[]
  customFields?: any[]
  createdAt?: string
  updatedAt: string
}

function isTauri(): boolean {
  return typeof window !== 'undefined' && (window as any).__TAURI__ !== undefined
}

export function useFilePersistence() {

  async function pickSavePath(defaultName?: string): Promise<string | null> {
    if (isTauri()) {
      try {
        const { save } = await import('@tauri-apps/plugin-dialog')
        const result = await save({
          filters: [
            { name: 'Test Space Case File', extensions: ['tc', 'json'] },
            { name: 'Excel Workbook', extensions: ['xlsx'] },
            { name: 'PNG Image', extensions: ['png'] },
          ],
          defaultPath: defaultName || 'untitled.tc',
        })
        return result || null
      } catch { return null }
    }
    return null
  }

  async function pickOpenPath(): Promise<string | null> {
    if (isTauri()) {
      try {
        const { open } = await import('@tauri-apps/plugin-dialog')
        const result = await open({
          filters: [
            { name: 'Test Space Case File', extensions: ['tc', 'json'] },
          ],
          multiple: false,
        })
        return (result as string) || null
      } catch { return null }
    }
    return null
  }

  async function readFile(path: string): Promise<FileContent | null> {
    try {
      let json: string
      if (isTauri()) {
        const { readTextFile } = await import('@tauri-apps/plugin-fs')
        json = await readTextFile(path)
      } else {
        json = localStorage.getItem('test-space:dev:' + path) || ''
      }
      if (!json) return null
      return JSON.parse(json) as FileContent
    } catch (err) {
      console.error('Read failed:', err)
      return null
    }
  }

  async function writeFile(path: string, data: any): Promise<boolean> {
    try {
      if (isTauri()) {
        if (data instanceof Blob || data instanceof Uint8Array || data instanceof ArrayBuffer) {
          const { writeFile: fsWrite } = await import('@tauri-apps/plugin-fs')
          const bytes = data instanceof Blob
            ? new Uint8Array(await data.arrayBuffer())
            : data instanceof ArrayBuffer
              ? new Uint8Array(data)
              : data
          await fsWrite(path, bytes)
        } else {
          const { writeTextFile } = await import('@tauri-apps/plugin-fs')
          await writeTextFile(path, JSON.stringify(data, null, 2))
        }
      } else {
        if (data instanceof Blob || data instanceof Uint8Array || data instanceof ArrayBuffer) {
          const blob = data instanceof Blob ? data : new Blob([data])
          localStorage.setItem('test-space:dev:' + path, 'BINARY:' + (await blob.text()))
        } else {
          localStorage.setItem('test-space:dev:' + path, JSON.stringify(data))
        }
      }
      return true
    } catch (err) {
      console.error('Write failed:', err)
      return false
    }
  }

  async function openFileDialog(): Promise<{ path: string; content: FileContent } | null> {
    const path = await pickOpenPath()
    if (!path) return null
    const content = await readFile(path)
    if (!content) return null
    return { path, content }
  }

  async function saveFileDialog(path: string | null, data: FileContent): Promise<string | null> {
    if (!path) {
      path = await pickSavePath((data.name || 'untitled') + '.tc')
      if (!path) return null
    }
    const ok = await writeFile(path, { ...data, updatedAt: new Date().toISOString() })
    if (!ok) return null
    return path
  }

  return {
    pickSavePath,
    pickOpenPath,
    readFile,
    writeFile,
    openFileDialog,
    saveFileDialog,
  }
}
