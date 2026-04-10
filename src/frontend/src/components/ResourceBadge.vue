<template>
  <span class="q-gutter-x-xs" :class="{ 'rb-stacked': props.stacked }">
    <q-chip
      :color="styles.color"
      square
      outline
      :clickable="props.clickable"
      :removable="removable"
      @remove="$emit('remove')"
      @click.stop="openResource"
      @auxclick.stop="onAuxClick"
    >
      <span ref="chipTarget" class="rb-label">
        <q-icon
          v-if="styles.icon"
          :name="styles.icon"
          size="xs"
          class="q-mr-sm"
        />
        {{ resource?.name }}
        <span
          v-if="resource?.deleted"
          class="q-ml-sm"
        >
          ❌
        </span>

        <q-badge
          v-if="resource?.latestSnapshot === false"
          color="red"
          label="outdated"
          rounded
          class="q-ml-xs"
        />
      </span>

      <q-btn
        v-if="resource?.latestSnapshot === false"
        round
        dense
        color="red"
        icon="sync"
        size="xs"
        padding="xs"
        class="q-ml-xs"
        @click.stop="$emit('sync')"
      >
        <q-tooltip>
          Sync to latest version
        </q-tooltip>
      </q-btn>

      <q-tooltip v-if="resource?.deleted" :target="chipTarget">
        This <span class="text-capitalize">{{ resourceType }}</span> has been deleted
      </q-tooltip>
      <q-tooltip
        v-else-if="props.clickable"
        class="text-capitalize"
        :target="chipTarget"
      >
        Go To: {{ resourceType }} (ID {{ resource.id
        }}{{ resource.snapshotId ? `, Snapshot ${resource.snapshotId}` : "" }})
      </q-tooltip>

      <q-menu context-menu>
        <q-list dense>
          <q-item
            clickable
            v-close-popup
            @click.stop="openResource"
          >
            <q-item-section>Open</q-item-section>
          </q-item>
          <q-item
            clickable
            v-close-popup
            @click.stop="openInNewTab"
          >
            <q-item-section>Open In New Tab</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-chip>


  </span>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { getResourceStyle } from "@/services/resourceStyles"
import { useRouter } from "vue-router"

const emit = defineEmits(['sync', 'remove'])
const router = useRouter()
const darkMode = inject("darkMode")

const props = defineProps({
  resource: Object,
  resourceType: String,
  removable: { type: Boolean, default: false },
  clickable: { type: Boolean, default: true },
  // When true, place the badge on its own line
  stacked: { type: Boolean, default: false }
})

const chipTarget = ref()

const styles = computed(() => {
  return getResourceStyle(props.resourceType, darkMode.value)
})

const formattedUrl = computed(() => {
  const url = props.resource?.url?.replace(/^\/api\/v1/, "")
  if (!url) {
    return `/${props.resourceType}s/${props.resource.id}`
  }

  const parts = url.split("/").filter(Boolean)

  if (parts.length === 4 && parts[2] === "snapshots") {
    const [resourceType, resourceId, , snapshotId] = parts
    return `/${resourceType}/${resourceId}?snapshotId=${snapshotId}`
  }

  return url
})

function openInNewTab() {
  if (!formattedUrl.value) return
  window.open(formattedUrl.value, "_blank")
}

function onAuxClick(event) {
  if (event.button === 1) {
    openInNewTab()
  }
}

function openResource(event) {
  if (!formattedUrl.value) return

  // ⌘ on macOS or Ctrl on Windows/Linux opens in a new tab
  if (event?.metaKey || event?.ctrlKey) {
    openInNewTab()
    return
  }

  router.push(formattedUrl.value)
}
</script>

<style scoped>
.rb-stacked {
  display: block;
  width: 100%;
  margin-top: 4px;
}
</style>
