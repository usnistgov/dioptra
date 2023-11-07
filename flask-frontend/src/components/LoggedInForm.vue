<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Logged In</div>
        <div>You are currently logged in as <span class="text-weight-bold text-primary">{{ loggedInUser }}</span></div>
    </q-card-section>
    <q-form @submit="$emit('submit', `api/auth/logout?everywhere=${allDevices}`, 'POST')" class="row flex-center">
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
      <q-form @submit="$emit('submit', 'api/user/password', 'POST')">
        <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
          <div>
            To change your password, enter your current and new password.
          </div>
          <q-input
            class="q-py-sm"
            outlined
            label="Current Password"
            :rules="[requiredRule]"
            :model-value="password"
            @update:model-value="newValue => $emit('update:password', newValue)"
          >
          </q-input>
          <q-input
            class="q-py-lg"
            outlined
            label="New Password"
            :rules="[requiredRule]"
            :model-value="newPassword"
            @update:model-value="newValue => $emit('update:newPassword', newValue)"
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
      <q-form @submit="$emit('submit', 'api/user/', 'DELETE')">
        <q-card-section class="text-center shadow-2 q-mt-sm q-mb-sm">
          <div>
            To delete your account, enter your password and press the delete button.
          </div>
          <q-input
            class="q-py-lg"
            outlined
            label="Password"
            :rules="[requiredRule]"
            :model-value="deleteRequestPassword"
            @update:model-value="newValue => $emit('update:deleteRequestPassword', newValue)"
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
  import { useLoginStore } from '@/stores/LoginStore'
  import { storeToRefs } from 'pinia'

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  defineProps(['username', 'password', 'newPassword', 'deleteRequestPassword'])
  defineEmits(['update:username', 'update:password', 'update:newPassword', 'update:deleteRequestPassword', 'submit'])

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";

  const allDevices = ref(false);

</script>