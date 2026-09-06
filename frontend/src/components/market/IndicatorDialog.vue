<script setup lang="ts">
import { computed, ref, watch } from "vue";

import {
  createIndicator,
  hydrateIndicator,
  normalizeStyles,
  periodLineKey,
  plotKeys,
  type ConfiguredIndicator,
  type IndicatorPlotStyle,
} from "@/indicators/config";
import type { IndicatorCatalog, IndicatorDefinition, IndicatorParameter, IndicatorPlacement } from "@/types/api";

const props = defineProps<{
  open: boolean;
  catalog: IndicatorCatalog | null;
  configs: ConfiguredIndicator[];
}>();
const emit = defineEmits<{
  close: [];
  save: [configs: ConfiguredIndicator[]];
}>();

const tab = ref<IndicatorPlacement>("main");
const draft = ref<ConfiguredIndicator[]>([]);
const selectedId = ref("");

const definitions = computed(() => props.catalog?.items.filter((item) => item.placement === tab.value) || []);
const selectedDefinition = computed(() => props.catalog?.items.find((item) => item.id === selectedId.value) || definitions.value[0]);
const selectedConfig = computed(() => draft.value.find((item) => item.indicator_id === selectedDefinition.value?.id));
const periodParameter = computed(() => selectedDefinition.value?.parameters.find((item) => item.type === "integer_list"));
const regularParameters = computed(() => selectedDefinition.value?.parameters.filter((item) => (
  item.type !== "integer_list" && !(periodParameter.value && item.key === "source")
)) || []);
const extraPlotKeys = computed(() => {
  const config = selectedConfig.value;
  if (!config) return [];
  const periodKeys = new Set(config.periodLines?.map((_, index) => periodLineKey(config, index)) || []);
  return plotKeys(config, true).filter((key) => !periodKeys.has(key));
});
const sourceParameter = computed(() => selectedDefinition.value?.parameters.find((item) => item.key === "source"));

function initializeDraft() {
  if (!props.catalog) return;
  const saved = new Map(props.configs.map((item) => [item.indicator_id, item]));
  draft.value = props.catalog.items
    .filter((item) => item.available)
    .map((definition) => hydrateIndicator(definition, saved.get(definition.id)));
  const firstEnabled = draft.value.find((item) => item.placement === tab.value && item.enabled);
  selectedId.value = firstEnabled?.indicator_id || definitions.value[0]?.id || "";
}

watch([() => props.open, () => props.catalog], ([open]) => {
  if (open) initializeDraft();
}, { immediate: true });

watch(tab, () => {
  const firstEnabled = draft.value.find((item) => item.placement === tab.value && item.enabled);
  selectedId.value = firstEnabled?.indicator_id || definitions.value[0]?.id || "";
});

function isEnabled(definition: IndicatorDefinition) {
  return draft.value.find((item) => item.indicator_id === definition.id)?.enabled || false;
}

function select(definition: IndicatorDefinition) {
  if (definition.available) selectedId.value = definition.id;
}

function toggle(definition: IndicatorDefinition) {
  if (!definition.available) return;
  selectedId.value = definition.id;
  let config = draft.value.find((item) => item.indicator_id === definition.id);
  if (!config) {
    config = createIndicator(definition);
    draft.value.push(config);
  }
  config.enabled = !config.enabled;
  if (config.enabled && config.periodLines && !config.periodLines.some((line) => line.enabled)) {
    config.periodLines[0].enabled = true;
  }
}

function updateParameter(parameter: IndicatorParameter, event: Event) {
  const config = selectedConfig.value;
  const target = event.target as HTMLInputElement | HTMLSelectElement;
  if (!config) return;
  if (parameter.type === "integer") {
    config.parameters[parameter.key] = Number.parseInt(target.value, 10);
  } else if (parameter.type === "number") {
    config.parameters[parameter.key] = Number(target.value);
  } else {
    config.parameters[parameter.key] = target.value;
  }
  Object.assign(config, normalizeStyles(config));
}

function parameterValue(parameter: IndicatorParameter): string | number {
  const value = selectedConfig.value?.parameters[parameter.key] ?? parameter.default;
  return String(value);
}

function lineLabel(index: number) {
  const id = selectedDefinition.value?.id.toUpperCase() || "";
  return `${id === "VOL" ? "MAVOL" : id}${index + 1}`;
}

function defaultPeriod(indicatorId: string, index: number) {
  const definition = props.catalog?.items.find((item) => item.id === indicatorId);
  const defaults = definition?.parameters.find((item) => item.type === "integer_list")?.default;
  return Array.isArray(defaults) ? Number(defaults[index] || defaults[0] || 1) : 1;
}

function togglePeriodLine(index: number) {
  const config = selectedConfig.value;
  const line = config?.periodLines?.[index];
  if (!config || !line) return;
  if (config.enabled && line.enabled && config.periodLines?.filter((item) => item.enabled).length === 1) {
    return;
  }
  line.enabled = !line.enabled;
  if (line.enabled && line.value <= 0) line.value = defaultPeriod(config.indicator_id, index);
}

function updatePeriodValue(index: number, event: Event) {
  const line = selectedConfig.value?.periodLines?.[index];
  if (!line) return;
  line.value = Number.parseInt((event.target as HTMLInputElement).value, 10) || 0;
}

function updatePeriodSource(index: number, event: Event) {
  const line = selectedConfig.value?.periodLines?.[index];
  if (line) line.source = (event.target as HTMLSelectElement).value;
}

function styleFor(key: string): IndicatorPlotStyle {
  return selectedConfig.value?.styles[key] || { color: "#ffd43b", lineStyle: "solid" };
}

function updateStyle(key: string, field: keyof IndicatorPlotStyle, event: Event) {
  const config = selectedConfig.value;
  if (!config) return;
  const value = (event.target as HTMLInputElement | HTMLSelectElement).value;
  config.styles[key] = { ...styleFor(key), [field]: value } as IndicatorPlotStyle;
}

function resetSelected() {
  const definition = selectedDefinition.value;
  const config = selectedConfig.value;
  if (!definition || !config) return;
  const index = draft.value.indexOf(config);
  draft.value[index] = createIndicator(definition, config.enabled);
}

function save() {
  draft.value.forEach((config) => {
    if (!config.enabled || !config.periodLines) return;
    if (!config.periodLines.some((line) => line.enabled)) config.periodLines[0].enabled = true;
    config.periodLines.forEach((line, index) => {
      if (line.enabled && line.value <= 0) line.value = defaultPeriod(config.indicator_id, index);
    });
  });
  emit("save", draft.value.map(normalizeStyles));
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="indicator-overlay" role="presentation" @mousedown.self="emit('close')">
      <section class="indicator-dialog" role="dialog" aria-modal="true" aria-label="技术指标设置">
        <header class="indicator-dialog-header">
          <nav class="indicator-tabs" aria-label="指标位置">
            <button :class="{ active: tab === 'main' }" @click="tab = 'main'">主图</button>
            <button :class="{ active: tab === 'sub' }" @click="tab = 'sub'">副图</button>
          </nav>
          <button class="indicator-close" aria-label="关闭" @click="emit('close')">×</button>
        </header>

        <div class="indicator-dialog-body">
          <aside class="indicator-list">
            <div
              v-for="definition in definitions"
              :key="definition.id"
              class="indicator-list-row"
              :class="{ selected: selectedDefinition?.id === definition.id, unavailable: !definition.available }"
            >
              <input
                type="checkbox"
                :checked="isEnabled(definition)"
                :disabled="!definition.available"
                :aria-label="`启用 ${definition.name}`"
                @change="toggle(definition)"
              >
              <button :disabled="!definition.available" @click="select(definition)">
                <span>{{ definition.id.toUpperCase() }}</span><i>›</i>
              </button>
            </div>
          </aside>

          <div v-if="selectedDefinition" class="indicator-settings">
            <div class="indicator-settings-title">
              <div><h3>{{ selectedDefinition.name }}</h3><p>{{ selectedDefinition.description }}</p></div>
              <span v-if="!selectedDefinition.available" class="indicator-unavailable">暂不可用</span>
            </div>
            <p v-if="!selectedDefinition.available" class="indicator-help">{{ selectedDefinition.unavailable_reason }}</p>
            <template v-else-if="selectedConfig">
              <div v-if="selectedConfig.periodLines" class="indicator-line-list">
                <div
                  v-for="(line, index) in selectedConfig.periodLines"
                  :key="index"
                  class="indicator-line-row"
                  :class="{ muted: !line.enabled }"
                >
                  <input
                    type="checkbox"
                    :checked="line.enabled"
                    :aria-label="`显示 ${lineLabel(index)}`"
                    @change="togglePeriodLine(index)"
                  >
                  <span>{{ lineLabel(index) }}</span>
                  <input
                    type="number"
                    :min="periodParameter?.minimum ?? 1"
                    :max="periodParameter?.maximum ?? 500"
                    :value="line.value"
                    :aria-label="`${lineLabel(index)} 周期`"
                    @input="updatePeriodValue(index, $event)"
                  >
                  <select
                    v-if="sourceParameter"
                    :value="line.source || sourceParameter.default"
                    :aria-label="`${lineLabel(index)} 价格源`"
                    @change="updatePeriodSource(index, $event)"
                  >
                    <option v-for="option in sourceParameter.options" :key="option.value" :value="option.value">{{ option.label }}</option>
                  </select>
                  <span v-else class="indicator-line-placeholder">—</span>
                  <select
                    :value="styleFor(periodLineKey(selectedConfig, index)).lineStyle"
                    :aria-label="`${lineLabel(index)} 线型`"
                    @change="updateStyle(periodLineKey(selectedConfig, index), 'lineStyle', $event)"
                  >
                    <option value="solid">实线</option>
                    <option value="dashed">虚线</option>
                    <option value="dotted">点线</option>
                  </select>
                  <input
                    type="color"
                    :value="styleFor(periodLineKey(selectedConfig, index)).color"
                    :aria-label="`${lineLabel(index)} 颜色`"
                    @input="updateStyle(periodLineKey(selectedConfig, index), 'color', $event)"
                  >
                </div>
              </div>

              <div v-if="regularParameters.length" class="indicator-form">
                <label v-for="parameter in regularParameters" :key="parameter.key">
                  <span>{{ parameter.label }}</span>
                  <select
                    v-if="parameter.type === 'select'"
                    :value="parameterValue(parameter)"
                    @change="updateParameter(parameter, $event)"
                  >
                    <option v-for="option in parameter.options" :key="option.value" :value="option.value">{{ option.label }}</option>
                  </select>
                  <input
                    v-else
                    type="number"
                    :min="parameter.minimum ?? undefined"
                    :max="parameter.maximum ?? undefined"
                    :step="parameter.type === 'number' ? 'any' : 1"
                    :value="parameterValue(parameter)"
                    @input="updateParameter(parameter, $event)"
                  >
                </label>
              </div>

              <div v-if="extraPlotKeys.length" class="indicator-style-list">
                <div v-for="key in extraPlotKeys" :key="key" class="indicator-style-row">
                  <span>{{ key.toUpperCase() }}</span>
                  <select
                    :value="styleFor(key).lineStyle"
                    :disabled="key === 'volume' || key === 'histogram'"
                    @change="updateStyle(key, 'lineStyle', $event)"
                  >
                    <option value="solid">实线</option>
                    <option value="dashed">虚线</option>
                    <option value="dotted">点线</option>
                  </select>
                  <input
                    type="color"
                    :value="styleFor(key).color"
                    :aria-label="`${key} 颜色`"
                    @input="updateStyle(key, 'color', $event)"
                  >
                </div>
              </div>
            </template>
          </div>
        </div>

        <footer class="indicator-dialog-footer">
          <button class="secondary-button" :disabled="!selectedDefinition?.available" @click="resetSelected">恢复默认</button>
          <button class="primary-button" @click="save">保存</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
