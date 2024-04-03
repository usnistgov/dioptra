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
  <BasicTable
    :columns="columns"
    :rows="store.users"
    @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
    @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
  >
  </BasicTable>
</template>

<script setup>
  import { ref } from 'vue'
  import BasicTable from '@/components/BasicTable.vue'
  import { useLoginStore } from '@/stores/LoginStore'

  const store = useLoginStore()

  const name = ref('')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'read', label: 'Read', align: 'left', field: 'read', sortable: true },
    { name: 'write', label: 'Write', align: 'left', field: 'write', sortable: true },
    { name: 'shareRead', label: 'Share Read', align: 'left', field: 'shareRead', sortable: true, style: 'width: 200px' },
    { name: 'shareWrite', label: 'Share Write', align: 'left', field: 'shareWrite', sortable: true, style: 'width: 200px' },
    { name: 'admin', label: 'Admin', align: 'left', field: 'admin', sortable: true },
    { name: 'owner', label: 'Owner', align: 'left', field: 'owner', sortable: true },
    { name: 'actions', label: 'Actions', align: 'center',  },
  ]

</script>