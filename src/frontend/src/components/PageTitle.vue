<template>
  <div class="text-h3 q-mb-xs">{{ data[routeName].title }}</div>
  <q-breadcrumbs class="text-grey">
    <template v-slot:separator>
      <q-icon
        size="1.2em"
        name="arrow_forward"
      />
    </template>
    <q-breadcrumbs-el label="Home" icon="home" to="/" />
    <q-breadcrumbs-el :label="data[routeName].finalBreadcrumb" class="text-primary" />
  </q-breadcrumbs>
</template>

<script setup>
  import { useRoute } from 'vue-router'

  const route = useRoute()

  const routeName = route.name

  const data = {
    entrypoints: {
      title: 'Entry-Points',
      finalBreadcrumb: 'Entry Points'
    },
    queues: {
      title: 'Queues',
      finalBreadcrumb: 'Queues'
    }
  }
</script>