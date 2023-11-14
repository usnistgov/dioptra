<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Logged In</div>
        <div>You are currently logged in as <span class="text-weight-bold text-primary">{{ loggedInUser }}</span></div>
    </q-card-section>
    <q-form @submit="callLogout()" class="row flex-center">
      <q-checkbox
        label="Log out from all devices"
        v-model="allDevices"
        class="q-mt-md"
      />
      <q-btn
        color="orange"
        class="full-width "
        type="submit"
      >
        Log Out
      </q-btn>
    </q-form>
    <p class="text-body1 text-bold q-mt-xl">
      Additional User Account Actions
    </p>

    <q-expansion-item
      header-class="text-bold shadow-2"
      label="Change Password"
      group="somegroup"
    >
      <q-form @submit="callChangePassword()">
        <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
          <div>
            To change your password, enter your current and new password.
          </div>
          <q-input
            class="q-py-sm"
            outlined
            label="Current Password"
            :rules="[requiredRule]"
            v-model="password"
          >
          </q-input>
          <q-input
            class="q-py-lg"
            outlined
            label="New Password"
            :rules="[requiredRule]"
            v-model="newPassword"
          >
          </q-input>
          <q-btn
            color="primary"
            class="full-width "
            type="submit"
          >
            Change Password
          </q-btn>
        </q-card-section>
      </q-form>
    </q-expansion-item>
    <q-expansion-item
      header-class="text-bold shadow-2"
      label="Delete Account"
      group="somegroup"
    >
      <q-form @submit="callDeleteUser()">
        <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
          <div>
            To delete your account, enter your password and press the delete button.
          </div>
          <q-input
            class="q-py-lg"
            outlined
            label="Password"
            :rules="[requiredRule]"
            v-model="deleteRequestPassword"
          >
          </q-input>
          <q-btn
            color="red"
            class="full-width "
            type="submit"
          >
            Delete User
          </q-btn>
        </q-card-section>
      </q-form>
    </q-expansion-item>
  </q-card>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { useLoginStore } from '@/stores/LoginStore';
  import { storeToRefs } from 'pinia';
  import * as api from '../api';
  import * as notify from '../notify';

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";

  const password = ref('');
  const newPassword = ref('');
  const deleteRequestPassword = ref('');

  const allDevices = ref(false);

  async function callLogout() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value));
    try {
      await api.logout(allDevices.value);
      loggedInUser.value = '';
      notify.success(`Successfully logged out from ${previousUser}`);
    } catch (err) {
      notify.error(`Error logging out from user: ${previousUser}`);
    }
  }

  async function callChangePassword() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value));
    try {
      const res = await api.changePassword(password.value, newPassword.value);
      loggedInUser.value = '';
      notify.success(`${res.data.message} for user: ${previousUser}`);
    } catch(err: any) {
      notify.error(err.response.data.message);
    }
  }

  async function callDeleteUser() {
    try {
      const res = await api.deleteUser(deleteRequestPassword.value);
      loggedInUser.value = '';
      notify.success(res.data.message);
    } catch(err: any) {
      notify.error(err.response.data.message);
    }
  }

</script>