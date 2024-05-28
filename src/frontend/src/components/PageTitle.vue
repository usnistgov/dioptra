<template>
  <h1 class="text-capitalize q-mb-sm" @click="console.log(route, title)">{{ title }}</h1>
  <nav aria-label="Breadcrumb">
    <q-breadcrumbs class="text-grey text-capitalize">
      <template v-slot:separator>
        <q-icon
          size="1.2em"
          name="arrow_forward"
        />
      </template>
      <q-breadcrumbs-el label="Home" icon="home" to="/" />
      <q-breadcrumbs-el 
        :label="path[0]" 
        :to="path[1] ? `/${path[0]}` : ''" 
        :aria-current="`${path.length === 1 ? 'true' : 'false'}`"
      />
      <q-breadcrumbs-el
        v-if="route.params.id && route.params.fileId"
        :label="`${getPluginName(route.params.id)} Files`"
        :to="`/plugins/${route.params.id}/files`"
      />
      <q-breadcrumbs-el
        v-if="path[1]"
        :label="title"
        aria-disabled="true"
        aria-current="page"
      />
    </q-breadcrumbs>
  </nav>
</template>

<script setup>
  import { useRoute } from 'vue-router'
  import { computed, watch } from 'vue'
  import { useDataStore } from '@/stores/DataStore.ts'
  const store = useDataStore()

  const route = useRoute()

  const path = computed(() => {
    return route.path.split('/').slice(1)
  })

  const newOrEdit = computed(() => {
    return store.editMode ? 'Edit' : 'New'
  })

  watch(() => route.path, (newVal) => {
    if(newVal !== '/entrypoints/create' && newVal !== '/experiments/create' && newVal !== '/groups/admin') {
      store.editMode = false
    }
  })

  const title = computed(() => {
    if(route.path === '/entrypoints/create') return `${newOrEdit.value} Entry Point`
    if(route.path === '/groups/admin') return `${store.editMode ? 'Edit Group ' : 'New Group'}`
    if(path.value[0] === 'entrypoints') return 'Entry Points'
    if(route.path === '/experiments/create') return `${newOrEdit.value} Experiment`
    if(path.value[2] === 'files' && !route.params.fileId) return `${getPluginName(route.params.id)} Files`
    if(path.value[2] === 'files' && route.params.fileId) return `File ${route.params.fileId}`
    if(path.value[0] === 'plugins' && path.value[1]) return 'Edit Plugin' 
    return path.value[0]
  })

  function getPluginName(id) {
    return store.plugins.find((plugin) => plugin.id === id).name
  }

</script>