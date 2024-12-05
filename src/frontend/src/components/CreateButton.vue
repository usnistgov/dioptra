<template>
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
  >
    <span class="sr-only">Create new resource</span>
    <q-tooltip>
      Create new resource
    </q-tooltip>
    <q-menu anchor="top middle" self="bottom middle">
      <q-list separator>
        <q-item
          v-for="resource in resources"
          clickable 
          :to="resource.url"
          @click="store.triggerPopup = true"
        >
          <q-item-section class="text-capitalize">
            Create {{ resource.name }}
          </q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<script setup>
import { useLoginStore } from '@/stores/LoginStore.ts'

const store = useLoginStore()

const resources = [
  {
    name: 'experiment',
    url: '/experiments/new'
  },
  {
    name: 'entrypoint',
    url: '/entrypoints/new'
  },
  {
    name: 'plugin',
    url: '/plugins',
    popup: true
  },
]

</script>