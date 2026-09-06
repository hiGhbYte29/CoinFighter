<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { api } from "@/api/client";

const route = useRoute();
const apiReady = ref(false);

onMounted(async () => {
  try {
    await api<{ status: string }>("/health/live");
    apiReady.value = true;
  } catch {
    apiReady.value = false;
  }
});

const navigation = [
  { to: "/", index: "01", label: "实时看盘" },
  { to: "/datasets", index: "02", label: "数据管理" },
  { to: "/strategies", index: "03", label: "策略实验室" },
  { to: "/backtests", index: "04", label: "回测分析" },
];
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">CF</span>
        <div>
          <strong>CoinFighter</strong>
          <small>Research Terminal</small>
        </div>
      </div>
      <nav aria-label="主导航">
        <RouterLink v-for="item in navigation" :key="item.to" :to="item.to" class="nav-item">
          <span>{{ item.index }}</span>{{ item.label }}
        </RouterLink>
      </nav>
      <div class="sidebar-status">
        <span class="status-dot" :class="{ online: apiReady }"></span>
        <div><strong>LOCAL</strong><small>{{ apiReady ? "服务已连接" : "等待后端服务" }}</small></div>
      </div>
    </aside>

    <main>
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ route.meta.eyebrow || "RESEARCH TERMINAL" }}</p>
          <h1>{{ route.meta.title || "CoinFighter" }}</h1>
        </div>
        <div class="top-actions">
          <span class="clock">UTC+8 · LOCAL</span>
          <RouterLink class="primary-button" to="/backtests">+ 新建回测</RouterLink>
        </div>
      </header>
      <RouterView />
      <footer><span>CoinFighter v0.1</span><span>本地优先 · 数据由你掌控</span></footer>
    </main>
  </div>
</template>
