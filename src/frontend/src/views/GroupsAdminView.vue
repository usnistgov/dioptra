<template>
  <PageTitle title="Groups Admin" />
  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg `">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset class="q-pa-lg">
        <legend>Basic Info</legend>
        <div class="row items-center">
          <div class="col-9">
            <q-input 
              outlined 
              dense 
              v-model.trim="name"
              :rules="[requiredRule]"
              class="q-mb-sm"
              aria-required="true"
            >
              <template v-slot:before>
                <label :class="`field-label-short`">Group Name:</label>
              </template>
            </q-input>
          </div>
          <div class="col">
            <q-btn 
              label="Save Name"
              color="primary"
              class="float-right q-mb-lg"
            />
          </div>
        </div>
      </fieldset>

      <fieldset class="q-mt-xl q-pa-lg" v-if="dataStore.editMode">
        <legend>Owner Only Options</legend>
        <q-list bordered>
          <q-item>
            <q-item-section>
              <q-item-label class="text-bold">Delete Group</q-item-label>
              <q-item-label caption >Once you delete a group it CAN NOT be undone.</q-item-label>
            </q-item-section>

            <q-item-section side>
              <q-btn 
                label="Delete Group"
                color="negative"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </fieldset>

      <fieldset class="q-mt-xl q-pa-lg">
        <legend>Add User</legend>
        <div class="row items-center">
          <div class="col-9">
            <q-input 
              outlined 
              dense 
              v-model.trim="name"
              :rules="[requiredRule]"
              class="q-mb-sm "
              aria-required="true"
            >
              <template v-slot:before>
                <label :class="`field-label-short`">Search User:</label>
              </template>
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="col">
            <q-btn 
              label="Search"
              color="primary"
              class="float-right q-mb-lg"
            />
          </div>
        </div>
        <q-card flat bordered class="my-card">
          <q-card-section>
            <div class="">Search Results</div>
          </q-card-section>

          <q-card-section class="q-pt-none overflow-auto">
            <q-list dense style="max-height: 10vh;">
              <q-item v-for="(user, i) in searchResults" :key="i" style="border: 1px solid lightgray;">
                <q-item-section>
                  <q-item-label class="text-bold">{{ user }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    round
                    icon="add"
                    color="secondary"
                    size="xs"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

        </q-card>

      </fieldset>

    </div>
    <fieldset :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'} overflow-auto`" >
      <legend>Group Members</legend>
      <BasicTable
        :columns="columns"
        :rows="store.users"
        :hideEditRow="true"
        @edit="(param, i) => {selectedParam = param; selectedParamIndex = i; showEditParamDialog = true}"
        @delete="(param) => {selectedParam = param; showDeleteDialog = true}"
        style="max-height: 500px;"
        class="q-mt-xl"
      />
    </fieldset>
  </div>
</template>

<script setup>
  import { ref, inject } from 'vue'
  import BasicTable from '@/components/BasicTable.vue'
  import { useLoginStore } from '@/stores/LoginStore'
  import { useDataStore } from '@/stores/DataStore.ts'
  import PageTitle from '@/components/PageTitle.vue'
  
  const dataStore = useDataStore()

  const isMobile = inject('isMobile')

  const store = useLoginStore()

  const name = ref('')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required"

  const columns = [
    { name: 'name', label: 'Name', align: 'left', field: 'name', sortable: true },
    { name: 'read', label: 'Read', align: 'left', field: 'read', sortable: true },
    { name: 'write', label: 'Write', align: 'left', field: 'write', sortable: true },
    { name: 'shareRead', label: 'Share Read', align: 'left', field: 'shareRead', sortable: true, style: 'width: 100px' },
    { name: 'shareWrite', label: 'Share Write', align: 'left', field: 'shareWrite', sortable: true, style: 'width: 100px' },
    { name: 'admin', label: 'Admin', align: 'left', field: 'admin', sortable: true },
    { name: 'owner', label: 'Owner', align: 'left', field: 'owner', sortable: true },
    { name: 'actions', label: 'Actions', align: 'center',  },
  ]

  const searchResults = ref(['Henry', 'Bob', 'Joe', 'Larry', 'John', 'Dan'])

</script>