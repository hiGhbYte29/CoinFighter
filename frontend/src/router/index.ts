import { createRouter, createWebHashHistory } from "vue-router";

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", component: () => import("@/views/MarketView.vue"), meta: { title: "实时看盘", eyebrow: "MARKET OVERVIEW" } },
    { path: "/datasets", component: () => import("@/views/DatasetsView.vue"), meta: { title: "数据管理", eyebrow: "LOCAL DATASETS" } },
    { path: "/strategies", component: () => import("@/views/StrategiesView.vue"), meta: { title: "策略实验室", eyebrow: "STRATEGY LAB" } },
    { path: "/backtests", component: () => import("@/views/BacktestsView.vue"), meta: { title: "回测分析", eyebrow: "BACKTEST STUDIO" } },
  ],
});
