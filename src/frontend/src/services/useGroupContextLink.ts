import { useRouter, type RouteLocationRaw } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore";

export function useGroupContextLink() {
  const router = useRouter();
  const store = useLoginStore();

  function withGroupContext(to: RouteLocationRaw | undefined): RouteLocationRaw | undefined {
    if (to === undefined) return to;

    const destination = router.resolve(to);
    const context = destination.meta.groupContext as { kind: string; idParam?: string } | undefined;
    const usesSelectedGroup =
      context?.kind === "selected" ||
      (context?.kind === "resource" && context.idParam && destination.params[context.idParam] === "new");
    const group = store.loggedInGroup;

    if (!usesSelectedGroup || !group) return to;

    // Include context in the href itself so native new-tab navigation preserves it.
    return {
      path: destination.path,
      query: { ...destination.query, groupId: destination.query.groupId ?? String(group.id) },
      hash: destination.hash,
    };
  }

  return { withGroupContext };
}
