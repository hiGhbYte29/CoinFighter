<script setup lang="ts">
import { CandlestickChart } from "echarts/charts";
import { DataZoomComponent, GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import type { Candle } from "@/types/api";

echarts.use([CandlestickChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer]);
const props = defineProps<{ candles: Candle[] }>();
const element = ref<HTMLDivElement>();
let chart: echarts.ECharts | undefined;

function draw() {
  if (!element.value) return;
  chart ||= echarts.init(element.value);
  chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    grid: { left: 62, right: 18, top: 16, bottom: 42 },
    tooltip: { trigger: "axis", backgroundColor: "#142022", borderColor: "#32413d", textStyle: { color: "#e8f0ed" } },
    xAxis: { type: "category", data: props.candles.map((c) => new Date(c.timestamp).toLocaleString()), axisLine: { lineStyle: { color: "#263432" } }, axisLabel: { color: "#60706b", hideOverlap: true } },
    yAxis: { scale: true, splitLine: { lineStyle: { color: "rgba(205,230,221,.07)" } }, axisLabel: { color: "#60706b" } },
    dataZoom: [{ type: "inside", start: 35, end: 100 }],
    series: [{ type: "candlestick", data: props.candles.map((c) => [c.open, c.close, c.low, c.high]), itemStyle: { color: "#5ce1a6", color0: "#ff8060", borderColor: "#5ce1a6", borderColor0: "#ff8060" } }],
  });
}
watch(() => props.candles, () => void nextTick(draw), { deep: true, immediate: true });
const resize = () => chart?.resize();
window.addEventListener("resize", resize);
onBeforeUnmount(() => { window.removeEventListener("resize", resize); chart?.dispose(); });
</script>

<template><div ref="element" class="market-chart"></div></template>
