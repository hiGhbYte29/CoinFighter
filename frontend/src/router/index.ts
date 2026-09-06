import { createRouter, createWebHashHistory } from "vue-router";

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", name: "markets", component: () => import("@/views/MarketView.vue"), meta: { title: "行情", eyebrow: "MARKET OVERVIEW" } },
    { path: "/market/:symbol", name: "market-detail", component: () => import("@/views/MarketDetailView.vue"), meta: { title: "代币详情", eyebrow: "MARKET DETAIL" } },
    { path: "/datasets", component: () => import("@/views/DatasetsView.vue"), meta: { title: "数据", eyebrow: "LOCAL DATASETS" } },
    { path: "/strategies", component: () => import("@/views/StrategiesView.vue"), meta: { title: "策略", eyebrow: "STRATEGY LAB" } },
    { path: "/backtests", component: () => import("@/views/BacktestsView.vue"), meta: { title: "回测", eyebrow: "BACKTEST STUDIO" } },
  ],
});
