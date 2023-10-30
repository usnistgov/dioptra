<template>
  <q-tabs inline-label class="nav-bar">
    <q-route-tab label="Login" icon="login" to="/" />
    <q-route-tab label="API" icon="language" to="/api" />

    <q-toggle
      v-model="darkMode"
      class="absolute-right q-mr-sm" 
      :label="`${$q.dark.isActive ? 'Dark' : 'Light'} Mode `"
      @click="$q.dark.toggle()"
    >
      <q-icon :name="darkMode ? 'bedtime' : 'light_mode'" size="xs"/>
    </q-toggle>
  </q-tabs>
</template>

<script setup lang="ts">
  import { useQuasar } from 'quasar'

  const $q = useQuasar()
  const darkMode = JSON.parse(JSON.stringify($q.dark.isActive))
</script>

<style lang="scss" scoped>
  body.body--dark a {
    color: white;
  }
</style>