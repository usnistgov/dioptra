<template>
  <q-card bordered class="q-pa-lg" style="min-width: 40%;">
    <q-card-section class="text-center">
        <h1 class="form-title" style="margin-top: 0; margin-bottom: 0;">Logged In</h1>
        <p>You are currently logged in as <span class="text-weight-bold text-primary">{{ loggedInUser.username }}</span></p>
        <p>
          Email: {{ loggedInUser.email }} <br>
          Password Expires: {{ 
            new Date(loggedInUser.passwordExpiresOn)
              .toLocaleString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) 
          }}
        </p>
    </q-card-section>
    <q-form @submit="callLogout()" class="row flex-center">
      <q-checkbox
        label="Log out from all devices"
        v-model="allDevices"
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
          <p>
            To change your password, enter your current and new password.
          </p>
          <q-input
            class="q-mb-sm"
            outlined
            label="Current Password"
            :type="showPassword ? 'text' : 'password'"
            :rules="[requiredRule]"
            v-model="password"
            aria-required="true"
          >
            <template v-slot:append>
              <q-icon
                :name="showPassword ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>
          <q-input
            class="q-mb-sm"
            outlined
            label="New Password"
            :type="showPassword ? 'text' : 'password'"
            :rules="[requiredRule]"
            v-model="newPassword"
            aria-required="true"
          >
            <template v-slot:append>
              <q-icon
                :name="showPassword ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
          </q-input>
          <q-input
            class="q-mb-sm"
            outlined
            label="Confirm New Password"
            :type="showPassword ? 'text' : 'password'"
            :rules="[requiredRule]"
            v-model="confirmNewPassword"
            aria-required="true"
          >
            <template v-slot:append>
              <q-icon
                :name="showPassword ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="showPassword = !showPassword"
              />
            </template>
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
          <p>
            To delete your account, enter your password and press the delete button.
          </p>
          <q-input
            class="q-py-lg"
            outlined
            label="Password"
            :type="showDeletePassword ? 'text' : 'password'"
            :rules="[requiredRule]"
            v-model="deleteRequestPassword"
            aria-required="true"
          >
            <template v-slot:append>
              <q-icon
                :name="showDeletePassword ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="showDeletePassword = !showDeletePassword"
              />
            </template>
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

<script setup>
  import { ref } from 'vue';
  import { useLoginStore } from '@/stores/LoginStore';
  import { storeToRefs } from 'pinia';
  import * as api from '@/services/dataApi';
  import * as notify from '../notify';

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";

  const password = ref('');
  const newPassword = ref('');
  const confirmNewPassword = ref('');
  const deleteRequestPassword = ref('');
  const showPassword = ref(false);
  const showDeletePassword = ref(false);

  const allDevices = ref(false);

  async function callLogout() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value.username));
    try {
      await api.logout(allDevices.value);
      loggedInUser.value = '';
      notify.success(`Successfully logged out from ${previousUser}`);
    } catch (err) {
      notify.error(`Error logging out from user: ${previousUser}`);
    }
  }

  async function callChangePassword() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value.username));
    try {
      const res = await api.changePassword(password.value, newPassword.value, confirmNewPassword.value);
      loggedInUser.value = '';
      notify.success(`${res.data.status} for user: ${previousUser}`);
    } catch(err) {
      notify.error(err.response.data.message);
    }
  }

  async function callDeleteUser() {
    const previousUser = JSON.parse(JSON.stringify(loggedInUser.value));
    try {
      const res = await api.deleteUser(deleteRequestPassword.value);
      console.log('delete user res = ', res)
      loggedInUser.value = '';
      notify.success(`Successfully deleted user '${previousUser}'`);
    } catch(err) {
      console.log('delete user err = ', err)
      notify.error(err);
    }
  }

  const timeOptions = { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric', 
    hour: 'numeric', 
    minute: 'numeric', 
    second: 'numeric', 
    hour12: true, 
    timeZoneName: 'short' 
  }

</script>