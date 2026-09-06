import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { listBacktests } from "@/api/backtests";
import { listDownloadTasks } from "@/api/datasets";
import type { TaskRecord } from "@/types/api";

export const useTaskStore = defineStore("tasks", () => {
  const tasks = ref<TaskRecord[]>([]);
  const active = computed(() => tasks.value.filter((task) => ["PENDING", "RUNNING"].includes(task.status)));
  async function refresh() {
    const [downloads, backtests] = await Promise.all([listDownloadTasks(), listBacktests()]);
    tasks.value = [...downloads, ...backtests].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  }
  return { tasks, active, refresh };
});
