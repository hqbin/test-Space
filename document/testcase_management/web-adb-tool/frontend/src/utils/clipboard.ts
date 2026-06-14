/**
 * 复制文本到剪贴板
 * 支持 HTTPS 和 HTTP 环境
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // 方法 1: 使用现代 Clipboard API（仅 HTTPS 或 localhost）
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.warn('Clipboard API failed, falling back to execCommand', error);
    }
  }

  // 方法 2: 降级到 document.execCommand（兼容 HTTP）
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // 使文本区域不可见
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    textArea.style.opacity = '0';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    
    return successful;
  } catch (error) {
    console.error('Failed to copy text to clipboard', error);
    return false;
  }
}
