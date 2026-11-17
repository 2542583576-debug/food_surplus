<template>
  <div class="app-shell">
    <!-- 顶部导航 -->
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand" @click="$router.push('/bags')">
          <span class="brand-mark">🌱</span>
          <span class="brand-name">惜食魔法袋</span>
          <span class="brand-slogan">让余量遇见需要</span>
        </div>

        <nav class="nav">
          <router-link v-for="item in menus" :key="item.path" :to="item.path"
                       class="nav-item" active-class="active">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </router-link>
        </nav>

        <div class="top-actions">
          <!-- 通知铃铛 -->
          <el-popover placement="bottom-end" :width="320" trigger="click" @show="loadNotifications">
            <template #reference>
              <div class="bell">
                <el-badge :value="unread" :hidden="unread === 0" :max="99">
                  <el-icon :size="20"><Bell /></el-icon>
                </el-badge>
              </div>
            </template>
            <div class="notify-panel">
              <div class="notify-head">
                <span>消息通知</span>
                <el-button link type="primary" size="small" @click="markAllRead">全部已读</el-button>
              </div>
              <div v-if="notifications.length === 0" class="notify-empty">暂无消息</div>
              <div v-for="n in notifications" :key="n.id" class="notify-item" :class="{ unread: !n.is_read }">
                <div class="notify-icon">{{ n.type === 'success' ? '✅' : '📢' }}</div>
                <div class="notify-body">
                  <div class="notify-title">{{ n.title }}</div>
                  <div class="notify-content">{{ n.content }}</div>
                  <div class="notify-time">{{ formatTime(n.create_time) }}</div>
                </div>
              </div>
            </div>
          </el-popover>

          <el-dropdown @command="handleCommand">
            <div class="user-chip">
              <div class="avatar">{{ (userStore.info?.nickname || userStore.info?.username || '游')[0] }}</div>
              <span class="user-name">{{ userStore.info?.nickname || userStore.info?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <main class="main-area">
      <router-view />
    </main>

    <footer class="footer">
      🌱 惜食余量魔法袋 · 减少食物浪费，从每一袋开始
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getNotifications, getUnreadCount, readAllNotifications } from '../api/magic'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const unread = ref(0)
const notifications = ref([])

const menus = computed(() => {
  const children = router.options.routes.find((r) => r.path === '/')?.children || []
  const isMerchant = userStore.info?.role === 1
  return children
    .filter((c) => c.meta.public || isMerchant)
    .map((c) => ({ path: `/${c.path}`, title: c.meta.title, icon: c.meta.icon }))
})

function formatTime(value) {
  return value ? String(value).slice(5, 16).replace('T', ' ') : ''
}

async function loadNotifications() {
  try {
    notifications.value = await getNotifications()
    unread.value = (await getUnreadCount()).unread
  } catch (e) { /* 忽略 */ }
}

async function markAllRead() {
  await readAllNotifications()
  unread.value = 0
  notifications.value.forEach((n) => (n.is_read = true))
}

async function refreshUnread() {
  try {
    unread.value = (await getUnreadCount()).unread
  } catch (e) { /* 忽略 */ }
}

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

onMounted(async () => {
  await userStore.fetchInfo()
  refreshUnread()
})
</script>

<style scoped>
.app-shell {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--paper);
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.topbar-inner {
  max-width: 1240px;
  margin: 0 auto;
  height: 66px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  white-space: nowrap;
}
.brand-mark { font-size: 24px; }
.brand-name { font-size: 18px; font-weight: 800; color: var(--green-700); }
.brand-slogan {
  font-size: 11px;
  color: var(--ink-mute);
  padding-left: 8px;
  border-left: 1px solid var(--line);
}
.nav {
  display: flex;
  gap: 4px;
  flex: 1;
  overflow-x: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  border-radius: 10px;
  color: var(--ink-soft);
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  transition: all 0.2s;
}
.nav-item:hover { background: var(--green-50); color: var(--green-600); }
.nav-item.active {
  background: var(--green-100);
  color: var(--green-700);
  font-weight: 600;
}
.top-actions { display: flex; align-items: center; gap: 18px; }
.bell { cursor: pointer; color: var(--ink-soft); display: flex; align-items: center; padding: 6px; }
.bell:hover { color: var(--green-600); }
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--green-400), var(--green-600));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.user-name { color: var(--ink); max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.main-area { flex: 1; }
.footer {
  text-align: center;
  padding: 22px;
  color: var(--ink-mute);
  font-size: 12px;
}

/* 通知面板 */
.notify-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}
.notify-empty { text-align: center; color: var(--ink-mute); padding: 28px 0; font-size: 13px; }
.notify-item {
  display: flex;
  gap: 10px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--line);
}
.notify-item:last-child { border-bottom: none; }
.notify-icon { font-size: 18px; }
.notify-body { flex: 1; min-width: 0; }
.notify-title { font-size: 13px; font-weight: 600; }
.notify-content { font-size: 12px; color: var(--ink-soft); line-height: 1.5; margin: 3px 0; }
.notify-time { font-size: 11px; color: var(--ink-mute); }
.notify-item.unread .notify-title { color: var(--green-600); }

@media (max-width: 900px) {
  .brand-slogan { display: none; }
  .topbar-inner { gap: 12px; padding: 0 14px; }
  .user-name { display: none; }
}
</style>
