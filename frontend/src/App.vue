<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const activeView = ref('overview')
const loading = ref(false)
const saving = ref(false)
const agentInput = ref('为什么 demo-device-001 告警？')
const agentAnswer = ref('')
const notice = ref('')

const dashboard = ref<any>({ stats: {}, devices: [], latest_logs: [], alarms: [] })
const categories = ref<any[]>([])
const products = ref<any[]>([])
const devices = ref<any[]>([])
const categoryThingModels = ref<any[]>([])
const thingModels = ref<any[]>([])
const effectiveThingModels = ref<any[]>([])
const rules = ref<any[]>([])
const selectedDeviceId = ref<number | null>(null)
const selectedDeviceName = ref('')
const deviceHistory = ref<any[]>([])
const deviceDetail = ref<any | null>(null)
const deviceDetailTab = ref('properties')
const selectedProperty = ref('')
const propertyHistory = ref<any[]>([])
const messageLogs = ref<any[]>([])

const categoryForm = reactive({ name: '演示传感器品类', industry: '智能工业', scene: '环境监测' })
const productForm = reactive({ category_id: 1, product_key: 'TEMP_SENSOR_002', name: '演示温湿度传感器', protocol: 'mqtt' })
const deviceForm = reactive({ product_id: 1, device_name: 'demo-device-002', device_secret: 'demo-secret-002', unique_no: 'SN-DEMO-002' })
const categoryModelForm = reactive({ category_id: 1, identifier: 'temperature', name: '温度', model_type: 'property', data_type: 'float', unit: 'C', access_mode: 'read', required: true })
const productModelForm = reactive({ product_id: 1, identifier: 'battery', name: '电量', model_type: 'property', data_type: 'int', unit: '%', access_mode: 'read' })
const ruleForm = reactive({ product_id: 1, name: '温度过高告警', identifier: 'temperature', operator: '>', threshold: 50, message: '温度超过 50C，请检查设备环境', enabled: true })

let chart: echarts.ECharts | null = null
let refreshTimer: number | undefined

const navItems = [
  { key: 'overview', label: '总览' },
  { key: 'categories', label: '品类' },
  { key: 'products', label: '产品' },
  { key: 'devices', label: '设备' },
  { key: 'models', label: '物模型' },
  { key: 'rules', label: '规则' },
  { key: 'logs', label: '日志' },
  { key: 'agent', label: 'AI 助手' },
]

const latestTemperature = computed(() =>
  dashboard.value.latest_logs
    .filter((item: any) => item.identifier === 'temperature')
    .slice()
    .reverse()
)

async function fetchJson(path: string, options?: RequestInit) {
  const res = await fetch(`${apiBase}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data?.detail?.errors?.join('；') || data?.detail || '请求失败')
  return data
}

async function refresh() {
  loading.value = true
  try {
    const [dashboardData, categoryData, productData, deviceData, categoryModelData, productModelData, ruleData] =
      await Promise.all([
        fetchJson('/api/dashboard'),
        fetchJson('/api/categories'),
        fetchJson('/api/products'),
        fetchJson('/api/devices'),
        fetchJson('/api/category-thing-models'),
        fetchJson('/api/thing-models'),
        fetchJson('/api/rules'),
      ])

    dashboard.value = dashboardData
    categories.value = categoryData
    products.value = productData
    devices.value = deviceData
    categoryThingModels.value = categoryModelData
    thingModels.value = productModelData
    rules.value = ruleData
    syncDefaultIds()
    await loadEffectiveThingModels()
    if (selectedDeviceId.value) await refreshDeviceDetail()
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function syncDefaultIds() {
  const firstCategory = categories.value[0]?.id
  const firstProduct = products.value[0]?.id
  if (firstCategory) {
    if (!categories.value.some((item) => item.id === productForm.category_id)) productForm.category_id = firstCategory
    if (!categories.value.some((item) => item.id === categoryModelForm.category_id)) categoryModelForm.category_id = firstCategory
  }
  if (firstProduct) {
    if (!products.value.some((item) => item.id === deviceForm.product_id)) deviceForm.product_id = firstProduct
    if (!products.value.some((item) => item.id === productModelForm.product_id)) productModelForm.product_id = firstProduct
    if (!products.value.some((item) => item.id === ruleForm.product_id)) ruleForm.product_id = firstProduct
  }
}

async function loadEffectiveThingModels() {
  if (!productModelForm.product_id) {
    effectiveThingModels.value = []
    return
  }
  effectiveThingModels.value = await fetchJson(`/api/products/${productModelForm.product_id}/effective-thing-models`)
}

async function createRecord(path: string, payload: Record<string, unknown>, label: string) {
  saving.value = true
  notice.value = ''
  try {
    const created = await fetchJson(path, { method: 'POST', body: JSON.stringify(payload) })
    notice.value = `${label}已创建`
    await refresh()
    return created
  } catch (error: any) {
    notice.value = error.message || `${label}创建失败`
    return null
  } finally {
    saving.value = false
  }
}

function createCategory() {
  return createRecord('/api/categories', categoryForm, '品类')
}

async function createProduct() {
  const created = await createRecord('/api/products', productForm, '产品')
  if (created?.id) {
    deviceForm.product_id = created.id
    productModelForm.product_id = created.id
    ruleForm.product_id = created.id
    await loadEffectiveThingModels()
  }
}

async function publishProduct(productId: number) {
  saving.value = true
  notice.value = ''
  try {
    await fetchJson(`/api/products/${productId}/publish`, { method: 'POST' })
    notice.value = 'Product published'
    await refresh()
  } catch (error: any) {
    notice.value = error.message || 'Publish failed'
  } finally {
    saving.value = false
  }
}

function createDevice() {
  return createRecord('/api/devices', deviceForm, '设备')
}

async function openDeviceDetail(row: any) {
  selectedDeviceId.value = row.id
  selectedDeviceName.value = row.device_name
  deviceDetailTab.value = 'properties'
  selectedProperty.value = ''
  propertyHistory.value = []
  await refreshDeviceDetail()
}

async function loadDeviceHistory(deviceId: number, deviceName: string) {
  selectedDeviceId.value = deviceId
  selectedDeviceName.value = deviceName
  deviceHistory.value = await fetchJson(`/api/devices/${deviceId}/property-logs?limit=200`)
}

async function refreshDeviceDetail() {
  if (!selectedDeviceId.value) return
  const deviceId = selectedDeviceId.value
  const [detail, logs, history] = await Promise.all([
    fetchJson(`/api/devices/${deviceId}/detail`),
    fetchJson(`/api/devices/${deviceId}/message-logs?limit=100`),
    fetchJson(`/api/devices/${deviceId}/property-logs?limit=200`),
  ])
  deviceDetail.value = detail
  messageLogs.value = logs
  deviceHistory.value = history
  if (selectedProperty.value) {
    propertyHistory.value = await fetchJson(`/api/devices/${deviceId}/property-logs?identifier=${encodeURIComponent(selectedProperty.value)}&limit=200`)
  }
}

async function loadPropertyHistory(identifier: string) {
  if (!selectedDeviceId.value) return
  selectedProperty.value = identifier
  propertyHistory.value = await fetchJson(`/api/devices/${selectedDeviceId.value}/property-logs?identifier=${encodeURIComponent(identifier)}&limit=200`)
}

function createCategoryThingModel() {
  return createRecord('/api/category-thing-models', categoryModelForm, '品类物模型')
}

function createProductThingModel() {
  return createRecord('/api/thing-models', productModelForm, '产品物模型')
}

function createRule() {
  return createRecord('/api/rules', ruleForm, '规则')
}

async function askAgent() {
  const data = await fetchJson('/api/agent', {
    method: 'POST',
    body: JSON.stringify({ message: agentInput.value }),
  })
  agentAnswer.value = data.answer
}

function renderChart() {
  const el = document.getElementById('trend')
  if (!el) return
  chart = chart || echarts.init(el)
  chart.setOption({
    grid: { left: 42, right: 18, top: 24, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: latestTemperature.value.map((p: any) => new Date(p.reported_at).toLocaleTimeString()) },
    yAxis: { type: 'value', name: 'C' },
    series: [{
      name: 'temperature',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: latestTemperature.value.map((p: any) => Number(p.value)),
      areaStyle: { opacity: 0.12 },
    }],
  })
}

function productName(productId: number) {
  return products.value.find((item) => item.id === productId)?.name || `产品 ${productId}`
}

function categoryName(categoryId: number) {
  return categories.value.find((item) => item.id === categoryId)?.name || `品类 ${categoryId}`
}

onMounted(() => {
  refresh()
  refreshTimer = window.setInterval(refresh, 5000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<template>
  <main class="shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>IoT Agent Demo</strong>
        <span>v0.2 继承物模型</span>
      </div>
      <nav>
        <button v-for="item in navItems" :key="item.key" :class="{ active: activeView === item.key }" type="button" @click="activeView = item.key">
          {{ item.label }}
        </button>
      </nav>
    </aside>

    <section class="content">
      <header class="topbar">
        <div>
          <h1>物联网演示控制台</h1>
          <p>品类通用物模型 -> 产品继承并扩展 -> 设备实例拥有最终能力 -> MQTT 上报校验</p>
        </div>
        <el-button :loading="loading" type="primary" @click="refresh">刷新</el-button>
      </header>

      <el-alert v-if="notice" class="notice" :title="notice" type="info" show-icon :closable="false" />

      <template v-if="activeView === 'overview'">
        <section class="stats-grid">
          <div class="metric"><span>品类</span><strong>{{ dashboard.stats.categories || 0 }}</strong></div>
          <div class="metric"><span>产品</span><strong>{{ dashboard.stats.products || 0 }}</strong></div>
          <div class="metric"><span>设备</span><strong>{{ dashboard.stats.devices || 0 }}</strong></div>
          <div class="metric"><span>品类物模型</span><strong>{{ dashboard.stats.category_thing_models || 0 }}</strong></div>
          <div class="metric"><span>产品物模型</span><strong>{{ dashboard.stats.product_thing_models || 0 }}</strong></div>
          <div class="metric warn"><span>告警</span><strong>{{ dashboard.stats.alarms || 0 }}</strong></div>
        </section>
        <section class="main-grid">
          <section class="panel wide">
            <div class="panel-head"><h2>温度趋势</h2><span>来自 MQTT 模拟设备</span></div>
            <div id="trend" class="chart"></div>
          </section>
          <section class="panel">
            <div class="panel-head"><h2>最新告警</h2><span>规则引擎输出</span></div>
            <el-table :data="dashboard.alarms" size="small" height="280">
              <el-table-column prop="device_name" label="设备" width="132" />
              <el-table-column prop="content" label="内容" min-width="220" />
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'categories'">
        <section class="workspace-grid">
          <section class="panel">
            <div class="panel-head"><h2>创建品类</h2><span>设备大类</span></div>
            <el-form label-position="top">
              <el-form-item label="品类名称"><el-input v-model="categoryForm.name" /></el-form-item>
              <el-form-item label="行业"><el-input v-model="categoryForm.industry" /></el-form-item>
              <el-form-item label="场景"><el-input v-model="categoryForm.scene" /></el-form-item>
              <el-button :loading="saving" type="primary" @click="createCategory">创建品类</el-button>
            </el-form>
          </section>
          <section class="panel table-panel">
            <div class="panel-head"><h2>品类列表</h2><span>{{ categories.length }} 条</span></div>
            <el-table :data="categories" size="small" height="420">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="industry" label="行业" />
              <el-table-column prop="scene" label="场景" />
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'products'">
        <section class="workspace-grid">
          <section class="panel">
            <div class="panel-head"><h2>创建产品</h2><span>品类的具体型号</span></div>
            <el-form label-position="top">
              <el-form-item label="继承品类">
                <el-select v-model="productForm.category_id">
                  <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="ProductKey"><el-input v-model="productForm.product_key" /></el-form-item>
              <el-form-item label="产品名称"><el-input v-model="productForm.name" /></el-form-item>
              <el-form-item label="接入协议"><el-input v-model="productForm.protocol" /></el-form-item>
              <el-button :loading="saving" type="primary" @click="createProduct">创建产品</el-button>
            </el-form>
          </section>
          <section class="panel table-panel">
            <div class="panel-head"><h2>产品列表</h2><span>产品继承品类物模型</span></div>
            <el-table :data="products" size="small" height="420">
              <el-table-column prop="product_key" label="ProductKey" min-width="150" />
              <el-table-column prop="name" label="名称" />
              <el-table-column label="继承品类" min-width="130">
                <template #default="{ row }">{{ categoryName(row.category_id) }}</template>
              </el-table-column>
              <el-table-column prop="protocol" label="协议" width="90" />
              <el-table-column prop="status" label="状态" width="100" />
              <el-table-column label="发布" width="120">
                <template #default="{ row }">
                  <el-button v-if="!row.published" size="small" type="primary" @click="publishProduct(row.id)">发布</el-button>
                  <el-tag v-else type="success">已上线</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'devices'">
        <section class="workspace-grid">
          <section class="panel">
            <div class="panel-head"><h2>创建设备</h2><span>产品的实例</span></div>
            <el-form label-position="top">
              <el-form-item label="所属产品">
                <el-select v-model="deviceForm.product_id">
                  <el-option v-for="item in products" :key="item.id" :label="`${item.name} / ${item.product_key}`" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="DeviceName"><el-input v-model="deviceForm.device_name" /></el-form-item>
              <el-form-item label="DeviceSecret"><el-input v-model="deviceForm.device_secret" /></el-form-item>
              <el-form-item label="唯一编号"><el-input v-model="deviceForm.unique_no" /></el-form-item>
              <el-button :loading="saving" type="primary" @click="createDevice">创建设备</el-button>
            </el-form>
          </section>
          <section class="panel table-panel">
            <div class="panel-head"><h2>设备列表</h2><span>设备拥有产品最终物模型</span></div>
            <el-table :data="devices" size="small" height="420">
              <el-table-column prop="device_name" label="DeviceName" min-width="150" />
              <el-table-column label="产品" min-width="140">
                <template #default="{ row }">{{ productName(row.product_id) }}</template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="92">
                <template #default="{ row }"><el-tag :type="row.status === 'online' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="last_report_at" label="最后上报" min-width="170" />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button size="small" type="primary" @click="openDeviceDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>
          <section class="panel device-detail" v-if="deviceDetail">
            <div class="panel-head"><h2>设备详情</h2><span>{{ deviceDetail.device.device_name }}</span></div>
            <div class="detail-summary">
              <div><span>ProductName</span><strong>{{ deviceDetail.product.name }}</strong></div>
              <div><span>ProductKey</span><strong>{{ deviceDetail.product.product_key }}</strong></div>
              <div><span>DeviceName</span><strong>{{ deviceDetail.device.device_name }}</strong></div>
              <div><span>DeviceSecret</span><strong>{{ deviceDetail.device.device_secret }}</strong></div>
              <div><span>状态</span><strong>{{ deviceDetail.device.status }}</strong></div>
              <div><span>最后上报</span><strong>{{ deviceDetail.device.last_report_at || '-' }}</strong></div>
            </div>
            <el-tabs v-model="deviceDetailTab">
              <el-tab-pane label="设备信息" name="info">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="唯一编号">{{ deviceDetail.device.unique_no }}</el-descriptions-item>
                  <el-descriptions-item label="所属产品">{{ deviceDetail.product.name }}</el-descriptions-item>
                  <el-descriptions-item label="所属品类">{{ deviceDetail.category?.name || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="接入协议">{{ deviceDetail.product.protocol }}</el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>
              <el-tab-pane label="物模型数据" name="properties">
                <div class="property-grid">
                  <div v-for="model in deviceDetail.thing_models.filter((item: any) => item.model_type === 'property')" :key="model.identifier" class="property-card">
                    <div class="property-title"><strong>{{ model.name }}</strong><el-tag size="small">{{ model.data_type }}</el-tag></div>
                    <div class="property-meta">标识符：{{ model.identifier }}</div>
                    <div class="property-meta">来源：{{ model.source === 'category' ? '品类继承' : '产品扩展' }}</div>
                    <div class="property-value">最新值：{{ deviceDetail.device.latest_properties?.[model.identifier] ?? '-' }} {{ model.unit }}</div>
                    <el-button size="small" @click="loadPropertyHistory(model.identifier)">历史数据</el-button>
                  </div>
                </div>
                <section class="history-section">
                  <div class="panel-head"><h2>属性历史数据</h2><span>{{ selectedProperty || '请选择属性' }}</span></div>
                  <el-table :data="propertyHistory" size="small" height="260">
                    <el-table-column prop="reported_at" label="上报时间" min-width="190" />
                    <el-table-column prop="identifier" label="属性" min-width="140" />
                    <el-table-column prop="value" label="值" min-width="100" />
                  </el-table>
                </section>
              </el-tab-pane>
              <el-tab-pane label="设备日志" name="logs">
                <el-table :data="messageLogs" size="small" height="360">
                  <el-table-column prop="reported_at" label="更新时间" min-width="190" />
                  <el-table-column prop="topic" label="Topic" min-width="260" />
                  <el-table-column label="消息内容" min-width="360">
                    <template #default="{ row }"><code class="payload-code">{{ JSON.stringify(row.payload) }}</code></template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="MQTT 协议" name="mqtt">
                <el-alert title="Demo 参数用于本地调试；BladeX 生产环境需要按设备三元组生成 HMAC 密码。" type="warning" :closable="false" />
                <pre class="mqtt-code">{{ JSON.stringify(deviceDetail.mqtt, null, 2) }}</pre>
              </el-tab-pane>
            </el-tabs>
          </section>
          <section class="panel" v-else>
            <div class="empty-detail"><h2>设备详情</h2><p>请选择设备列表中的“详情”，查看物模型数据、属性历史、设备日志和 MQTT 参数。</p></div>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'models'">
        <section class="model-grid">
          <section class="panel">
            <div class="panel-head"><h2>品类通用物模型</h2><span>发布后被产品继承</span></div>
            <el-form label-position="top">
              <el-form-item label="所属品类">
                <el-select v-model="categoryModelForm.category_id">
                  <el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <div class="two-cols">
                <el-form-item label="标识符"><el-input v-model="categoryModelForm.identifier" /></el-form-item>
                <el-form-item label="名称"><el-input v-model="categoryModelForm.name" /></el-form-item>
              </div>
              <div class="three-cols">
                <el-form-item label="类型"><el-input v-model="categoryModelForm.model_type" /></el-form-item>
                <el-form-item label="数据类型"><el-input v-model="categoryModelForm.data_type" /></el-form-item>
                <el-form-item label="单位"><el-input v-model="categoryModelForm.unit" /></el-form-item>
              </div>
              <el-button :loading="saving" type="primary" @click="createCategoryThingModel">保存品类物模型</el-button>
            </el-form>
          </section>

          <section class="panel">
            <div class="panel-head"><h2>产品扩展物模型</h2><span>产品特有能力或覆盖项</span></div>
            <el-form label-position="top">
              <el-form-item label="所属产品">
                <el-select v-model="productModelForm.product_id" @change="loadEffectiveThingModels">
                  <el-option v-for="item in products" :key="item.id" :label="`${item.name} / ${item.product_key}`" :value="item.id" />
                </el-select>
              </el-form-item>
              <div class="two-cols">
                <el-form-item label="标识符"><el-input v-model="productModelForm.identifier" /></el-form-item>
                <el-form-item label="名称"><el-input v-model="productModelForm.name" /></el-form-item>
              </div>
              <div class="three-cols">
                <el-form-item label="类型"><el-input v-model="productModelForm.model_type" /></el-form-item>
                <el-form-item label="数据类型"><el-input v-model="productModelForm.data_type" /></el-form-item>
                <el-form-item label="单位"><el-input v-model="productModelForm.unit" /></el-form-item>
              </div>
              <el-button :loading="saving" type="primary" @click="createProductThingModel">保存产品物模型</el-button>
            </el-form>
          </section>

          <section class="panel table-panel">
            <div class="panel-head"><h2>产品最终物模型</h2><span>品类继承 + 产品扩展</span></div>
            <el-table :data="effectiveThingModels" size="small" height="280">
              <el-table-column prop="identifier" label="标识符" min-width="130" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="source" label="来源" width="90">
                <template #default="{ row }"><el-tag :type="row.source === 'category' ? 'success' : 'warning'">{{ row.source === 'category' ? '品类继承' : '产品扩展' }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="model_type" label="类型" width="90" />
              <el-table-column prop="data_type" label="数据类型" width="100" />
              <el-table-column prop="unit" label="单位" width="70" />
            </el-table>
          </section>

          <section class="panel table-panel">
            <div class="panel-head"><h2>物模型原始定义</h2><span>左：品类，右：产品</span></div>
            <el-table :data="[...categoryThingModels, ...thingModels]" size="small" height="280">
              <el-table-column prop="identifier" label="标识符" min-width="130" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="source" label="层级" width="90" />
              <el-table-column prop="model_type" label="类型" width="90" />
              <el-table-column prop="data_type" label="数据类型" width="100" />
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'rules'">
        <section class="workspace-grid">
          <section class="panel">
            <div class="panel-head"><h2>创建规则</h2><span>基于最终物模型属性</span></div>
            <el-form label-position="top">
              <el-form-item label="所属产品">
                <el-select v-model="ruleForm.product_id">
                  <el-option v-for="item in products" :key="item.id" :label="`${item.name} / ${item.product_key}`" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="规则名称"><el-input v-model="ruleForm.name" /></el-form-item>
              <div class="three-cols">
                <el-form-item label="属性"><el-input v-model="ruleForm.identifier" /></el-form-item>
                <el-form-item label="条件"><el-input v-model="ruleForm.operator" /></el-form-item>
                <el-form-item label="阈值"><el-input-number v-model="ruleForm.threshold" :min="0" :max="9999" /></el-form-item>
              </div>
              <el-form-item label="告警内容"><el-input v-model="ruleForm.message" /></el-form-item>
              <el-form-item><el-switch v-model="ruleForm.enabled" active-text="启用" inactive-text="停用" /></el-form-item>
              <el-button :loading="saving" type="primary" @click="createRule">创建规则</el-button>
            </el-form>
          </section>
          <section class="panel table-panel">
            <div class="panel-head"><h2>规则列表</h2><span>{{ rules.length }} 条</span></div>
            <el-table :data="rules" size="small" height="420">
              <el-table-column prop="name" label="名称" min-width="150" />
              <el-table-column prop="identifier" label="属性" width="110" />
              <el-table-column prop="operator" label="条件" width="70" />
              <el-table-column prop="threshold" label="阈值" width="82" />
              <el-table-column prop="enabled" label="启用" width="80" />
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'logs'">
        <section class="main-grid lower">
          <section class="panel">
            <div class="panel-head"><h2>设备</h2><span>在线状态</span></div>
            <el-table :data="dashboard.devices" size="small" height="420">
              <el-table-column prop="device_name" label="设备名" min-width="150" />
              <el-table-column prop="status" label="状态" width="92" />
              <el-table-column prop="last_report_at" label="最后上报" min-width="190" />
            </el-table>
          </section>
          <section class="panel">
            <div class="panel-head"><h2>最近上报</h2><span>属性日志</span></div>
            <el-table :data="dashboard.latest_logs" size="small" height="420">
              <el-table-column prop="identifier" label="属性" width="110" />
              <el-table-column prop="value" label="值" width="90" />
              <el-table-column prop="device_name" label="设备" min-width="150" />
            </el-table>
          </section>
          <section class="panel">
            <div class="panel-head"><h2>告警</h2><span>规则触发</span></div>
            <el-table :data="dashboard.alarms" size="small" height="420">
              <el-table-column prop="device_name" label="设备" width="132" />
              <el-table-column prop="content" label="内容" min-width="240" />
            </el-table>
          </section>
        </section>
      </template>

      <template v-if="activeView === 'agent'">
        <section class="agent-layout">
          <section class="panel">
            <div class="panel-head"><h2>AI 诊断助手</h2><span>规则解释入口</span></div>
            <el-input v-model="agentInput" type="textarea" :rows="4" />
            <el-button class="ask" type="primary" @click="askAgent">询问</el-button>
            <pre class="answer">{{ agentAnswer || '可以问：为什么 demo-device-001 告警？物模型有哪些属性？MQTT 报文怎么发？设备为什么离线？' }}</pre>
          </section>
          <section class="panel">
            <div class="panel-head"><h2>继承链路</h2><span>对照 BladeX 主干</span></div>
            <div class="flow-list">
              <span>品类定义通用物模型</span><span>产品继承</span><span>产品扩展</span><span>设备实例化</span><span>上报按最终物模型校验</span><span>规则按属性触发</span><span>AI 解释</span>
            </div>
          </section>
        </section>
      </template>
    </section>
  </main>
</template>
