<template>
  <div>
    <div class="q-mb-sm">
      <h1 class="q-mb-none">
        {{ title }}
      </h1>

      <q-badge
        v-if="draftLabel"
        :label="draftLabel"
        outline
        color="primary"
        class="q-ml-md"
        :class="darkMode ? 'text-white' : ''"
      />
    </div>

    <nav aria-label="Breadcrumb" style="font-size: 1.2em;">
      <q-breadcrumbs class="text-grey">
        <template #separator>
          <q-icon name="arrow_forward" />
        </template>

        <q-breadcrumbs-el
          v-for="(crumb, index) in breadcrumbs"
          :key="`${crumb.label}-${index}`"
          :label="crumb.label"
          :icon="crumb.icon"
          :to="crumb.to"
          :aria-current="crumb.current ? 'page' : 'false'"
          :aria-disabled="crumb.disabled ? 'true' : 'false'"
          :class="crumb.class"
        />
      </q-breadcrumbs>
    </nav>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute } from 'vue-router'
import * as api from '@/services/dataApi'

const props = defineProps({
  title: {
    type: String,
    required: true,
    default: '',
  },
  draftLabel: {
    type: String,
    default: '',
  },
})

const darkMode = inject('darkMode')
const route = useRoute()
const objName = ref('')

const path = computed(() => route.path.split('/').filter(Boolean))

const sectionLabel = computed(() => {
  return path.value[0] === 'pluginParams' ? 'Plugin Parameters' : path.value[0]
})

const parentObjectRoute = computed(() => {
  if (route.name === 'pluginFile') {
    return {
      label: objName.value,
      to: `/plugins/${route.params.id}`,
    }
  }

  if (route.name === 'createExperimentJob') {
    return {
      label: objName.value,
      to: `/experiments/${route.params.id}`,
    }
  }

  return null
})

const breadcrumbs = computed(() => {
  const crumbs = [
    {
      label: 'Home',
      icon: 'home',
      to: '/',
    },
  ]

  if (path.value[0]) {
    crumbs.push({
      label: sectionLabel.value,
      to: path.value[1] ? `/${path.value[0]}` : undefined,
      current: path.value.length === 1,
      class: 'text-capitalize',
    })
  }

  if (parentObjectRoute.value?.label) {
    crumbs.push({
      label: parentObjectRoute.value.label,
      to: parentObjectRoute.value.to,
    })
  }

  if (path.value[1]) {
    crumbs.push({
      label: props.title,
      current: true,
      disabled: true,
    })
  }

  return crumbs
})

if (route.name === 'pluginFile') {
  getName('plugins')
} else if (route.name === 'createExperimentJob') {
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