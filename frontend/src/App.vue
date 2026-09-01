<template>
  <div class="min-h-screen flex flex-col bg-bg-main">
    <AppHeader
      :user="currentUser"
      @login="showAuthModal('login')"
      @register="showAuthModal('register')"
      @logout="handleLogout"
      @open-vip="handleOpenVip"
    />
    <main class="flex-1">
      <HeroSection
        @parse="handleParse"
        :loading="loading"
        :compact="!!videoData"
        :showSlogan="!videoData || demoMode"
      />
      <!-- 视频信息 + AI 总结：左右双栏同屏布局 -->
      <section v-if="videoData" class="py-4 sm:py-6 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6">
          <div class="flex flex-col lg:flex-row gap-6">
            <!-- 左栏：视频信息 -->
            <div class="w-full lg:w-2/5 lg:flex-shrink-0">
              <VideoResult
                :video="videoData"
                :downloading="downloading"
                :summarizing="summarizing"
                @download="handleDownload"
                @summarize="handleSummarize"
              />
            </div>
            <!-- 右栏：AI 总结 -->
            <div class="w-full lg:w-3/5 min-w-0">
              <VideoSummary
                :videoUrl="currentUrl"
                :videoTitle="videoData.title"
                :user="currentUser"
                :key="summaryKey"
                @loading-change="handleSummarizeLoadingChange"
                @need-login="showAuthModal('login')"
                @need-vip="handleOpenVip"
              />
            </div>
          </div>
        </div>
      </section>
      <FeatureSection />
      <HowToSection />
      <ComparisonSection />
      <PricingSection :user="currentUser" @open-vip="handleOpenVip" @need-login="showAuthModal('login')" />
      <PlatformSection />
    </main>
    <AppFooter />

    <!-- 支付成功/取消提示 -->
    <Teleport to="body">
      <div v-if="paymentToast" class="fixed top-20 left-1/2 -translate-x-1/2 z-[200] animate-toast-in">
        <div :class="[
          'flex items-center gap-3 px-6 py-4 rounded-2xl shadow-xl border',
          paymentToast === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-orange-50 border-orange-200 text-orange-800'
        ]">
          <svg v-if="paymentToast === 'success'" class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else class="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span class="font-medium text-sm">
            {{ paymentToast === 'success' ? 'VIP 开通成功！已为你激活全部高级功能' : '支付已取消，你可以随时再次开通' }}
          </span>
        </div>
      </div>
    </Teleport>

    <AuthModal
      :visible="authModalVisible"
      :initialMode="authModalMode"
      @close="authModalVisible = false"
      @success="handleAuthSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import AppHeader from './components/AppHeader.vue'
import HeroSection from './components/HeroSection.vue'
import VideoResult from './components/VideoResult.vue'
import VideoSummary from './components/VideoSummary.vue'
import FeatureSection from './components/FeatureSection.vue'
import HowToSection from './components/HowToSection.vue'
import ComparisonSection from './components/ComparisonSection.vue'
import PricingSection from './components/PricingSection.vue'
import PlatformSection from './components/PlatformSection.vue'
import AppFooter from './components/AppFooter.vue'
import AuthModal from './components/AuthModal.vue'
import { parseVideo, downloadViaServer } from './api/video.js'
import { getSavedUser, fetchMe, logout as logoutApi, isLoggedIn } from './api/auth.js'
import { createCheckoutSession } from './api/payment.js'

const demoMode = ref(false)
let enterCount = 0
let enterTimer = null

function onKeyDown(e) {
  if (e.key === 'Enter' && !e.target.matches('input, textarea, [contenteditable]')) {
    enterCount++
    clearTimeout(enterTimer)
    if (enterCount >= 3) {
      demoMode.value = !demoMode.value
      enterCount = 0
    } else {
      enterTimer = setTimeout(() => { enterCount = 0 }, 800)
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeyDown)
  restoreUser()
  checkPaymentResult()
})
onBeforeUnmount(() => { document.removeEventListener('keydown', onKeyDown) })

// ===== 用户状态管理 =====
const currentUser = ref(null)
const authModalVisible = ref(false)
const authModalMode = ref('login')

function showAuthModal(mode = 'login') {
  authModalMode.value = mode
  authModalVisible.value = true
}

function handleAuthSuccess(user) {
  currentUser.value = user
}

function handleLogout() {
  logoutApi()
  currentUser.value = null
}

async function restoreUser() {
  if (!isLoggedIn()) return
  const saved = getSavedUser()
  if (saved) currentUser.value = saved
  try {
    currentUser.value = await fetchMe()
  } catch {
    handleLogout()
  }
}

// ===== VIP 购买 =====
async function handleOpenVip() {
  if (!isLoggedIn()) {
    showAuthModal('login')
    return
  }
  try {
    const { checkout_url } = await createCheckoutSession('monthly')
    window.location.href = checkout_url
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || '创建支付失败'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
}

// ===== 支付结果处理 =====
const paymentToast = ref(null)

function checkPaymentResult() {
  const params = new URLSearchParams(window.location.search)
  const payment = params.get('payment')
  if (payment === 'success' || payment === 'cancel') {
    paymentToast.value = payment
    window.history.replaceState({}, '', window.location.pathname)
    if (payment === 'success' && isLoggedIn()) {
      setTimeout(async () => {
        try { currentUser.value = await fetchMe() } catch {}
      }, 1000)
    }
    setTimeout(() => { paymentToast.value = null }, 5000)
  }
}

// ===== 视频功能 =====
const loading = ref(false)
const downloading = ref(false)
const videoData = ref(null)
const currentUrl = ref('')
const summaryKey = ref(0)
const summarizing = ref(false)

function handleSummarize() {
  summaryKey.value++
}

function handleSummarizeLoadingChange(isLoading) {
  summarizing.value = isLoading
}

async function handleParse(url) {
  loading.value = true
  videoData.value = null
  currentUrl.value = url
  try {
    const res = await parseVideo(url)
    if (res.success) {
      videoData.value = res.data
      summaryKey.value++
    } else {
      alert('解析失败：' + (res.error || '未知错误'))
    }
  } catch (err) {
    const msg = err.response?.data?.detail?.error || err.response?.data?.detail || err.message
    alert('解析失败：' + msg)
  } finally {
    loading.value = false
  }
}

async function handleDownload(formatId) {
  downloading.value = true
  try {
    console.log('开始下载，formatId:', formatId)

    const response = await downloadViaServer(currentUrl.value, formatId)
    console.log('下载响应状态:', response.status)
    console.log('响应类型:', response.headers['content-type'])
    console.log('Content-Disposition:', response.headers['content-disposition'])

    // 获取文件名
    let filename = 'video.mp4'
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      // 尝试多种文件名匹配模式
      const patterns = [
        /filename\*?=(?:UTF-8'')?([^;\n]+)/i,
        /filename="?([^"]+)"?/i,
        /filename=([^;]+)/i
      ]

      for (const pattern of patterns) {
        const match = contentDisposition.match(pattern)
        if (match) {
          filename = decodeURIComponent(match[1].replace(/"/g, ''))
          break
        }
      }
    }

    console.log('使用文件名:', filename)

    // 创建blob
    const blob = new Blob([response.data], { type: response.headers['content-type'] || 'video/mp4' })
    console.log('Blob大小:', blob.size)

    // 方法1：使用标准下载方式
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    a.style.display = 'none'

    document.body.appendChild(a)

    // 使用dispatchEvent来模拟点击
    const clickEvent = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true
    })
    a.dispatchEvent(clickEvent)

    // 清理
    setTimeout(() => {
      document.body.removeChild(a)
      window.URL.revokeObjectURL(downloadUrl)
    }, 100)

    // 方法2：备用方案 - 检查是否真的开始下载
    setTimeout(() => {
      const activeDownloads = document.querySelectorAll('a[download]')
      if (activeDownloads.length === 0) {
        console.log('方法1失败，尝试方法2：新窗口打开')
        window.open(downloadUrl, '_blank')

        // 延长清理时间
        setTimeout(() => {
          window.URL.revokeObjectURL(downloadUrl)
        }, 5000)
      }
    }, 1000)

    // 方法3：最终备用 - 显示手动下载提示
    setTimeout(() => {
      const finalCheck = document.querySelectorAll('a[download]')
      if (finalCheck.length === 0) {
        console.log('所有自动方法都失败了，显示手动下载链接')

        // 创建下载提示
        const notice = document.createElement('div')
        notice.id = 'download-notice'
        notice.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          background: #28a745;
          color: white;
          padding: 15px;
          border-radius: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
          z-index: 10000;
          max-width: 300px;
        `
        notice.innerHTML = `
          <p style="margin: 0 0 10px 0;">📥 如果下载没有自动开始：</p>
          <a href="${downloadUrl}" download="${filename}"
             style="display: inline-block; background: white; color: #28a745;
                    padding: 8px 12px; text-decoration: none; border-radius: 4px; font-weight: bold;">
            点击手动下载
          </a>
          <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.9;">文件名：${filename}</p>
        `
        document.body.appendChild(notice)

        // 5秒后自动移除提示
        setTimeout(() => {
          const noticeEl = document.getElementById('download-notice')
          if (noticeEl && noticeEl.parentNode) {
            noticeEl.parentNode.removeChild(noticeEl)
          }
        }, 5000)
      }
    }, 2000)

  } catch (err) {
    console.error('下载失败:', err)
    alert('下载失败：' + (err.message || '请稍后重试'))
  } finally {
    downloading.value = false
  }
}
</script>

<style>
@keyframes toast-in {
  from { opacity: 0; transform: translate(-50%, -10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
.animate-toast-in {
  animation: toast-in 0.3s ease-out;
}
</style>
