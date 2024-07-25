<template>
  <h1 class="q-mb-sm" 
    :class="{ invisible: title ? false : true }"
  >
    {{ title || 'Loading...' }}
  </h1>
  <nav aria-label="Breadcrumb">
    <q-breadcrumbs class="text-grey">
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
        class="text-capitalize"
      />
      <q-breadcrumbs-el
        v-if="route.params.id && route.params.fileId"
        :label="`${objName} Files`"
        :to="`/plugins/${route.params.id}/files`"
      />
      <q-breadcrumbs-el
        v-if="route.path === `/experiments/${route.params.id}/jobs/new`"
        :label="`${objName} jobs`"
        :to="`/experiments/${route.params.id}/jobs`"
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
  import { ref, computed, watch } from 'vue'
  import * as api from '@/services/dataApi'

  defineProps(['title'])

  const route = useRoute()

  const path = computed(() => {
    return route.path.split('/').slice(1)
  })


  const objName = ref('')

  if(route.params.id && route.params.fileId) {
    getName('plugins')
  }
  if(route.params.id && path.value.includes('jobs')) {
    getName('experiments')
  }

  async function getName(type) {
    try {
      const res = await api.getItem(type, route.params.id)
      objName.value = res.data.name
    } catch(err) {
      console.log(err)
    } 
  }


</script>