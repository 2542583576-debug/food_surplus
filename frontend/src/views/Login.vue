<template>
  <div class="login-page">
    <div class="login-card fade-up">
      <!-- 左侧品牌故事 -->
      <div class="brand-panel">
        <div class="brand-logo">
          <span class="logo-icon">🌱</span>
          <span>惜食魔法袋</span>
        </div>
        <h1>把余量，变成心意</h1>
        <p class="brand-lead">
          每天打烊前，商家把当天没卖完、
          却依然新鲜的食物装进"魔法袋"，
          以超值价格送给需要的人。
        </p>
        <ul class="brand-points">
          <li><span>🥖</span> 花更少的钱，收获新鲜食物</li>
          <li><span>🌍</span> 减少浪费，为地球减一点碳</li>
          <li><span>🏪</span> 到店自提，简单又方便</li>
        </ul>
        <div class="brand-quote">"每一袋，都是一次对浪费说不。"</div>
        <div class="decor decor-1">🥐</div>
        <div class="decor decor-2">🍎</div>
        <div class="decor decor-3">🥗</div>
      </div>

      <!-- 右侧表单 -->
      <div class="form-panel">
        <div class="form-head">
          <h2>欢迎来到惜食</h2>
          <p>登录后即可预订属于你的魔法袋</p>
        </div>

        <el-tabs v-model="activeTab" stretch class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" @keyup.enter="handleLogin">
              <el-form-item>
                <el-input v-model="loginForm.username" placeholder="用户名" size="large" clearable>
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="loginForm.password" type="password" placeholder="密码"
                          size="large" show-password clearable>
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleLogin">
                登 录
              </el-button>
            </el-form>
            <div class="demo-tip">
              <span>体验账号</span>
              <el-button link type="primary" @click="fillDemo('user', 'user123')">顾客 user</el-button>
              <el-button link type="primary" @click="fillDemo('admin', 'admin123')">商家 admin</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="regForm" @keyup.enter="handleRegister">
              <el-form-item>
                <el-input v-model="regForm.username" placeholder="用户名（字母/数字/下划线）" size="large" clearable>
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="regForm.nickname" placeholder="昵称" size="large" clearable>
                  <template #prefix><el-icon><EditPen /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="regForm.password" type="password" placeholder="密码（至少6位）"
                          size="large" show-password clearable>
                  <template #prefix><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-input v-model="regForm.phone" placeholder="手机号（选填）" size="large" clearable>
                  <template #prefix><el-icon><Iphone /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleRegister">
                注 册
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    <p class="footer-note">惜食余量魔法袋 · 让每一份食物都不被辜负</p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', nickname: '', password: '', phone: '' })

function fillDemo(username, password) {
  loginForm.username = username
  loginForm.password = password
  activeTab.value = 'login'
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await login(loginForm)
    userStore.setToken(data.access_token)
    await userStore.fetchInfo()
    ElMessage.success('欢迎回来！')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!regForm.username || regForm.password.length < 6) {
    ElMessage.warning('用户名必填，密码至少6位')
    return
  }
  loading.value = true
  try {
    await register(regForm)
    ElMessage.success('注册成功，现在可以登录了')
    fillDemo(regForm.username, regForm.password)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background:
    radial-gradient(circle at 15% 20%, #dcf2e2 0%, transparent 40%),
    radial-gradient(circle at 85% 80%, #fdf0dc 0%, transparent 45%),
    linear-gradient(135deg, #f0f9f2 0%, #f7fbf5 100%);
}
.login-card {
  width: min(900px, 96%);
  min-height: 520px;
  display: flex;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(39, 138, 81, 0.14);
  background: #fff;
}
.brand-panel {
  position: relative;
  flex: 1.05;
  padding: 48px 44px;
  color: #fff;
  background: linear-gradient(150deg, #2f9e60 0%, #278a51 55%, #1e6b3e 100%);
  overflow: hidden;
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 40px;
}
.logo-icon { font-size: 26px; }
.brand-panel h1 {
  font-size: 34px;
  line-height: 1.3;
  margin: 0 0 18px;
  letter-spacing: 1px;
}
.brand-lead {
  font-size: 14px;
  line-height: 1.9;
  opacity: 0.92;
  margin: 0 0 24px;
}
.brand-points {
  list-style: none;
  padding: 0;
  margin: 0 0 28px;
  font-size: 14px;
  line-height: 2.4;
}
.brand-points span { margin-right: 8px; }
.brand-quote {
  display: inline-block;
  font-size: 13px;
  padding: 10px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  letter-spacing: 0.5px;
}
.decor {
  position: absolute;
  font-size: 60px;
  opacity: 0.16;
  pointer-events: none;
}
.decor-1 { right: -10px; top: 40px; transform: rotate(18deg); }
.decor-2 { right: 60px; bottom: 20px; font-size: 46px; }
.decor-3 { left: -20px; bottom: 60px; font-size: 52px; transform: rotate(-20deg); }

.form-panel {
  flex: 1;
  padding: 48px 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-head h2 {
  margin: 0 0 6px;
  font-size: 26px;
  color: var(--ink);
}
.form-head p {
  margin: 0 0 24px;
  font-size: 13px;
  color: var(--ink-mute);
}
.login-tabs :deep(.el-tabs__header) { margin-bottom: 24px; }
.submit-btn {
  width: 100%;
  margin-top: 6px;
  height: 44px;
  background: linear-gradient(135deg, #57bd7d, #278a51);
  border: none;
  font-weight: 600;
  letter-spacing: 4px;
}
.demo-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: var(--ink-mute);
}
.demo-tip span { margin-right: 6px; }
.footer-note {
  margin: 22px 0 0;
  font-size: 12px;
  color: var(--ink-mute);
}
@media (max-width: 760px) {
  .login-card { flex-direction: column; }
  .brand-panel { padding: 32px; }
  .brand-panel h1 { font-size: 26px; }
  .form-panel { padding: 32px; }
}
</style>
