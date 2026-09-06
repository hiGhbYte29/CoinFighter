<script setup lang="ts">
import { BarChart, CandlestickChart, LineChart, ScatterChart } from "echarts/charts";
import {
  AxisPointerComponent,
  DataZoomComponent,
  GridComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

import type { ConfiguredIndicator } from "@/indicators/config";
import type { Candle, IndicatorOutput, IndicatorPlot } from "@/types/api";

echarts.use([
  CandlestickChart,
  BarChart,
  LineChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  AxisPointerComponent,
  MarkLineComponent,
  TitleComponent,
  CanvasRenderer,
]);

const props = defineProps<{
  candles: Candle[];
  indicators: IndicatorOutput[];
  configs: ConfiguredIndicator[];
}>();
const element = ref<HTMLDivElement>();
let chart: echarts.ECharts | undefined;
let observer: ResizeObserver | undefined;
let zoom = { start: 35, end: 100 };
let layoutSignature = "";

const subIndicators = computed(() => props.indicators.filter((item) => item.placement === "sub"));
const chartHeight = computed(() => 430 + subIndicators.value.length * 158);

function currentValue(plot: IndicatorPlot): string {
  const value = [...plot.values].reverse().find((item) => item != null);
  if (value == null) return "—";
  const absolute = Math.abs(value);
  const digits = absolute >= 1000 ? 2 : absolute >= 1 ? 3 : 6;
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function indicatorTitle(output: IndicatorOutput): string {
  const values = output.plots.map((plot) => `${plot.label} ${currentValue(plot)}`).join("   ");
  return `${output.indicator_id.toUpperCase()}  ${values}`;
}

function plotStyle(output: IndicatorOutput, plot: IndicatorPlot) {
  const config = props.configs.find((item) => item.instance_id === output.instance_id);
  return config?.styles[plot.key] || { color: plot.color, lineStyle: "solid" as const };
}

function barData(output: IndicatorOutput, plot: IndicatorPlot) {
  return plot.values.map((value, index) => {
    let color = value != null && value >= 0
      ? "rgba(92,225,166,.58)"
      : "rgba(255,128,96,.58)";
    if (output.indicator_id === "vol") {
      const candle = props.candles[index];
      color = candle?.close >= candle?.open
        ? "rgba(92,225,166,.5)"
        : "rgba(255,128,96,.5)";
    }
    return { value, itemStyle: { color } };
  });
}

function plotSeries(output: IndicatorOutput, plot: IndicatorPlot, axisIndex: number) {
  const style = plotStyle(output, plot);
  const common = {
    id: `${output.instance_id}:${plot.key}`,
    name: plot.label,
    xAxisIndex: axisIndex,
    yAxisIndex: axisIndex,
    animation: false,
    data: plot.values,
  };
  if (plot.render_type === "bar") {
    return { ...common, type: "bar", data: barData(output, plot), barMaxWidth: 7 };
  }
  if (plot.render_type === "scatter") {
    return {
      ...common,
      type: "scatter",
      symbolSize: 5,
      itemStyle: { color: style.color },
    };
  }
  return {
    ...common,
    type: "line",
    showSymbol: false,
    connectNulls: false,
    lineStyle: { width: 1.35, color: style.color, type: style.lineStyle },
    itemStyle: { color: style.color },
    markLine: output.guides.length ? {
      silent: true,
      symbol: "none",
      label: { show: false },
      lineStyle: { color: "rgba(176,194,188,.35)", type: "dashed", width: 1 },
      data: output.guides.map((guide) => ({ yAxis: guide.value })),
    } : undefined,
  };
}

function draw() {
  if (!element.value) return;
  chart ||= echarts.init(element.value);
  const labels = props.candles.map((candle) => new Date(candle.timestamp).toLocaleString());
  const mainIndicators = props.indicators.filter((item) => item.placement === "main");
  const sub = subIndicators.value;
  const mainTop = 46;
  const mainHeight = 330;
  const paneGap = 42;
  const paneHeight = 116;
  const grids: Record<string, unknown>[] = [
    { left: 68, right: 18, top: mainTop, height: mainHeight },
  ];
  sub.forEach((_, index) => grids.push({
    left: 68,
    right: 18,
    top: mainTop + mainHeight + paneGap + index * (paneHeight + paneGap),
    height: paneHeight,
  }));
  const xAxes = grids.map((_, index) => ({
    type: "category",
    gridIndex: index,
    data: labels,
    boundaryGap: true,
    axisLine: { lineStyle: { color: "#263432" } },
    axisTick: { show: false },
    axisLabel: {
      show: index === grids.length - 1,
      color: "#60706b",
      hideOverlap: true,
    },
  }));
  const yAxes = grids.map((_, index) => {
    const output = index > 0 ? sub[index - 1] : undefined;
    return {
      scale: output?.axis_min == null && output?.axis_max == null,
      min: output?.axis_min ?? undefined,
      max: output?.axis_max ?? undefined,
      gridIndex: index,
      splitNumber: index === 0 ? 5 : 3,
      splitLine: { lineStyle: { color: "rgba(205,230,221,.07)" } },
      axisLabel: {
        color: "#60706b",
        formatter: (value: number) => Math.abs(value) >= 10_000
          ? Intl.NumberFormat("en", { notation: "compact" }).format(value)
          : value.toLocaleString(undefined, { maximumFractionDigits: 2 }),
      },
    };
  });
  const titles = [
    ...(mainIndicators.length ? [{
      text: mainIndicators.map(indicatorTitle).join("   "),
      left: 68,
      top: 7,
      textStyle: {
        color: "#9aaba5",
        fontSize: 10,
        fontWeight: 400,
        fontFamily: "monospace",
      },
    }] : []),
    ...sub.map((output, index) => ({
      text: indicatorTitle(output),
      left: 68,
      top: mainTop + mainHeight + 17 + index * (paneHeight + paneGap),
      textStyle: {
        color: "#9aaba5",
        fontSize: 10,
        fontWeight: 400,
        fontFamily: "monospace",
      },
    })),
  ];
  const series: Record<string, unknown>[] = [
    {
      id: "candles",
      name: "K 线",
      type: "candlestick",
      xAxisIndex: 0,
      yAxisIndex: 0,
      animation: false,
      data: props.candles.map((candle) => [
        candle.open,
        candle.close,
        candle.low,
        candle.high,
      ]),
      itemStyle: {
        color: "#5ce1a6",
        color0: "#ff8060",
        borderColor: "#5ce1a6",
        borderColor0: "#ff8060",
      },
    },
  ];
  mainIndicators.forEach((output) => {
    output.plots.forEach((plot) => series.push(plotSeries(output, plot, 0)));
  });
  sub.forEach((output, index) => {
    output.plots.forEach((plot) => series.push(plotSeries(output, plot, index + 1)));
  });

  const nextLayoutSignature = [
    grids.length,
    ...series.map((item) => `${String(item.id)}:${String(item.type)}`),
  ].join("|");
  const rebuildLayout = nextLayoutSignature !== layoutSignature;
  layoutSignature = nextLayoutSignature;

  chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    title: titles,
    grid: grids,
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "line" },
      backgroundColor: "#142022",
      borderColor: "#32413d",
      textStyle: { color: "#e8f0ed", fontSize: 10 },
    },
    xAxis: xAxes,
    yAxis: yAxes,
    dataZoom: [{
      type: "inside",
      xAxisIndex: grids.map((_, index) => index),
      ...zoom,
    }],
    series,
  }, { notMerge: rebuildLayout, lazyUpdate: true });
}

watch(
  () => [props.candles, props.indicators, props.configs],
  () => void nextTick(draw),
  { immediate: true },
);
watch(chartHeight, () => void nextTick(() => chart?.resize()));

watch(element, (value) => {
  if (!value) return;
  observer = new ResizeObserver(() => chart?.resize());
  observer.observe(value);
  void nextTick(() => {
    draw();
    chart?.on("datazoom", () => {
      const option = chart?.getOption();
      const current = Array.isArray(option?.dataZoom)
        ? option.dataZoom[0] as { start?: number; end?: number }
        : undefined;
      if (current?.start != null && current?.end != null) {
        zoom = { start: current.start, end: current.end };
      }
    });
  });
});

onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <div ref="element" class="market-chart" :style="{ height: `${chartHeight}px` }"></div>
</template>
