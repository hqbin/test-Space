<template>
  <div>
    <div class="flex justify-between items-end mb-8">
      <div>
        <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight">Data Analytics</h2>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Monitor usage trends and user behavior.</p>
      </div>
      <div class="flex gap-2">
        <div class="relative">
          <select v-model="selectedDays" class="glass-input rounded-lg px-4 py-2 font-label-md text-label-md text-on-surface focus:outline-none appearance-none pr-8 bg-white/40" @change="reloadCharts">
            <option :value="7">Last 7 days</option>
            <option :value="30">Last 30 days</option>
            <option :value="90">Last quarter</option>
          </select>
          <span class="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-[16px] pointer-events-none">expand_more</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-gutter-grid mb-8">
      <div v-for="stat in stats" :key="stat.label" class="glass-card rounded-xl p-6">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-on-surface-variant text-[20px]">{{ stat.icon }}</span>
          <span class="font-label-md text-label-md text-on-surface-variant">{{ stat.label }}</span>
        </div>
        <p class="font-display-lg text-display-lg font-semibold text-on-surface">{{ stat.value }}</p>
        <p class="font-caption text-caption" :class="stat.trend >= 0 ? 'text-success-indicator' : 'text-error'">
          {{ stat.trend >= 0 ? '+' : '' }}{{ stat.trend }}% vs last period
        </p>
      </div>
    </div>

    <div class="glass-card rounded-xl p-padding-card mb-8">
      <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Usage Trends</h3>
      <div ref="trendChartRef" class="h-80 w-full"></div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-gutter-grid">
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-4">Feature Usage</h3>
        <div class="space-y-4">
          <div v-for="feature in features" :key="feature.name" class="flex items-center justify-between">
            <span class="font-body-md text-body-md text-on-surface">{{ feature.name }}</span>
            <div class="flex items-center gap-3">
              <div class="w-32 h-1.5 bg-surface-variant rounded-full overflow-hidden">
                <div class="h-full bg-secondary rounded-full" :style="{ width: feature.percent + '%' }"></div>
              </div>
              <span class="font-label-md text-label-md text-on-surface-variant w-10 text-right">{{ feature.percent }}%</span>
            </div>
          </div>
        </div>
      </div>
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-4">Active Users</h3>
        <div ref="usersChartRef" class="h-56 w-full"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as echarts from "echarts";
import { fetchAnalyticsStats, fetchFeatureUsage, fetchUsageTrend, fetchActiveUsers } from "@/api/analytics";

const selectedDays = ref(7);
const trendChartRef = ref<HTMLDivElement>();
const usersChartRef = ref<HTMLDivElement>();
let trendChart: echarts.ECharts | null = null;
let usersChart: echarts.ECharts | null = null;

const stats = ref([
  { icon: "visibility", label: "Page Views", value: "12,847", trend: 12.5 },
  { icon: "person", label: "Active Users", value: "1,423", trend: 8.2 },
  { icon: "touch_app", label: "Interactions", value: "48,291", trend: -3.1 },
  { icon: "schedule", label: "Avg. Session", value: "4m 32s", trend: 5.7 },
]);

const features = ref<{ name: string; percent: number }[]>([
  { name: "Test Case Management", percent: 85 },
  { name: "Test Execution", percent: 62 },
  { name: "Report Generation", percent: 43 },
  { name: "Device Management", percent: 71 },
  { name: "Database Query", percent: 28 },
]);

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 1000).toFixed(1) + "k";
  return n.toLocaleString();
}

function generateMockTrendData(days: number): { dates: string[]; pageViews: number[]; interactions: number[] } {
  const dates: string[] = [];
  const pageViews: number[] = [];
  const interactions: number[] = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().slice(0, 10));
    pageViews.push(Math.floor(800 + Math.random() * 1200));
    interactions.push(Math.floor(200 + Math.random() * 800));
  }
  return { dates, pageViews, interactions };
}

function generateMockUsersData(days: number): { dates: string[]; values: number[] } {
  const dates: string[] = [];
  const values: number[] = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().slice(0, 10));
    values.push(Math.floor(80 + Math.random() * 120));
  }
  return { dates, values };
}

function renderTrendChart(data: { dates: string[]; pageViews: number[]; interactions: number[] }) {
  if (!trendChartRef.value) return;
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value);
  }
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Page Views", "Interactions"], bottom: 0, icon: "circle" },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "category", data: data.dates, axisLabel: { fontSize: 11, color: "#6b6f82" }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#e4e5e7", type: "dashed" } }, axisLabel: { fontSize: 11, color: "#6b6f82" } },
    series: [
      { name: "Page Views", type: "line", smooth: true, data: data.pageViews, symbol: "none", lineStyle: { color: "#0050cb", width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(0,80,203,0.12)" }, { offset: 1, color: "rgba(0,80,203,0)" }]) } },
      { name: "Interactions", type: "line", smooth: true, data: data.interactions, symbol: "none", lineStyle: { color: "#4c4aca", width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(76,74,202,0.08)" }, { offset: 1, color: "rgba(76,74,202,0)" }]) } },
    ],
  });
}

function renderUsersChart(data: { dates: string[]; values: number[] }) {
  if (!usersChartRef.value) return;
  if (!usersChart) {
    usersChart = echarts.init(usersChartRef.value);
  }
  usersChart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: "category", data: data.dates, axisLabel: { fontSize: 10, color: "#6b6f82" }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#e4e5e7", type: "dashed" } }, axisLabel: { fontSize: 11, color: "#6b6f82" } },
    series: [
      { type: "line", smooth: true, data: data.values, symbol: "circle", symbolSize: 4, lineStyle: { color: "#4c4aca", width: 2 }, itemStyle: { color: "#4c4aca" }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(76,74,202,0.2)" }, { offset: 1, color: "rgba(76,74,202,0)" }]) } },
    ],
  });
}

async function reloadCharts() {
  try {
    const trendData = await fetchUsageTrend({ days: selectedDays.value });
    renderTrendChart({ dates: trendData.map((d) => d.date), pageViews: trendData.map((d) => d.value), interactions: trendData.map((d) => Math.floor(d.value * 0.6)) });
  } catch {
    const mock = generateMockTrendData(selectedDays.value);
    renderTrendChart(mock);
  }
  try {
    const usersData = await fetchActiveUsers({ days: selectedDays.value });
    renderUsersChart({ dates: usersData.map((d) => d.date), values: usersData.map((d) => d.value) });
  } catch {
    const mock = generateMockUsersData(selectedDays.value);
    renderUsersChart(mock);
  }
}

onMounted(async () => {
  try {
    const s = await fetchAnalyticsStats();
    stats.value = [
      { icon: "visibility", label: "Page Views", value: formatNumber(s.pageViews), trend: s.pageViewsTrend },
      { icon: "person", label: "Active Users", value: formatNumber(s.activeUsers), trend: s.activeUsersTrend },
      { icon: "touch_app", label: "Interactions", value: formatNumber(s.interactions), trend: s.interactionsTrend },
      { icon: "schedule", label: "Avg. Session", value: `${Math.floor(s.avgSession / 60)}m ${s.avgSession % 60}s`, trend: s.avgSessionTrend },
    ];
  } catch {}
  try {
    const f = await fetchFeatureUsage();
    features.value = f.map((item) => ({ name: item.name, percent: Math.round((item.usage / item.total) * 100) }));
  } catch {}
  await nextTick();
  await reloadCharts();
});

onBeforeUnmount(() => {
  trendChart?.dispose();
  usersChart?.dispose();
});
</script>
