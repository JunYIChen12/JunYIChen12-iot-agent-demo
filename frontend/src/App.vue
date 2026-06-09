<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const dashboard = ref<any>({
  stats: {},
  devices: [],
  latest_logs: [],
  alarms: [],
})
const loading = ref(false)
const agentInput = ref('为什么 demo-device-001 离线或告警？')
const agentAnswer = ref('')
let chart: echarts.ECharts | null = null

const latestTemperature = computed(() =>
  dashboard.value.latest_logs
    .filter((item: any) => item.identifier === 'temperature')
    .slice()
    .reverse()
)

async function refresh() {
  loading.value = true
  try {
    const res = await fetch(`${apiBase}/api/dashboard`)
    dashboard.value = await res.json()
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

async function askAgent() {
  const res = await fetch(`${apiBase}/api/agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: agentInput.value }),
  })
  const data = await res.json()
  agentAnswer.value = data.answer
}

function renderChart() {
  const el = document.getElementById('trend')
  if (!el) return
  chart = chart || echarts.init(el)
  chart.setOption({
    grid: { left: 42, right: 18, top: 24, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: latestTemperature.value.map((p: any) => new Date(p.reported_at).toLocaleTimeString()),
    },
    yAxis: { type: 'value', name: 'C' },
    series: [
      {
        name: 'temperature',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: latestTemperature.value.map((p: any) => Number(p.value)),
        areaStyle: { opacity: 0.12 },
      },
    ],
  })
}

onMounted(() => {
  refresh()
  window.setInterval(refresh, 5000)
})
</script>

<template>
  <main class="shell">
    <aside class="sidebar">
      <div class="brand">IoT Agent Demo</div>
      <nav>
        <span class="active">总览</span>
        <span>产品</span>
        <span>设备</span>
        <span>规则</span>
        <span>日志</span>
        <span>AI 助手</span>
      </nav>
    </aside>

    <section class="content">
      <header class="topbar">
        <div>
          <h1>物联网演示控制台</h1>
          <p>品类 - 产品 - 设备 - MQTT - 数据流转 - 规则告警 - AI 诊断</p>
        </div>
        <el-button :loading="loading" type="primary" @click="refresh">刷新</el-button>
      </header>

      <section class="stats-grid">
        <div class="metric">
          <span>品类</span>
          <strong>{{ dashboard.stats.categories || 0 }}</strong>
        </div>
        <div class="metric">
          <span>产品</span>
          <strong>{{ dashboard.stats.products || 0 }}</strong>
        </div>
        <div class="metric">
          <span>设备</span>
          <strong>{{ dashboard.stats.devices || 0 }}</strong>
        </div>
        <div class="metric">
          <span>在线设备</span>
          <strong>{{ dashboard.stats.online_devices || 0 }}</strong>
        </div>
        <div class="metric">
          <span>属性日志</span>
          <strong>{{ dashboard.stats.property_logs || 0 }}</strong>
        </div>
        <div class="metric warn">
          <span>告警</span>
          <strong>{{ dashboard.stats.alarms || 0 }}</strong>
        </div>
      </section>

      <section class="main-grid">
        <section class="panel wide">
          <div class="panel-head">
            <h2>温度趋势</h2>
            <span>来自 MQTT 模拟设备</span>
          </div>
          <div id="trend" class="chart"></div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>AI 助手</h2>
            <span>第一版诊断入口</span>
          </div>
          <el-input v-model="agentInput" type="textarea" :rows="3" />
          <el-button class="ask" type="primary" @click="askAgent">询问</el-button>
          <pre class="answer">{{ agentAnswer || '可以问：最近有什么告警？物模型有哪些属性？MQTT 报文怎么发？' }}</pre>
        </section>
      </section>

      <section class="main-grid lower">
        <section class="panel">
          <div class="panel-head">
            <h2>设备</h2>
            <span>在线状态</span>
          </div>
          <el-table :data="dashboard.devices" size="small" height="260">
            <el-table-column prop="device_name" label="设备名" min-width="130" />
            <el-table-column prop="status" label="状态" width="86">
              <template #default="{ row }">
                <el-tag :type="row.status === 'online' ? 'success' : 'info'">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="latest_properties.temperature" label="温度" width="80" />
            <el-table-column prop="latest_properties.humidity" label="湿度" width="80" />
          </el-table>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>最近上报</h2>
            <span>属性日志</span>
          </div>
          <el-table :data="dashboard.latest_logs" size="small" height="260">
            <el-table-column prop="identifier" label="属性" width="110" />
            <el-table-column prop="value" label="值" width="80" />
            <el-table-column prop="device_name" label="设备" min-width="130" />
          </el-table>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>告警</h2>
            <span>规则触发</span>
          </div>
          <el-table :data="dashboard.alarms" size="small" height="260">
            <el-table-column prop="device_name" label="设备" width="130" />
            <el-table-column prop="content" label="内容" min-width="220" />
          </el-table>
        </section>
      </section>
    </section>
  </main>
</template>
