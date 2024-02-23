<template>
  <PageTitle />
  <q-btn 
    class="fixedButton"
    round
    color="primary"
    icon="add"
    size="lg"
  >
    <q-tooltip>
      Create a new Experiment
    </q-tooltip>
    <q-menu>
      <q-list>
        <q-item clickable to="/experiments/create">
          <q-item-section>Create Experiment</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Job</q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable>
          <q-item-section>Create Entry Point</q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<script setup>
  import PageTitle from '@/components/PageTitle.vue'
</script>
