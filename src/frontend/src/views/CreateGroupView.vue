<template>
  <PageTitle
    title="Create Group"
    resourceType="group"
  />
  <q-banner
    rounded
    class="bg-orange-2 text-dark q-mt-md"
  >
    Warning: All users can read and write resources in every group as permissions are not yet implemented.
  </q-banner>
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }">
    <fieldset class="q-mt-lg">
      <legend>Basic Info</legend>
      <q-form
        ref="form"
        class="q-ma-lg"
        @submit="submit"
      >
        <q-input
          v-model.trim="name"
          outlined
          dense
          :rules="[requiredRule]"
          aria-required="true"
          class="q-mb-sm"
        >
          <template #before>
            <label class="field-label">Name:</label>
          </template>
        </q-input>
        <q-checkbox
          v-model="isPublic"
          label="Public"
          disable
          class="q-mb-sm"
        />
      </q-form>
    </fieldset>

    <div class="float-right q-mt-lg">
      <q-btn
        outline
        color="primary"
        label="Cancel"
        class="q-mr-lg cancel-btn"
        @click="router.push('/groups')"
      />
      <q-btn
        color="primary"
        label="Submit"
        @click="submit"
      />
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from "vue";
import { useRouter } from "vue-router";

import PageTitle from "@/components/PageTitle.vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import { useLoginStore } from "@/stores/LoginStore";

const router = useRouter();
const store = useLoginStore();
const isMobile = inject("isMobile");
const isMedium = inject("isMedium");

const form = ref();
const name = ref("");
const isPublic = ref(true);

const requiredRule = (val) => (val && val.length > 0) || "This field is required";

async function submit() {
  const valid = await form.value?.validate();
  if (!valid) {
    return;
  }

  try {
    const createResponse = await api.addItem("groups", { name: name.value, public: isPublic.value });
    const userInfoResponse = await api.getLoginStatus();
    store.loggedInUser = userInfoResponse.data;
    store.setGroups(userInfoResponse.data.groups);
    store.setLoggedInGroup(createResponse.data.id);
    notify.success("Group created");
    await router.push("/groups");
  } catch (err) {
    notify.error(err.response?.data?.message || "Failed to create group");
  }
}
</script>
