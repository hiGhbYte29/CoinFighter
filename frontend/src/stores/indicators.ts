import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { getIndicatorCatalog } from "@/api/indicators";
import {
  apiSelection,
  createIndicator,
  hydrateIndicator,
  normalizeStyles,
  type ConfiguredIndicator,
} from "@/indicators/config";
import type { IndicatorCatalog } from "@/types/api";

const STORAGE_KEY = "cf-chart-indicators:v1";

function loadSaved(): ConfiguredIndicator[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]") as ConfiguredIndicator[];
    return Array.isArray(parsed) ? parsed.map(normalizeStyles) : [];
  } catch {
    return [];
  }
}

export const useIndicatorStore = defineStore("indicators", () => {
  const catalog = ref<IndicatorCatalog | null>(null);
  const selections = ref<ConfiguredIndicator[]>(loadSaved());
  const loading = ref(false);
  const error = ref("");
  const enabledSelections = computed(() => selections.value.filter((item) => item.enabled));
  const enabledCount = computed(() => enabledSelections.value.length);
  const apiSelections = computed(() => enabledSelections.value.map(apiSelection));

  async function loadCatalog() {
    if (catalog.value) return;
    loading.value = true;
    error.value = "";
    try {
      catalog.value = await getIndicatorCatalog();
      const saved = new Map(selections.value.map((item) => [item.indicator_id, item]));
      selections.value = catalog.value.items
        .filter((item) => item.available)
        .map((definition) => hydrateIndicator(
          definition,
          saved.get(definition.id) || (definition.id === "vol" ? createIndicator(definition, true) : undefined),
        ));
      persist();
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : "技术指标目录加载失败";
    } finally {
      loading.value = false;
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(selections.value));
  }

  function save(configs: ConfiguredIndicator[]) {
    selections.value = configs.map(normalizeStyles);
    persist();
  }

  return {
    catalog,
    selections,
    enabledSelections,
    enabledCount,
    apiSelections,
    loading,
    error,
    loadCatalog,
    save,
  };
});
