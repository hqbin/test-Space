/**
 * 将备注文本中的PR号转为可点击链接
 * 匹配规则：PR 后紧跟恰好6位数字（如 PR #333398、PR333398、PR #333398）
 */
export function renderRemarkWithPR(text) {
  if (!text) return ''
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escaped.replace(/PR\s*[#＃]?\s*(\d{6})(?!\d)/gi, (match, prId) => {
    return `<a href="https://zmind.whaletv.com/issues/${prId}" target="_blank" rel="noopener noreferrer" class="pr-link-inline" onclick="event.stopPropagation()">${match}</a>`
  })
}
