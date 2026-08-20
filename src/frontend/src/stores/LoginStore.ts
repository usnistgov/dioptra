import { defineStore } from "pinia";
import { ref, computed } from "vue";

const GROUP_STORAGE_KEY = "dioptra_group_id";

type UserRef = {
  id: number;
  username: string;
  url: string;
};

type GroupRef = {
  id: number;
  name: string;
  user: UserRef;
  url: string;
};

function getGroupStorageKey(userId: number) {
  return `${GROUP_STORAGE_KEY}:${userId}`;
}

function readStoredGroupId(userId: number): number | null {
  const raw = localStorage.getItem(getGroupStorageKey(userId));
  if (!raw) {
    return null;
  }

  const groupId = Number(raw);
  return Number.isNaN(groupId) ? null : groupId;
}

function writeStoredGroupId(userId: number, groupId: number) {
  localStorage.setItem(getGroupStorageKey(userId), String(groupId));
}

function clearStoredGroupId(userId: number) {
  localStorage.removeItem(getGroupStorageKey(userId));
}

export const useLoginStore = defineStore("login", () => {
  // ref()'s are state properties
  const loggedInUser = ref({});

  const groups = ref<GroupRef[]>([]);
  const selectedGroupId = ref<number | null>(null);
  const groupContextLocked = ref(false);
  const groupContextResolving = ref(false);

  const createdGroups = computed(() => {
    const userId = getLoggedInUserId();
    return userId === null ? [] : groups.value.filter((group) => Number(group.user.id) === userId);
  });

  function getLoggedInUserId(): number | null {
    const userId = Number((loggedInUser.value as { id?: number }).id);
    return Number.isNaN(userId) ? null : userId;
  }

  const loggedInGroup = computed(() => {
    if (groups.value.length === 0) {
      return "";
    }

    if (selectedGroupId.value !== null) {
      const selectedGroup = groups.value.find((group) => group.id === selectedGroupId.value);
      if (selectedGroup) {
        return selectedGroup;
      }
    }

    selectedGroupId.value = groups.value[0].id;
    const userId = getLoggedInUserId();
    if (userId !== null) {
      writeStoredGroupId(userId, groups.value[0].id);
    }
    return groups.value[0];
  });

  function setGroups(newGroups: GroupRef[]) {
    groups.value = newGroups;
    const userId = getLoggedInUserId();
    selectedGroupId.value = userId === null ? null : readStoredGroupId(userId);

    if (groups.value.length === 0) {
      selectedGroupId.value = null;
      if (userId !== null) {
        clearStoredGroupId(userId);
      }
      return;
    }

    const selected = groups.value.find((group) => group.id === selectedGroupId.value);
    if (!selected) {
      selectedGroupId.value = groups.value[0].id;
      if (userId !== null) {
        writeStoredGroupId(userId, groups.value[0].id);
      }
    }
  }

  function setLoggedInGroup(groupId: number): boolean {
    const group = groups.value.find((g) => g.id === groupId);
    if (!group) {
      return false;
    }

    selectedGroupId.value = groupId;
    const userId = getLoggedInUserId();
    if (userId !== null) {
      writeStoredGroupId(userId, groupId);
    }
    return true;
  }

  const users = ref([
    { name: "Tatum", id: "1", read: true, write: true, admin: true, owner: true },
    {
      name: "Jaylen",
      id: "2",
      read: false,
      write: false,
      admin: false,
      owner: false,
    },
    {
      name: "Kristaps",
      id: "3",
      read: false,
      write: false,
      admin: false,
      owner: false,
    },
    { name: "Jrue", id: "4", read: true, write: false, admin: false, owner: false },
    {
      name: "Derrick",
      id: "5",
      read: true,
      write: true,
      admin: false,
      owner: false,
    },
    {
      name: "Payton",
      id: "6",
      read: false,
      write: true,
      admin: false,
      owner: false,
    },
    { name: "Sam", id: "7", read: true, write: true, admin: true, owner: true },
    { name: "Al", id: "8", read: false, write: false, admin: false, owner: false },
    { name: "Luke", id: "9", read: true, write: true, admin: false, owner: false },
    { name: "Paul", id: "10", read: true, write: true, admin: false, owner: false },
    {
      name: "Kevin",
      id: "11",
      read: false,
      write: false,
      admin: false,
      owner: false,
    },
    { name: "Ray", id: "12", read: true, write: false, admin: false, owner: false },
    {
      name: "Antoine",
      id: "13",
      read: false,
      write: false,
      admin: false,
      owner: false,
    },
    {
      name: "Marcus",
      id: "14",
      read: false,
      write: true,
      admin: false,
      owner: false,
    },
    { name: "Larry", id: "15", read: true, write: true, admin: true, owner: true },
    {
      name: "Isiah",
      id: "16",
      read: true,
      write: false,
      admin: false,
      owner: false,
    },
    {
      name: "Rajon",
      id: "17",
      read: false,
      write: false,
      admin: false,
      owner: false,
    },
    {
      name: "Sofia",
      id: "18",
      read: true,
      write: false,
      admin: false,
      owner: false,
    },
    {
      name: "Avery",
      id: "19",
      read: true,
      write: true,
      admin: false,
      owner: false,
    },
    { name: "Mila", id: "20", read: true, write: false, admin: false, owner: false },
  ]);

  const savedForms = ref({
    jobs: {},
    files: {},
  });

  const triggerPopup = ref(false);

  const showRightDrawer = ref(false);
  const selectedSnapshot = ref();

  const initialPage = ref(false);

  // cache table pagination by route path (in-memory; resets on refresh)
  const tablePaginationCache = ref<
    Record<
      string,
      {
        page: number;
        rowsPerPage: number;
        sortBy?: string;
        descending?: boolean;
        lastScrollPosition?: number;
        search?: string;
      }
    >
  >({});

  // computed()'s are getters

  // function()'s are actions

  return {
    loggedInUser,
    loggedInGroup,
    groups,
    createdGroups,
    groupContextLocked,
    groupContextResolving,
    users,
    savedForms,
    showRightDrawer,
    selectedSnapshot,
    triggerPopup,
    initialPage,
    tablePaginationCache,
    setGroups,
    setLoggedInGroup,
  };
});
