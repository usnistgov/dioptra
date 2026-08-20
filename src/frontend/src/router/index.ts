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

type GroupContext = ResourceGroupContext | QueueDraftGroupContext | GroupSelfContext;

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
      meta: { type: "experiments" },
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
      meta: { type: "entrypoints" },
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
      meta: { type: "plugins" },
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
      meta: { type: "queues" },
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
      meta: { type: "jobs" },
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
    },
    {
      path: "/pluginParams",
      meta: { type: "pluginParams" },
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
    },
    {
      path: "/artifacts",
      meta: { type: "artifacts" },
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

async function resolveGroupContext(to: RouteLocationNormalizedGeneric, context: GroupContext): Promise<number | null> {
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
    const res = await api.getLoginStatus();
    store.loggedInUser = res.data;
    store.setGroups(res.data.groups);
  } catch {
    store.loggedInUser = "";
  }
}

router.afterEach((to, from) => {
  // remember pagination when clicking into a resource then going back to the table
  const backButton = window.event?.type === "popstate";
  const backToSameType = to.meta?.type === from.meta?.type;
  const jobBackToExperiment = to.name === "experimentJobs" && from.name === "jobDashboard";
  const viaBadgeLink = window.history.state?.viaBadgeLink === true;
  if (viaBadgeLink) {
    to.meta.viaBadgeLink = true;
  }
  if (backButton && (backToSameType || jobBackToExperiment || from.meta?.viaBadgeLink)) {
    to.meta.backButton = true;
  }

  // ensure only to and from pagination settings are stored
  const store = useLoginStore();
  const keep = new Set<string>([to.path, from.path]);
  Object.keys(store.tablePaginationCache).forEach((k) => {
    if (!keep.has(k)) {
      delete (store.tablePaginationCache as any)[k];
    }
  });
});

export default router;
