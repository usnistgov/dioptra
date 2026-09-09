import { createRouter, createWebHistory, START_LOCATION } from "vue-router";
import type { RouteLocationNormalizedGeneric } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore";
import HomeView from "../views/HomeView.vue";
import * as api from "@/services/dataApi";
import type { ResourceType } from "@/services/dataApi";
import * as notify from "@/notify";

type ResourceGroupContext = {
  kind: "resource";
  resource: ResourceType;
  idParam: string;
  fallback: string;
};

type QueueDraftGroupContext = {
  kind: "queueDraft";
  fallback: string;
};

type GroupSelfContext = {
  kind: "group";
  idParam: string;
  fallback: string;
};

type SelectedGroupContext = {
  kind: "selected";
};

type GroupContext = ResourceGroupContext | QueueDraftGroupContext | GroupSelfContext | SelectedGroupContext;

let isHistoryTraversal = false;
window.addEventListener("popstate", () => {
  isHistoryTraversal = true;
});

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    // always scroll to top
    return { top: 0 };
  },
  routes: [
    {
      path: "/",
      component: HomeView,
      name: "home",
    },
    {
      path: "/experiments",
      meta: { type: "experiments", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/ExperimentsView.vue"),
          name: "experiments",
        },
        {
          path: "/experiments/new",
          component: () => import("../views/CreateExperiment.vue"),
        },
        {
          path: "/experiments/:id",
          component: () => import("../views/EditExperiment.vue"),
          name: "experimentJobs",
          meta: {
            groupContext: { kind: "resource", resource: "experiments", idParam: "id", fallback: "/experiments" },
          },
        },
        {
          path: "/experiments/:id/jobs/:jobId",
          component: () => import("../views/CreateJob.vue"),
          name: "createExperimentJob",
          meta: {
            groupContext: { kind: "resource", resource: "experiments", idParam: "id", fallback: "/experiments" },
          },
        },
      ],
    },
    {
      path: "/entrypoints",
      meta: { type: "entrypoints", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/EntryPointsView.vue"),
          name: "entrypoints",
        },
        {
          path: "/entrypoints/:id",
          component: () => import("../views/CreateEntryPoint.vue"),
          meta: {
            groupContext: { kind: "resource", resource: "entrypoints", idParam: "id", fallback: "/entrypoints" },
          },
        },
      ],
    },
    {
      path: "/plugins",
      meta: { type: "plugins", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/PluginsView.vue"),
          name: "plugins",
        },
        {
          path: "/plugins/new",
          component: () => import("../views/CreatePluginView.vue"),
        },
        {
          path: "/plugins/:id",
          component: () => import("../views/EditPluginView.vue"),
          name: "editPlugin",
          meta: {
            groupContext: { kind: "resource", resource: "plugins", idParam: "id", fallback: "/plugins" },
          },
        },
        {
          path: "/plugins/:id/files/:fileId",
          component: () => import("../views/CreatePluginFile.vue"),
          name: "pluginFile",
          meta: {
            groupContext: { kind: "resource", resource: "plugins", idParam: "id", fallback: "/plugins" },
          },
        },
      ],
    },
    {
      path: "/queues",
      meta: { type: "queues", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/QueuesView.vue"),
          name: "queues",
        },
        {
          path: "/queues/:id/:draftType/:newResourceDraft?",
          component: () => import("../views/QueuesFormDraftView.vue"),
          meta: {
            groupContext: { kind: "queueDraft", fallback: "/queues" },
          },
        },
        {
          path: "/queues/:id",
          component: () => import("../views/QueuesFormView.vue"),
          meta: {
            groupContext: { kind: "resource", resource: "queues", idParam: "id", fallback: "/queues" },
          },
        },
      ],
    },
    {
      path: "/jobs",
      meta: { type: "jobs", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/JobsView.vue"),
          name: "allJobs",
        },
        {
          path: "/jobs/new",
          component: () => import("../views/CreateJob.vue"),
        },
        {
          path: "/jobs/:id",
          component: () => import("../views/JobDashboardView.vue"),
          name: "jobDashboard",
          meta: {
            groupContext: { kind: "resource", resource: "jobs", idParam: "id", fallback: "/jobs" },
          },
        },
      ],
    },
    {
      path: "/groups",
      component: () => import("../views/GroupsView.vue"),
    },
    {
      path: "/groups/new",
      component: () => import("../views/CreateGroupView.vue"),
    },
    {
      path: "/groups/:id/admin",
      component: () => import("../views/GroupsAdminView.vue"),
      meta: { groupContext: { kind: "group", idParam: "id", fallback: "/groups" } },
    },
    {
      path: "/tags",
      component: () => import("../views/TagsView.vue"),
      name: "tags",
      meta: { groupContext: { kind: "selected" } },
    },
    {
      path: "/pluginParams",
      meta: { type: "pluginParams", groupContext: { kind: "selected" } },
      children: [
        {
          path: "",
          component: () => import("../views/PluginParamsView.vue"),
          name: "pluginParams",
        },
        {
          path: "/pluginParams/:id",
          component: () => import("../views/PluginParamForm.vue"),
          name: "editPluginParam",
          meta: {
            groupContext: {
              kind: "resource",
              resource: "pluginParameterTypes",
              idParam: "id",
              fallback: "/pluginParams",
            },
          },
        },
      ],
    },
    {
      path: "/models",
      component: () => import("../views/ModelsView.vue"),
      name: "models",
      meta: { groupContext: { kind: "selected" } },
    },
    {
      path: "/artifacts",
      meta: { type: "artifacts", groupContext: { kind: "selected" } },
      children: [
        {
          path: "/artifacts",
          component: () => import("../views/ArtifactsView.vue"),
          name: "artifacts",
        },
        {
          path: "/artifacts/:id",
          component: () => import("../views/EditArtifactView.vue"),
          meta: {
            groupContext: { kind: "resource", resource: "artifacts", idParam: "id", fallback: "/artifacts" },
          },
        },
      ],
    },
    {
      path: "/login",
      component: () => import("../views/BasicLoginView.vue"),
    },
    {
      path: "/register",
      component: () => import("@/components/RegisterForm.vue"),
    },
  ],
});

router.beforeEach(async (to, from) => {
  const store = useLoginStore();
  delete to.meta.backButton;
  delete to.meta.viaBadgeLink;

  // on every route change, close snapshot drawer if open
  if (store.showRightDrawer) {
    store.showRightDrawer = false;
    store.selectedSnapshot = null;
  }

  // check login status on mounted and reloads
  if (from === START_LOCATION) {
    store.initialPage = true;
    await callGetLoginStatus();
  } else {
    store.initialPage = false;
  }

  const isAuthRoute = to.path === "/login" || to.path === "/register";
  const isLoggedIn = !!store.loggedInUser;

  // redirect to login if logged out
  if (!isLoggedIn && !isAuthRoute) {
    return "/login";
  }

  const groupContext = to.meta.groupContext as GroupContext | undefined;
  if (!groupContext || isAuthRoute) {
    store.groupContextLocked = false;
    store.groupContextResolving = false;
    return true;
  }

  if (groupContext.kind === "selected" || isNewResourceRoute(to, groupContext)) {
    store.groupContextLocked = false;
    store.groupContextResolving = true;
    try {
      const requestedGroupId = parseGroupIdQuery(to.query.groupId);
      if (requestedGroupId !== null && !store.setLoggedInGroup(requestedGroupId)) {
        await api.refreshLoginState();
        if (!store.setLoggedInGroup(requestedGroupId)) {
          notify.error(`Group ${requestedGroupId} is not available to the current user.`);
        }
      }

      const selectedGroup = store.loggedInGroup;
      if (!selectedGroup || typeof selectedGroup !== "object") {
        return true;
      }

      const canonicalGroupId = String(selectedGroup.id);
      if (to.query.groupId !== canonicalGroupId) {
        return {
          path: to.path,
          query: { ...to.query, groupId: canonicalGroupId },
          hash: to.hash,
          replace: from === START_LOCATION,
        };
      }
    } catch (error) {
      const apiError = error as { response?: { data?: { message?: string } }; message?: string };
      notify.error(apiError.response?.data?.message || apiError.message || "Failed to restore group context.");

      const selectedGroup = store.loggedInGroup;
      if (selectedGroup && typeof selectedGroup === "object") {
        return {
          path: to.path,
          query: { ...to.query, groupId: String(selectedGroup.id) },
          hash: to.hash,
          replace: from === START_LOCATION,
        };
      }
    } finally {
      store.groupContextResolving = false;
    }
    return true;
  }

  store.groupContextResolving = true;
  try {
    const groupId = await resolveGroupContext(to, groupContext);
    if (groupId === null) {
      store.groupContextLocked = false;
      return true;
    }
    if (!store.setLoggedInGroup(groupId)) {
      await callGetLoginStatus();
      if (!store.setLoggedInGroup(groupId)) {
        throw new Error(`Group ${groupId} is not available to the current user.`);
      }
    }
    store.groupContextLocked = true;
  } catch (error) {
    store.groupContextLocked = false;
    const apiError = error as { response?: { data?: { message?: string } }; message?: string };
    notify.error(
      apiError.response?.data?.message || apiError.message || "Failed to resolve the resource group context.",
    );
    return groupContext.fallback;
  } finally {
    store.groupContextResolving = false;
  }

  // allow navigation
  return true;
});

function getRouteParam(to: RouteLocationNormalizedGeneric, name: string): string | null {
  const value = to.params[name];
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }
  return value ?? null;
}

function isNewResourceRoute(to: RouteLocationNormalizedGeneric, context: GroupContext): boolean {
  if (context.kind !== "resource") {
    return false;
  }
  return getRouteParam(to, context.idParam) === "new";
}

function parseGroupIdQuery(value: unknown): number | null {
  if (value === undefined) {
    return null;
  }
  if (typeof value !== "string" || !/^[1-9]\d*$/.test(value)) {
    throw new Error("The groupId query parameter must be a positive integer.");
  }
  const groupId = Number(value);
  if (!Number.isSafeInteger(groupId)) {
    throw new Error("The groupId query parameter must be a positive integer.");
  }
  return groupId;
}

async function resolveGroupContext(to: RouteLocationNormalizedGeneric, context: GroupContext): Promise<number | null> {
  if (context.kind === "selected") {
    return null;
  }
  const idParam = context.kind === "queueDraft" ? "id" : context.idParam;
  const rawId = getRouteParam(to, idParam);
  if (!rawId || rawId === "new") {
    return null;
  }

  const id = Number(rawId);
  if (!Number.isInteger(id)) {
    throw new Error(`Invalid resource ID: ${rawId}`);
  }

  let response;
  if (context.kind === "queueDraft") {
    const draftType = getRouteParam(to, "draftType");
    if (draftType !== "draft" && draftType !== "resourceDraft") {
      throw new Error(`Unsupported queue draft type: ${draftType}`);
    }
    response = await api.getItem("queues", id, draftType === "draft");
  } else if (context.kind === "group") {
    response = await api.getItem("groups", id);
  } else {
    response = await api.getItem(context.resource, id);
  }

  const rawGroupId = context.kind === "group" ? response.data?.id : (response.data?.group?.id ?? response.data?.group);
  const groupId = Number(rawGroupId);
  if (!Number.isInteger(groupId)) {
    throw new Error("The resource does not have a valid group context.");
  }
  return groupId;
}

async function callGetLoginStatus() {
  const store = useLoginStore();
  try {
    await api.refreshLoginState();
  } catch {
    store.clearSession();
  }
}

router.afterEach((to) => {
  const viaBadgeLink = window.history.state?.viaBadgeLink === true;
  if (viaBadgeLink) {
    to.meta.viaBadgeLink = true;
  }
  if (isHistoryTraversal) {
    to.meta.backButton = true;
  }
  isHistoryTraversal = false;
});

export default router;
