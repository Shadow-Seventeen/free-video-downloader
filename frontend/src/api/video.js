import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function parseVideo(url) {
  const { data } = await api.post('/parse', { url })
  return data
}

export async function getDirectUrl(url, formatId) {
  const { data } = await api.post('/direct-url', { url, format_id: formatId })
  return data
}

export function getDownloadUrl() {
  return '/api/download'
}

export async function downloadViaServer(url, formatId) {
  try {
    const response = await api.post(
      '/download',
      { url, format_id: formatId },
      {
        responseType: 'blob',
        timeout: 600000,
        headers: {
          'Accept': 'application/octet-stream',
        }
      }
    )
    return response
  } catch (error) {
    console.error('下载请求失败:', error)
    throw error
  }
}
