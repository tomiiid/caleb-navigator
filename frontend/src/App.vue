<template>
  <div id="app">
    <nav class="navbar" v-if="auth.isAuthenticated">
      <div class="nav-brand">
        <span class="nav-logo">📍</span>
        <span class="nav-title">Caleb Navigator</span>
      </div>
      <div class="nav-actions">
        <span class="nav-user">{{ auth.user?.full_name || auth.user?.email }}</span>
        <button class="btn-logout" @click="auth.logout(); $router.push('/login')">
          Logout
        </button>
      </div>
    </nav>
    <RouterView />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

onMounted(() => {
  if (auth.isAuthenticated) {
    auth.fetchUser()
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', sans-serif;
  background: #f0f2f5;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #1a3a5c;
  color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1000;
  flex-shrink: 0;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-logo { font-size: 20px; }

.nav-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-user {
  font-size: 14px;
  opacity: 0.85;
}

.btn-logout {
  background: rgba(255,255,255,0.15);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.btn-logout:hover {
  background: rgba(255,255,255,0.25);
}
</style>