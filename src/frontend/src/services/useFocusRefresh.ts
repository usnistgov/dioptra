import { onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore";
import { getLoginStatus } from "@/services/dataApi";

export function useFocusRefresh() {
  const store = useLoginStore();
  const router = useRouter();
  let inFlight = false;
  let lastRefresh = -Infinity;

  async function refresh() {
    if (!store.loggedInUser || store.groupContextResolving || inFlight || Date.now() - lastRefresh < 2000) return;
    const generation = store.sessionGeneration;
    inFlight = true;
    lastRefresh = Date.now();
    try {
      const response = await getLoginStatus();
      if (generation !== store.sessionGeneration || !store.loggedInUser || store.groupContextResolving) return;

      const previousGroup = store.loggedInGroup;
      const wasLocked = store.groupContextLocked;
      const previousUserId = store.loggedInUser.id;
      store.setSession(response.data);
      const group = store.loggedInGroup;
      const route = router.currentRoute.value;

      if (
        previousUserId !== response.data.id ||
        (wasLocked && previousGroup && !store.groups.some((g) => g.id === previousGroup.id))
      ) {
        await router.replace("/groups");
      } else if (!wasLocked && group && route.query.groupId !== undefined && route.query.groupId !== String(group.id)) {
        await router.replace({
          path: route.path,
          query: { ...route.query, groupId: String(group.id) },
          hash: route.hash,
        });
      }
    } catch (error) {
      if (generation !== store.sessionGeneration) return;
      const status = (error as { response?: { status?: number } }).response?.status;
      if (status === 401) {
        store.clearSession();
        await router.replace("/login");
      }
    } finally {
      inFlight = false;
    }
  }

  onMounted(() => window.addEventListener("focus", refresh));
  onBeforeUnmount(() => window.removeEventListener("focus", refresh));
}
