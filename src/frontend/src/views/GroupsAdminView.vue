<template>
  <PageTitle subtitle="Groups Admin" conceptType="group" />
  <div :class="`row q-mt-lg ${isMobile ? '' : 'q-mx-xl'} q-mb-lg `">
    <div :class="`${isMobile ? 'col-12' : 'col-5'} q-mr-xl`">
      <fieldset class="q-pa-lg">
        <legend>Basic Info</legend>
        <div class="row items-center q-gutter-x-md">
          <q-input
            outlined
            dense
            v-model.trim="name"
            :rules="[requiredRule]"
            class="col-grow"
            bg-color="white"
          >
            <template v-slot:before>
              <label class="field-label text-weight-medium">Group Name:</label>
            </template>
          </q-input>
          <q-btn label="Save" color="primary" class="q-mb-md" />
        </div>
      </fieldset>

      <fieldset class="q-mt-lg q-pa-lg">
        <legend class="text-negative">Owner Options</legend>
        <q-list separator>
          <q-item>
            <q-item-section>
              <q-item-label class="text-bold">Delete Group</q-item-label>
              <q-item-label caption class="text-red">
                Action is permanent and cannot be undone.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                label="Delete"
                color="negative"
                outline
                icon="delete_forever"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </fieldset>

      <fieldset class="q-mt-lg q-pa-lg">
        <legend>Add User</legend>
        <div class="row items-center q-gutter-x-md q-mb-md">
          <q-input
            outlined
            dense
            v-model.trim="searchQuery"
            placeholder="Search by name..."
            class="col-grow"
            bg-color="white"
            @keyup.enter="performSearch"
          >
            <template v-slot:append>
              <q-icon
                name="search"
                class="cursor-pointer"
                @click="performSearch"
              />
            </template>
          </q-input>
          <q-btn label="Search" color="primary" @click="performSearch" />
        </div>

        <q-card flat bordered v-if="searchResults.length > 0">
          <q-card-section class="bg-grey-2 q-py-xs text-caption text-bold">
            Results
          </q-card-section>
          <q-scroll-area style="height: 150px">
            <q-list separator dense>
              <q-item
                v-for="(user, i) in searchResults"
                :key="i"
                clickable
                v-ripple
              >
                <q-item-section avatar>
                  <q-avatar size="sm" color="primary" text-color="white">{{
                    user.charAt(0)
                  }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium">{{
                    user
                  }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    round
                    flat
                    icon="person_add"
                    color="secondary"
                    size="sm"
                  >
                    <q-tooltip>Add to Group</q-tooltip>
                  </q-btn>
                </q-item-section>
              </q-item>
            </q-list>
          </q-scroll-area>
        </q-card>
      </fieldset>
    </div>

    <fieldset
      :class="`${isMobile ? 'col-12 q-mt-lg' : 'col'}`"
      style="display: flex; flex-direction: column"
    >
      <legend>Group Members</legend>

      <TableComponent
        :rows="store.users"
        :columns="memberColumns"
        :hideToggleDraft="true"
        :hideCreateBtn="true"
        :hideSearch="true"
        :disableSelect="true"
        :hideOpenBtn="true"
        :hideDeleteBtn="true"
        class="full-height"
      >
        <template #body-cell-actions="props">
          <div class="row justify-center q-gutter-x-sm">
            <q-btn
              icon="edit"
              round
              flat
              size="sm"
              color="primary"
              @click="
                selectedMember = props.row;
                showEditParamDialog = true;
              "
            >
              <q-tooltip>Edit Permissions</q-tooltip>
            </q-btn>
            <q-btn
              icon="person_remove"
              round
              flat
              size="sm"
              color="negative"
              @click="
                selectedMember = props.row;
                showDeleteDialog = true;
              "
            >
              <q-tooltip>Remove User</q-tooltip>
            </q-btn>
          </div>
        </template>
      </TableComponent>
    </fieldset>
  </div>
</template>

<script setup>
import { ref, inject, computed } from "vue";
import { useLoginStore } from "@/stores/LoginStore";
import PageTitle from "@/components/PageTitle.vue";
import TableComponent from "@/components/table/TableComponent.vue";

const isMobile = inject("isMobile");
const store = useLoginStore();

const name = ref("");
const searchQuery = ref("");
const searchResults = ref([]);

// Validation
const requiredRule = (val) =>
  (val && val.length > 0) || "This field is required";

// Table Configuration
const memberColumns = computed(() => [
  {
    name: "name",
    label: "User Name",
    align: "left",
    field: "name",
    styleType: "resource-name", 
    includeIcon: false, 
    conceptType: "user", 
  },
  {
    name: "read",
    label: "Read",
    field: "read",
    align: "center",
  },
  {
    name: "write",
    label: "Write",
    field: "write",
    align: "center",
  },
  {
    name: "shareRead",
    label: "Share Read",
    field: "shareRead",
    align: "center",
    style: "width: 100px",
  },
  {
    name: "shareWrite",
    label: "Share Write",
    field: "shareWrite",
    align: "center",
    style: "width: 100px",
  },
  {
    name: "admin",
    label: "Admin",
    field: "admin",
    align: "center",
  },
  {
    name: "owner",
    label: "Owner",
    field: "owner",
    align: "center",
  },
  {
    name: "actions",
    label: "Actions",
    align: "center",
    style: "width: 100px",
  },
]);


function performSearch() {
  if (!searchQuery.value) return;
  searchResults.value = ["Henry", "Bob", "Joe", "Larry", "John", "Dan"].filter(
    (u) => u.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
}

const selectedMember = ref(null);
const showDeleteDialog = ref(false);
const showEditParamDialog = ref(false);
</script>

<style scoped>
.field-label {
  font-size: 14px;
  color: #546e7a; 
}
</style>
