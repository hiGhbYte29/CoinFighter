<script setup lang="ts">
import { BarChart, CandlestickChart } from "echarts/charts";
import { DataZoomComponent, GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import type { Candle } from "@/types/api";

echarts.use([CandlestickChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer]);
const props = defineProps<{ candles: Candle[] }>();
const element = ref<HTMLDivElement>();
let chart: echarts.ECharts | undefined;

function draw() {
  if (!element.value) return;
  chart ||= echarts.init(element.value);
  const labels = props.candles.map((c) => new Date(c.timestamp).toLocaleString());
  chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    grid: [
      { left: 68, right: 18, top: 18, height: "60%" },
      { left: 68, right: 18, top: "76%", height: "14%" },
    ],
    tooltip: { trigger: "axis", backgroundColor: "#142022", borderColor: "#32413d", textStyle: { color: "#e8f0ed" } },
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    xAxis: [
      { type: "category", gridIndex: 0, data: labels, boundaryGap: true, axisLine: { lineStyle: { color: "#263432" } }, axisLabel: { show: false } },
      { type: "category", gridIndex: 1, data: labels, boundaryGap: true, axisLine: { lineStyle: { color: "#263432" } }, axisLabel: { color: "#60706b", hideOverlap: true } },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: "rgba(205,230,221,.07)" } }, axisLabel: { color: "#60706b" } },
      { scale: true, gridIndex: 1, splitNumber: 2, splitLine: { show: false }, axisLabel: { color: "#60706b", formatter: (value: number) => Intl.NumberFormat("en", { notation: "compact" }).format(value) } },
    ],
    dataZoom: [{ type: "inside", xAxisIndex: [0, 1], start: 35, end: 100 }],
    series: [
      { name: "K 线", type: "candlestick", xAxisIndex: 0, yAxisIndex: 0, data: props.candles.map((c) => [c.open, c.close, c.low, c.high]), itemStyle: { color: "#5ce1a6", color0: "#ff8060", borderColor: "#5ce1a6", borderColor0: "#ff8060" } },
      { name: "成交量", type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: props.candles.map((c) => ({ value: c.volume, itemStyle: { color: c.close >= c.open ? "rgba(92,225,166,.5)" : "rgba(255,128,96,.5)" } })) },
    ],
  });
}
watch(() => props.candles, () => void nextTick(draw), { deep: true, immediate: true });
const resize = () => chart?.resize();
window.addEventListener("resize", resize);
onBeforeUnmount(() => { window.removeEventListener("resize", resize); chart?.dispose(); });
</script>

<template><div ref="element" class="market-chart"></div></template>
