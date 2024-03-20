<template>
  <h1 class="text-capitalize q-mb-xs">{{ title }}</h1>
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
  import { computed } from 'vue'

  const route = useRoute()

  const path = computed(() => {
    return route.path.split('/').slice(1)
  })

  const title = computed(() => {
    if(path.value[0] === 'entrypoints') return 'Entry Points'
    if(route.path === '/experiments/create') return 'New Experiment'
    return path.value[0]
  })


</script>