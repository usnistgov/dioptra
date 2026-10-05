import { ref, watch } from "vue";
import { getQueueWorkers } from "@/services/dataApi";

export function useQueueWorkers(getQueueNames: () => (string | undefined)[]) {
  const workerCounts = ref(new Map<string, number>());
  const workersLoading = ref(false);

  watch(
    getQueueNames,
    async (names, _previousNames, onCleanup) => {
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
    },
    { immediate: true },
  );

  return { workerCounts, workersLoading };
}
