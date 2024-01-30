<template>
  <q-dialog v-model="show">
    <q-card style="width: 95%" flat >
      <q-form @submit="$emit('submit', name)">
        <q-card-section class="bg-primary text-white q-mb-md">
          <div class="text-h6">Register Queue</div>
        </q-card-section>
        <q-card-section class="">
          <div class="row items-center">
            <div class="col-3 q-mb-lg">
              Queue Name:
            </div>
            <q-input class="col" outlined dense v-model="name" autofocus :rules="[rules.requiredRule]" >
            </q-input>
          </div>
        </q-card-section>
        <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Cancel" v-close-popup outline />
          <q-btn flat label="Confirm" type="submit" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import { computed, ref } from 'vue'
  import * as rules from '@/services/validationRules'

  const props = defineProps(['showAddDialog'])
  const emit = defineEmits(['submit', 'update:modelValue' ])

  const name = ref('')

  const show = computed({
    get() { return props.showAddDialog },
    set(newValue) { emit('update:modelValue', newValue) }
  })

</script>