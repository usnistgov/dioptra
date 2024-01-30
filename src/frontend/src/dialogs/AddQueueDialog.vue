<template>
  <q-dialog v-model="showDialog">
    <q-card style="width: 95%" flat >
      <q-form @submit="$emit('submit', name)">
        <q-card-section class="bg-primary text-white q-mb-md">
          <div class="text-h6">Register Queue</div>
        </q-card-section>
        <q-card-section>
          <div class="row items-center">
            <div class="col-3 q-mb-lg">
              Queue Name:
            </div>
            <q-input class="col" outlined dense v-model="name" autofocus :rules="[rules.requiredRule]" >
            </q-input>
          </div>
          <div class="row items-center">
            <div class="col-3">
              Locked:
            </div>
            <q-toggle v-model="locked" />
            <q-icon :name="locked ? 'sym_o_lock' : 'lock_open'" size="sm" />
          </div>
        </q-card-section>
        <q-separator />
        <q-card-actions align="right" class="text-primary">
          <q-btn color="blue-grey-4" class="text-white" label="Cancel" v-close-popup />
          <q-btn color="secondary" label="Confirm" type="submit" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import { ref } from 'vue'
  import * as rules from '@/services/validationRules'

  const showDialog = defineModel()

  const name = ref('')
  const locked = ref(true)


</script>