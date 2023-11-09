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
  const { loggedInUser, formState, pauseLoginCheck } = storeToRefs(store);

  watch(loggedInUser, async(newVal) => {
    formState.value = newVal ? 'loggedIn' : 'login';
  });

  onMounted(async () => {
    // login status should be checked every time page loads, but when checking immediately
    // after logging out via other page, endpoint can be wrong, so in those cases dont check
    if (pauseLoginCheck.value) {
      pauseLoginCheck.value = false;
      $q.loading.hide();
      return;
    };
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

