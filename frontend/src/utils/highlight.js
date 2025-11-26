/**
 * 搜索结果高亮工具
 */

/**
 * 高亮文本中的关键词
 * @param {string} text - 原始文本
 * @param {string} keyword - 关键词
 * @param {string} className - 高亮样式类名
 * @returns {string} HTML 字符串
 */
export function highlightText(text, keyword, className = 'highlight') {
  if (!text || !keyword) return text

  const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi')
  return text.replace(regex, `<span class="${className}">$1</span>`)
}

/**
 * 转义正则表达式特殊字符
 * @param {string} string
 * @returns {string}
 */
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 截取包含关键词的文本片段
 * @param {string} text - 原始文本
 * @param {string} keyword - 关键词
 * @param {number} contextLength - 上下文长度
 * @returns {string}
 */
export function excerptText(text, keyword, contextLength = 50) {
  if (!text || !keyword) return text

  const index = text.toLowerCase().indexOf(keyword.toLowerCase())
  if (index === -1) {
    return text.length > contextLength * 2
      ? text.substring(0, contextLength * 2) + '...'
      : text
  }

  const start = Math.max(0, index - contextLength)
  const end = Math.min(text.length, index + keyword.length + contextLength)

  let excerpt = text.substring(start, end)
  if (start > 0) excerpt = '...' + excerpt
  if (end < text.length) excerpt = excerpt + '...'

  return excerpt
}

/**
 * 组合：截取并高亮
 * @param {string} text - 原始文本
 * @param {string} keyword - 关键词
 * @param {number} contextLength - 上下文长度
 * @param {string} className - 高亮样式类名
 * @returns {string} HTML 字符串
 */
export function highlightExcerpt(text, keyword, contextLength = 50, className = 'highlight') {
  const excerpt = excerptText(text, keyword, contextLength)
  return highlightText(excerpt, keyword, className)
}
