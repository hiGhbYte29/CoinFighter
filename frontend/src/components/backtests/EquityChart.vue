<script setup lang="ts">
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);
const props = defineProps<{ rows: Array<Record<string, number>> }>();
const element = ref<HTMLDivElement>();
let chart: echarts.ECharts | undefined;
function draw() {
  if (!element.value) return;
  chart ||= echarts.init(element.value);
  chart.setOption({
    animationDuration: 300,
    grid: { left: 60, right: 14, top: 16, bottom: 34 },
    tooltip: { trigger: "axis", backgroundColor: "#142022", borderColor: "#32413d", textStyle: { color: "#e8f0ed" } },
    xAxis: { type: "category", data: props.rows.map((row) => new Date(row.timestamp).toLocaleDateString()), axisLabel: { color: "#60706b", hideOverlap: true }, axisLine: { lineStyle: { color: "#263432" } } },
    yAxis: { scale: true, axisLabel: { color: "#60706b" }, splitLine: { lineStyle: { color: "rgba(205,230,221,.07)" } } },
    series: [{ type: "line", data: props.rows.map((row) => row.equity), showSymbol: false, smooth: true, lineStyle: { color: "#5ce1a6", width: 2 }, areaStyle: { color: "rgba(92,225,166,.08)" } }],
  });
}
watch(() => props.rows, () => void nextTick(draw), { deep: true, immediate: true });
const resize = () => chart?.resize();
window.addEventListener("resize", resize);
onBeforeUnmount(() => { window.removeEventListener("resize", resize); chart?.dispose(); });
</script>

<template><div ref="element" class="equity-chart"></div></template>
