<template>
  <div class="row">
    <div class="col-3">
      <h2>General</h2>
      <q-input 
        outlined 
        dense 
        v-model.trim="name"
        :rules="[requiredRule]"
        class="q-mb-sm q-mt-md"
        aria-required="true"
      >
        <template v-slot:before>
          <label :class="`field-label`">Entry Point Name:</label>
        </template>
      </q-input>
    </div>
    <div class="col-4 offset-md-2">
      <h2 class="q-mb-md">Owner Only Options</h2>
      <q-list bordered>
        <q-item>
          <q-item-section>
            <q-item-label class="text-bold">Transfer Ownership</q-item-label>
            <q-item-label caption lines="1">Transfer this group to another user.</q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn 
              label="Transfer Ownership"
              color="primary"
            />
          </q-item-section>
        </q-item>
        <q-separator />
        <q-item>
          <q-item-section>
            <q-item-label class="text-bold">Delete Group</q-item-label>
            <q-item-label caption lines="1">Once you delete a group it CAN NOT be undone.</q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn 
              label="Delete Group"
              color="negative"
            />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </div>
  <h2 class="q-mt-xl">Members</h2>
</template>

<script setup>
  import { ref } from 'vue'

  const name = ref('')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

</script>