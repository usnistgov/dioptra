<template>
  <PageTitle
    title="Group Admin"
    resourceType="group"
  />

  <q-banner
    rounded
    class="bg-orange-2 text-dark q-mt-md"
  >
    Warning: All users can read and write resources in every group as permissions are not yet implemented.
  </q-banner>

  <div
    v-if="group"
    class="row q-col-gutter-xl q-mt-lg"
  >
    <div class="col-12 col-md-5">
      <fieldset class="q-pa-lg">
        <legend>Group Details</legend>
        <q-list separator>
          <q-item>
            <q-item-section>
              <q-item-label caption>ID</q-item-label>
              <q-item-label>{{ group.id }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label caption>Name</q-item-label>
              <q-item-label>{{ qualifiedName }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label caption>Creator</q-item-label>
              <q-item-label>{{ group.user.username }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label caption>Public</q-item-label>
              <q-item-label>{{ group.public ? "Yes" : "No" }}</q-item-label>
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label caption>Your Role</q-item-label>
              <q-item-label>{{ currentUserRole }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </fieldset>

      <fieldset class="q-pa-lg q-mt-lg">
        <legend>Group Management</legend>
        <q-form
          ref="renameForm"
          @submit="renameGroup"
        >
          <div class="row items-start q-col-gutter-md">
            <div class="col">
              <q-input
                v-model.trim="name"
                outlined
                dense
                label="Group Name"
                :disable="!isOwner"
                :rules="[requiredRule]"
                aria-required="true"
              />
            </div>
            <div class="col-auto">
              <q-btn
                label="Save Name"
                :color="isOwner ? 'primary' : 'grey-5'"
                :disable="!isOwner || !nameChanged"
                type="submit"
              />
            </div>
          </div>
        </q-form>

        <q-separator class="q-my-lg" />

        <q-list bordered>
          <q-item>
            <q-item-section>
              <q-item-label class="text-bold">Delete Group</q-item-label>
              <q-item-label caption>
                Deletion cannot be undone. All resources in this group will also be deleted. You cannot delete your
                final owned group.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                label="Delete Group"
                :color="isOwner ? 'negative' : 'grey-5'"
                :disable="!isOwner"
                @click="showDeleteDialog = true"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </fieldset>
    </div>

    <div class="col-12 col-md-7">
      <fieldset class="q-pa-lg q-mb-lg">
        <legend>Group Managers</legend>
        <BasicTable
          :columns="managerColumns"
          :rows="managerRows"
          :hideEditTable="true"
          :hideDelete="true"
          title="Managers"
        />
      </fieldset>

      <fieldset class="q-pa-lg">
        <legend>Group Members</legend>
        <BasicTable
          :columns="memberColumns"
          :rows="memberRows"
          :hideEditTable="true"
          :hideDelete="true"
          title="Members"
        />
      </fieldset>
    </div>
  </div>

  <div
    v-else
    class="row justify-center q-pa-xl"
  >
    <q-spinner
      color="primary"
      size="3em"
    />
  </div>

  <DeleteDialog
    v-model="showDeleteDialog"
    type="Group"
    :name="qualifiedName"
    @submit="deleteGroup"
  />
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import BasicTable from "@/components/BasicTable.vue";
import DeleteDialog from "@/dialogs/DeleteDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import * as notify from "@/notify";
import * as api from "@/services/dataApi";
import { useLoginStore } from "@/stores/LoginStore";

const route = useRoute();
const router = useRouter();
const store = useLoginStore();

const group = ref(null);
const name = ref("");
const originalName = ref("");
const renameForm = ref(null);
const showDeleteDialog = ref(false);

const requiredRule = (value) => (value && value.length > 0) || "This field is required";

const currentMember = computed(() =>
  group.value?.members.find((member) => Number(member.user.id) === Number(store.loggedInUser?.id)),
);
const isOwner = computed(() => currentMember.value?.permissions.owner ?? false);
const qualifiedName = computed(() => (group.value ? `${group.value.user.username}/${group.value.name}` : ""));
const nameChanged = computed(() => name.value.length > 0 && name.value !== originalName.value);
const currentUserRole = computed(() => {
  if (isOwner.value) return "Owner";
  if (currentMember.value?.permissions.admin) return "Admin";
  if (currentMember.value) return "Member";
  return "Public access";
});
const memberRows = computed(() =>
  (group.value?.members ?? []).map((member) => ({
    id: member.user.id,
    name: member.user.username,
    read: member.permissions.read,
    write: member.permissions.write,
    admin: member.permissions.admin,
    owner: member.permissions.owner,
  })),
);
const managerRows = computed(() => memberRows.value.filter((member) => member.admin || member.owner));

const managerColumns = [
  { name: "name", label: "Name", align: "left", field: "name", sortable: true },
  { name: "admin", label: "Admin", align: "left", field: "admin", sortable: true },
  { name: "owner", label: "Owner", align: "left", field: "owner", sortable: true },
];

const memberColumns = [
  { name: "name", label: "Name", align: "left", field: "name", sortable: true },
  { name: "read", label: "Read", align: "left", field: "read", sortable: true },
  { name: "write", label: "Write", align: "left", field: "write", sortable: true },
  { name: "admin", label: "Admin", align: "left", field: "admin", sortable: true },
  { name: "owner", label: "Owner", align: "left", field: "owner", sortable: true },
];

async function loadGroup(id) {
  const groupId = Number(id);
  if (!Number.isInteger(groupId)) {
    notify.error(`Invalid group ID: ${id}`);
    router.replace("/groups");
    return;
  }

  group.value = null;
  try {
    const response = await api.getItem("groups", groupId);
    group.value = response.data;
    name.value = response.data.name;
    originalName.value = response.data.name;
  } catch (error) {
    notify.error(error.response?.data?.message || "Failed to load group");
    router.replace("/groups");
  }
}

async function refreshLoginState() {
  const response = await api.getLoginStatus();
  store.loggedInUser = response.data;
  store.setGroups(response.data.groups);
}

async function renameGroup() {
  if (!isOwner.value || !nameChanged.value) return;

  const valid = await renameForm.value?.validate();
  if (!valid) return;

  try {
    const response = await api.updateItem("groups", group.value.id, { name: name.value });
    group.value = response.data;
    name.value = response.data.name;
    originalName.value = response.data.name;
    await refreshLoginState();
    notify.success(`Successfully renamed group to '${qualifiedName.value}'`);
  } catch (error) {
    notify.error(error.response?.data?.message || "Failed to rename group");
  }
}

async function deleteGroup() {
  if (!isOwner.value) return;

  try {
    const deletedName = qualifiedName.value;
    await api.deleteItem("groups", group.value.id);
    await refreshLoginState();
    showDeleteDialog.value = false;
    notify.success(`Successfully deleted '${deletedName}'`);
    router.push("/groups");
  } catch (error) {
    notify.error(error.response?.data?.message || "Failed to delete group");
  }
}

watch(
  () => route.params.id,
  (id) => loadGroup(id),
  { immediate: true },
);
</script>
