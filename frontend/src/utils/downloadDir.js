const DB_NAME = 'video-downloader'
const STORE_NAME = 'settings'
const DIR_KEY = 'download-directory'

export const supportsDirectoryPicker =
  typeof window !== 'undefined' && typeof window.showDirectoryPicker === 'function'

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE_NAME)) {
        req.result.createObjectStore(STORE_NAME)
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function getRememberedDir() {
  try {
    const db = await openDb()
    return await new Promise((resolve, reject) => {
      const req = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).get(DIR_KEY)
      req.onsuccess = () => resolve(req.result || null)
      req.onerror = () => reject(req.error)
    })
  } catch {
    return null
  }
}

async function rememberDir(handle) {
  try {
    const db = await openDb()
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      tx.objectStore(STORE_NAME).put(handle, DIR_KEY)
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  } catch {
    // 句柄持久化失败不影响本次下载
  }
}

export async function chooseDir() {
  const handle = await window.showDirectoryPicker({
    id: 'video-download-dir',
    mode: 'readwrite',
  })
  await rememberDir(handle)
  return handle
}

export async function ensureDirPermission(handle) {
  try {
    if (await handle.queryPermission({ mode: 'readwrite' }) === 'granted') return true
    return await handle.requestPermission({ mode: 'readwrite' }) === 'granted'
  } catch {
    return false
  }
}

export async function saveBlobToDir(dirHandle, filename, blob) {
  const safeName = filename.replace(/[\\/:*?"<>|]/g, '_')
  const fileHandle = await dirHandle.getFileHandle(safeName, { create: true })
  const writable = await fileHandle.createWritable()
  try {
    await writable.write(blob)
  } finally {
    await writable.close()
  }
}
