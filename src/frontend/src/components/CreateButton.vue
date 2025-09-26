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
          v-for="resource in defaultResources"
          clickable 
          :active="false"
          @click="handleClick(resource)"
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
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const store = useLoginStore()

const defaultResources = [
    {
      name: 'experiment',
      url: '/experiments/new'
    },
    {
      name: 'job',
      url: '/jobs/new'
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
    {
      name: 'plugin parameters',
      url: '/pluginParams',
      popup: true
    },
    {
      name: 'queue',
      url: '/queues',
      popup: true
    },
    {
      name: 'tag',
      url: '/tags',
      popup: true
    },
  ]

function handleClick(resource) {
  if(resource.url) {
    router.push(resource.url).then(() => {
      if(resource.popup) {
        store.triggerPopup = true
      }
    })
  }
}

</script>