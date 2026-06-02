<template>
  <q-table
    ref="tableRef"
    v-model:selected="selected"
    v-model:showDeleted="showDeleted"
    v-model:pagination="pagination"
    :rows="props.rows"
    :columns="finalColumns"
    :title="title"
    :filter="filter"
    :selection="selection"
    :row-key="props.rowKey"
    :class="'q-mt-lg'"
    :style="sortIconStyle"
    flat
    bordered
    dense
    :tabindex="props.disableSelect ? '' : '0'"
    :rows-per-page-options="props.showAll ? [0] : [5, 10, 15, 20, 25, 50, 0]"
    :hideBottom="props.hideBottom && rows.length > 0"
    :loading="loading"
    color="primary"
    @request="onRequest"
    @keydown="keydown"
  >
    <template #header="headerProps">
      <q-tr :props="headerProps">
        <q-th
          v-for="col in headerProps.cols"
          :key="col.name"
          :props="headerProps"
          class="text-weight-bold text-uppercase text-subtitle1"
          :style="darkMode ? {} : { 'background-color': '#edebeb' }"
        >
          <span
            class="header-label"
            :class="darkMode ? 'header-label--dark' : 'header-label--light'"
          >
            {{ col.label }}
          </span>
          <q-icon
            v-if="col.sortable"
            :name="getSortIcon(col.name)"
            class="sort-icon"
          />
        </q-th>
      </q-tr>
    </template>
    <template #body="bodyProps">
      <!-- bodyProps.row[field] - field needs to be unique ID, pass this in as a prop, or just use id -->
      <q-tr
        :class="`
          cursor-pointer 
          ${getSelectedColor(bodyProps.selected)}
          ${highlightRow(bodyProps)}
          ${disableRow(bodyProps)}
          ${bodyProps.expand ? 'row-top-border' : ''}
        `"
        :props="bodyProps"
        :no-hover="bodyProps.expand"
        @click="
          openResource(bodyProps, $event);
          selectResource(bodyProps);
        "
        @auxclick="onAuxClick(bodyProps, $event)"
      >
        <q-td
          v-for="col in bodyProps.cols"
          :key="col.name"
          :props="bodyProps"
          :style="bodyProps.expand ? { 'border-bottom': 'none' } : {}"
        >
          <q-menu
            v-if="selection !== 'multiple' && !highlightSelection && !disableSelect"
            context-menu
            @show="bodyProps.selected = true"
          >
            <q-list dense>
              <q-item
                v-close-popup
                clickable
                @click="openResource(bodyProps)"
              >
                <q-item-section>Open</q-item-section>
              </q-item>
              <q-item
                v-close-popup
                clickable
                @click="openResource(bodyProps, null, true)"
              >
                <q-item-section>Open In New Tab</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
          <slot
            v-bind="bodyProps"
            :name="`body-cell-${col.name}`"
          >
            <div
              v-if="typeof col.value === 'boolean'"
              class="text-body1"
            >
              {{ col.value ? "✅" : "❌" }}
            </div>
            <div v-else-if="col.name === 'id'">
              <span class="link">{{ bodyProps.row.id }}</span>
              <q-icon
                name="open_in_new"
                size="sm"
                class="q-ml-sm"
                @click.stop="openResource(bodyProps, $event, true)"
              >
                <q-tooltip> Open In New Tab </q-tooltip>
              </q-icon>
            </div>
            <div v-else-if="col.name === 'name'">
              {{ truncateString(bodyProps.row.name, 20) }}
              <q-tooltip
                v-if="bodyProps.row.name.length >= 20"
                max-width="30vw"
                style="overflow-wrap: break-word"
              >
                {{ bodyProps.row.name }}
              </q-tooltip>
              <q-chip
                v-if="bodyProps.row.deleted"
                label="Deleted"
                outline
                :color="`${darkMode ? 'grey-4' : 'red'}`"
                dense
              />
            </div>
            <div v-else-if="col.name === 'description'">
              {{ truncateString(bodyProps.row.description, 40) }}
              <q-tooltip
                v-if="bodyProps.row.description?.length >= 40"
                max-width="30vw"
                style="overflow-wrap: break-word"
              >
                {{ bodyProps.row.description }}
              </q-tooltip>
            </div>
            <div
              v-else-if="col.name === 'tags'"
              class="tag-list-cell"
            >
              <q-chip
                v-for="(tag, i) in visibleTags(bodyProps.row.tags)"
                :key="i"
                color="primary"
                text-color="white"
                clickable
                @click.stop="!bodyProps.row.deleted && $emit('editTags', bodyProps.row)"
              >
                {{ formatTagName(tag) }}
                <q-tooltip
                  v-if="hasLongTagName(tag)"
                  max-width="30vw"
                  style="overflow-wrap: break-word"
                >
                  {{ tag.name }}
                </q-tooltip>
              </q-chip>
              <q-chip
                v-if="hiddenTags(bodyProps.row.tags).length"
                outline
                clickable
                :color="darkMode ? 'grey-4' : 'grey-7'"
                @click.stop
              >
                +{{ hiddenTags(bodyProps.row.tags).length }} more

                <q-menu max-width="300px">
                  <div class="tag-chip-menu q-pa-sm">
                    <q-chip
                      v-for="(tag, i) in hiddenTags(bodyProps.row.tags)"
                      :key="i"
                      color="primary"
                      text-color="white"
                      clickable
                      @click.stop="!bodyProps.row.deleted && $emit('editTags', bodyProps.row)"
                    >
                      {{ formatTagName(tag) }}
                      <q-tooltip
                        v-if="hasLongTagName(tag)"
                        max-width="30vw"
                        style="overflow-wrap: break-word"
                      >
                        {{ tag.name }}
                      </q-tooltip>
                    </q-chip>
                  </div>
                </q-menu>
              </q-chip>
              <q-btn
                v-if="bodyProps.row.deleted !== true"
                round
                size="xs"
                icon="add"
                color="grey-5"
                text-color="black"
                class="q-ml-xs"
                @click.stop="$emit('editTags', bodyProps.row)"
              />
            </div>
            <div v-else-if="col.name === 'createdOn' || col.name === 'created_on' || col.name === 'lastModifiedOn'">
              {{ formatDate(col.value) }}
            </div>
            <div
              v-else-if="col.resourceType"
              class="resource-badge-list-cell"
            >
              <ResourceBadgeList
                :resources="Array.isArray(col.value) ? col.value : [col.value]"
                :resourceType="col.resourceType"
                @sync="(resource) => $emit('syncResource', { row: bodyProps.row, col, resource })"
              />
              <q-btn
                v-if="col.showResourceAdd && bodyProps.row.deleted !== true"
                round
                size="sm"
                icon="add"
                class="q-ml-xs"
                @click.stop="$emit('addResource', { row: bodyProps.row, col })"
              />
            </div>
            <div v-else-if="!Array.isArray(col.value)">
              <!-- if value is an array, then render it with a custom slot -->
              {{ col.value }}
            </div>
            <q-btn
              v-if="col.name === 'delete' && bodyProps.row.deleted !== true"
              round
              color="negative"
              icon="sym_o_delete"
              size="sm"
              @click.stop="deleteResource(bodyProps)"
            />
            <q-btn
              v-if="col.name === 'expand'"
              size="md"
              flat
              dense
              round
              :icon="bodyProps.expand ? 'expand_less' : 'expand_more'"
              @click.stop="bodyProps.expand = !bodyProps.expand"
            />
          </slot>
        </q-td>
      </q-tr>
      <q-tr
        v-show="bodyProps.expand"
        :props="bodyProps"
        :class="`${highlightRow(bodyProps)} ${disableRow(bodyProps)}`"
        no-hover
      >
        <q-td colspan="100%">
          <!-- <div class="text-left ">Additional info for {{ bodyProps.row.name }}.</div> -->
          <slot
            name="expandedSlot"
            :row="bodyProps.row"
            :rowProps="bodyProps"
          />
        </q-td>
      </q-tr>
    </template>

    <template #top-right>
      <slot name="jobLogSlot" />
      <q-btn
        v-if="!hideCreateBtn"
        color="primary"
        icon="add"
        label="Create"
        class="q-mr-lg"
        @click="$emit('create')"
      />
      <q-toggle
        v-if="showDeletedToggle"
        v-model="showDeleted"
        color="red"
        label="Show Deleted"
        class="q-mr-lg"
        @click="refreshTable()"
      />
      <q-input
        v-if="!hideSearch"
        v-model="filter"
        debounce="300"
        dense
        placeholder="Search"
        outlined
      >
        <template #append>
          <q-icon name="search" />
        </template>
      </q-input>
      <caption
        v-if="props.rightCaption"
        class="text-caption"
      >
        {{
          props.rightCaption
        }}
      </caption>
    </template>
    <template
      v-if="showToggleDraft"
      #top-left
    >
      <q-btn-toggle
        v-model="showDrafts"
        toggle-color="primary"
        push
        style="box-shadow: 0 0 0 0.5px grey"
        :options="[
          { label: title, value: false },
          { label: 'Drafts', value: true },
        ]"
        @click="refreshTable"
      />
    </template>
  </q-table>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useRoute } from "vue-router";
import { useLoginStore } from "@/stores/LoginStore";
import { useQuasar } from "quasar";
import ResourceBadgeList from "@/components/ResourceBadgeList.vue";
import * as notify from "../notify";

const props = defineProps({
  columns: Array,
  rows: Array,
  title: String,
  showExpand: Boolean,
  hideCreateBtn: Boolean,
  showToggleDraft: Boolean,
  hideSearch: Boolean,
  disableSelect: Boolean,
  hideOpenBtn: Boolean,
  hideDeleteBtn: Boolean,
  hideBottom: Boolean,
  rightCaption: String,
  showAll: Boolean,
  enableHighlightRow: Boolean,
  selection: String,
  loading: Boolean,
  disabledRowKeys: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: String,
    default: "id",
  },
  showDeletedToggle: {
    type: Boolean,
    default: false,
  },
  highlightSelection: {
    type: Boolean,
    default: false,
  },
  defaultSort: {
    type: Object,
    default: () => ({ sortBy: "lastModifiedOn", descending: true }),
  },
  preserveSort: {
    type: Boolean,
    default: true,
  },
  tagLimit: {
    type: Number,
    default: 3,
    validator: (value) => Number.isFinite(value) && value > 0,
  },
});
const emit = defineEmits(["open", "delete", "request", "expand", "editTags", "create", "syncResource", "addResource"]);

const selection = computed(() => {
  if (props.disableSelect) return "none";
  if (props.selection === "multiple") return "multiple";
  return "single";
});

const finalColumns = computed(() => {
  let defaultColumns = [...props.columns];
  // if(!props.hideOpenBtn) {
  //   defaultColumns.push({ name: 'open', align: 'center', sortable: false, label: 'Open', headerStyle: 'width: 50px' })
  // }
  if (!props.hideDeleteBtn) {
    defaultColumns.push({
      name: "delete",
      align: "center",
      sortable: false,
      label: "Delete",
      headerStyle: "width: 50px",
    });
  }
  if (props.showExpand) {
    defaultColumns.push({
      name: "expand",
      align: "center",
      sortable: false,
      label: "Expand",
      headerStyle: "width: 50px",
    });
  }
  if (showDrafts.value) {
    defaultColumns = defaultColumns.map((column) => ({
      ...column,
      sortable: false,
    }));
  }
  return defaultColumns;
});

const $q = useQuasar();
const route = useRoute();
const loginStore = useLoginStore();

const darkMode = computed(() => {
  if ($q.dark.mode === "auto") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  return $q.dark.mode;
});

const sortIconStyle = computed(() => ({
  "--sort-icon-color": darkMode.value ? "#90CAF9" : "#1976D2",
}));

function getSortIcon(colName) {
  if (pagination.value.sortBy === colName) {
    return pagination.value.descending ? "arrow_downward" : "arrow_upward";
  }
  return "unfold_more";
}

const filter = ref("");
const selected = defineModel("selected");
//const showDrafts = ref(false)
const showDrafts = defineModel("showDrafts");
const showDeleted = defineModel("showDeleted");

function selectResource(tableProps) {
  if (props.disableSelect || props.selection !== "multiple") return;
  else tableProps.selected = !tableProps.selected;
}

function openResource(tableProps, event = null, openTab = false) {
  if (props.disableSelect || props.selection === "multiple") return;
  tableProps.selected = true;
  // ⌘ on macOS or Ctrl on windows should open new tab
  if (event?.metaKey || event?.ctrlKey) {
    emit("open", true);
  } else {
    emit("open", openTab);
  }
}

function onAuxClick(tableProps, event) {
  if (event.button === 1) {
    // mouse wheel click only
    openResource(tableProps, event, true);
  }
}

function deleteResource(tableProps) {
  tableProps.selected = true;
  if (props.disableSelect) return;
  emit("delete");
}

watch(showDrafts, (newVal, oldVal) => {
  if (newVal !== oldVal) selected.value = [];
});

watch(
  () => props.loading,
  async (newVal) => {
    if (!newVal) {
      await nextTick();
      // after loading, scroll to saved position
      if (route.meta.backButton && loginStore.tablePaginationCache[route.path]) {
        window.scrollTo({
          top: loginStore.tablePaginationCache[route.path].lastScrollPosition,
        });
      }
    }
  },
);

function getSelectedColor(selected) {
  if (!props.highlightSelection) return;
  if (darkMode.value && selected) return "bg-deep-purple-10";
  else if (selected) return "bg-blue-grey-1";
}

const pagination = ref({
  page: 1,
  rowsPerPage: props.showAll ? 0 : 15,
  sortBy: props.defaultSort.sortBy,
  descending: props.defaultSort.descending,
});

const tableRef = ref();
onMounted(() => {
  // Restore cached pagination when arriving via back; otherwise use defaults
  const key = route.path;
  const cached = loginStore.tablePaginationCache[key];
  if (route.meta.backButton && cached) {
    pagination.value = { ...pagination.value, ...cached };
    showDeleted.value = cached.showDeleted;
    filter.value = cached.search;
  } else if (cached) {
    delete loginStore.tablePaginationCache[key];
  }
  // get initial data from server with current pagination
  tableRef.value.requestServerInteraction();
});

defineExpose({ refreshTable, updateTotalRows });
function refreshTable() {
  tableRef.value.requestServerInteraction();
}

let invalidSearchNotification = notify.wait();

function onRequest(requestProps) {
  const searchError = checkSearch(requestProps.filter);

  invalidSearchNotification();
  if (searchError.length) {
    invalidSearchNotification = notify.wait(searchError);
    return;
  }
  pagination.value = requestProps.pagination;
  const paginationOptions = requestProps.pagination;
  const { page, rowsPerPage } = requestProps.pagination;
  const index = (page - 1) * rowsPerPage;
  paginationOptions.index = index;
  paginationOptions.search = requestProps.filter;
  emit("request", paginationOptions, showDrafts.value);
}

function checkSearch(string) {
  const trimmed = string.trimEnd();

  // if search ends with unescaped colon
  if (
    trimmed.length > 1 &&
    trimmed.endsWith(":") &&
    trimmed[trimmed.length - 2] !== "\\" &&
    trimmed[trimmed.length - 2] !== ":"
  ) {
    return `Enter a value after the trailing colon.`;
  }

  // if search ends with unescaped comma
  if (
    trimmed.length > 1 &&
    trimmed.endsWith(",") &&
    trimmed[trimmed.length - 2] !== "\\" &&
    trimmed[trimmed.length - 2] !== ","
  ) {
    return `Trailing comma.  Please remove or add new search criteria.`;
  }

  // Count unescaped single and double quotes
  let singleQuotes = 0;
  let doubleQuotes = 0;

  for (let i = 0; i < trimmed.length; i++) {
    const char = trimmed[i];
    const prevChar = trimmed[i - 1];

    if (char === "'" && prevChar !== "\\") {
      singleQuotes++;
    } else if (char === '"' && prevChar !== "\\") {
      doubleQuotes++;
    }
  }

  if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
    return `Unclosed quotation mark. Please close all quotes.`;
  }

  return "";
}

const path = route.path;

onBeforeUnmount(() => {
  invalidSearchNotification();

  // cache current pagination keyed by route path
  if (props.preserveSort) {
    loginStore.tablePaginationCache[path] = {
      page: pagination.value.page,
      rowsPerPage: pagination.value.rowsPerPage,
      sortBy: pagination.value.sortBy,
      descending: pagination.value.descending,
      showDeleted: props.showDeleted,
      search: filter.value,
      lastScrollPosition: window.scrollY,
    };
  }
});

function updateTotalRows(totalRows) {
  pagination.value.rowsNumber = totalRows;
}

function formatDate(dateString) {
  const options = {
    year: "2-digit",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  };
  return new Date(dateString).toLocaleString("en-US", options);
}

function keydown(event) {
  // exit if no rows or selection disabled
  if (!props.rows || props.rows.length === 0) return;
  if (props.disableSelect) return;

  // Get the current index of the selected row
  const currentIndex = props.rows.findIndex((row) => row[props.rowKey] === selected.value[0]?.[props.rowKey]);
  if (event.key === "ArrowUp") {
    // Navigate to the previous row (if not at the first row)
    if (currentIndex > 0) {
      const prevRow = props.rows[currentIndex - 1];
      selected.value = [prevRow];
    }
  } else if (event.key === "ArrowDown") {
    // Navigate to the next row (if not at the last row)
    if (currentIndex < props.rows.length - 1) {
      const nextRow = props.rows[currentIndex + 1];
      selected.value = [nextRow];
    }
  } else if (event.key === "Enter") {
    emit("open");
  }
}

function highlightRow(rowProps) {
  if (rowProps.row.deleted === true) {
    return darkMode.value ? "bg-red-dark-soft" : "bg-red-light";
  }
  if (props.disabledRowKeys.includes(rowProps.row[props.rowKey])) return;
  if (!props.enableHighlightRow) return;
  if (!rowProps.expand) return;
  if (darkMode.value) {
    return "bg-yellow-8 text-dark-gray row-bottom-border";
  } else {
    return "bg-yellow row-bottom-border";
  }
}

function disableRow(rowProps) {
  if (props.disabledRowKeys.includes(rowProps.row[props.rowKey])) {
    return "disabled-row";
  }
}

function truncateString(str, limit) {
  if (!str) return "";
  if (str?.length < limit) return str;
  return str?.slice(0, limit > 3 ? limit - 3 : limit) + "...";
}

function visibleTags(tags) {
  return Array.isArray(tags) ? tags.slice(0, props.tagLimit) : [];
}

function hiddenTags(tags) {
  return Array.isArray(tags) ? tags.slice(props.tagLimit) : [];
}

function hasLongTagName(tag) {
  return tag.name.length > 18;
}

function formatTagName(tag) {
  return hasLongTagName(tag) ? tag.name.replace(/(.{17})..+/, "$1…") : tag.name;
}
</script>

<style scoped>
:deep(.q-table td) {
  font-size: 14px;
}

:deep(.q-table__sort-icon) {
  display: none !important;
}

.disabled-row {
  pointer-events: none;
  opacity: 0.5;
}

.sort-icon {
  font-size: 1.5em;
  color: var(--sort-icon-color);
  margin-left: 4px;
  margin-bottom: 3px;
}

.header-label {
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-right: 4px;
}

.header-label--light {
  color: #546e7a;
}

.header-label--dark {
  color: #cbe8f5;
}

:deep(tr.row-bottom-border .q-td) {
  border-bottom: 1px solid #263238;
}

:deep(tr.row-top-border .q-td) {
  /* Draw a top separator on the main row even with collapsed borders */
  box-shadow: inset 0 1px 0 #263238;
}

:deep(.q-table__container table),
:deep(.q-table__middle table) {
  border-collapse: collapse;
  border-spacing: 0;
}

.tag-chip-menu {
  display: flex;
  flex-wrap: wrap;
  max-width: 300px;
}

.tag-list-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.resource-badge-list-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.resource-badge-list-cell :deep(.resource-badge-list) {
  display: contents;
}
</style>
