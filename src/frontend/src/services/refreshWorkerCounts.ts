import type { Ref } from "vue";
import { getQueueWorkers } from "@/services/dataApi";

export async function refreshWorkerCounts(
  names: (string | undefined)[],
  workerCounts: Ref<Map<string, number>>,
  workersLoading: Ref<boolean>,
  onCleanup: (cleanup: () => void) => void,
) {
  let active = true;
  onCleanup(() => {
    active = false;
  });
  workerCounts.value = new Map();
  const queueNames = [...new Set(names.filter((name): name is string => !!name))];
  workersLoading.value = queueNames.length > 0;
  if (!queueNames.length) return;

  try {
    const res = await getQueueWorkers(queueNames);
    if (active) workerCounts.value = new Map(Object.entries(res.data.workers));
  } catch (err) {
    console.error("Unable to fetch queue worker counts", err);
  } finally {
    if (active) workersLoading.value = false;
  }
}
