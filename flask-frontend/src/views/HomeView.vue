<template>
  <div class="flex flex-center q-mt-xl q-pt-xl">

    <LoginForm v-if="formState === 'login'" />

    <RegisterForm v-if="formState === 'register'" />

    <LoggedInForm v-if="formState === 'loggedIn'" />
    
  </div>
</template>

<script setup lang="ts">
  import { watch, onMounted  } from 'vue';
  import { useQuasar } from 'quasar';
  import { useLoginStore } from '@/stores/LoginStore.js';
  import { storeToRefs } from 'pinia';
  import LoginForm from '../components/LoginForm.vue';
  import RegisterForm from '../components/RegisterForm.vue';
  import LoggedInForm from '../components/LoggedInForm.vue';
  import * as api from '../api';

  const $q = useQuasar();

  $q.loading.show();

  const store = useLoginStore();
  const { loggedInUser, formState } = storeToRefs(store);

  watch(loggedInUser, async(newVal) => {
    formState.value = newVal ? 'loggedIn' : 'login';
  });

  onMounted(async () => {
    try {
      const res = await api.getLoginStatus();
      loggedInUser.value = res.data.name;
      formState.value = 'loggedIn';
    } catch(err) {
      loggedInUser.value = '';
      formState.value = 'login';
    } finally {
      $q.loading.hide();
    }
  });

</script>

