<script setup lang="ts">
import { onMounted, ref } from "vue";

import { createStrategy, getStrategySource, listStrategies, saveStrategy } from "@/api/strategies";
import type { StrategyInfo } from "@/types/api";

const strategies = ref<StrategyInfo[]>([]);
const selected = ref<StrategyInfo>();
const source = ref("");
const newName = ref("");
const message = ref("");

async function refresh(selectName?: string) {
  strategies.value = await listStrategies();
  const target = strategies.value.find((item) => item.name === selectName) || selected.value || strategies.value[0];
  if (target) await select(target);
}
async function select(item: StrategyInfo) {
  selected.value = item;
  source.value = (await getStrategySource(item.name)).source;
  message.value = "";
}
async function create() {
  if (!newName.value) return;
  try { await createStrategy(newName.value); const name = newName.value; newName.value = ""; await refresh(name); }
  catch (error) { message.value = error instanceof Error ? error.message : "创建失败"; }
}
async function save() {
  if (!selected.value?.editable) return;
  try {
    const result = await saveStrategy(selected.value.name, source.value);
    message.value = result.valid ? "策略已保存并通过语法校验" : result.errors.join("；");
    await refresh(selected.value.name);
  } catch (error) { message.value = error instanceof Error ? error.message : "保存失败"; }
}
onMounted(() => void refresh());
</script>

<template>
  <section class="strategy-layout">
    <aside class="panel strategy-list">
      <div class="panel-heading"><div><p class="eyebrow">LIBRARY</p><h2>策略</h2></div><span class="count">{{ strategies.length }}</span></div>
      <button v-for="item in strategies" :key="item.name" class="strategy-item" :class="{ active: selected?.name === item.name }" @click="select(item)">
        <span><strong>{{ item.name }}</strong><small>{{ item.description || item.class_name }}</small></span><i :class="{ valid: item.valid }"></i>
      </button>
      <form class="create-strategy" @submit.prevent="create"><input v-model="newName" placeholder="new_strategy" pattern="[A-Za-z][A-Za-z0-9_]{1,63}" /><button aria-label="创建策略">+</button></form>
    </aside>
    <article class="panel editor-panel">
      <div class="panel-heading"><div><p class="eyebrow">PYTHON STRATEGY</p><h2>{{ selected?.name || "选择策略" }}</h2></div><button class="primary-button" :disabled="!selected?.editable" @click="save">保存并校验</button></div>
      <div v-if="selected" class="editor-meta"><span>{{ selected.class_name }}</span><span>{{ selected.editable ? "用户策略" : "内置示例 · 只读" }}</span><span :class="selected.valid ? 'ok' : 'bad'">{{ selected.valid ? "VALID" : "INVALID" }}</span></div>
      <textarea v-model="source" class="code-editor" spellcheck="false" :readonly="!selected?.editable" aria-label="Python 策略源码"></textarea>
      <div v-if="message" class="notice" :class="{ error: selected && !selected.valid }">{{ message }}</div>
    </article>
  </section>
</template>
