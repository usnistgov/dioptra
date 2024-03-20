<template>
  <div :class="`flex flex-center q-mt-xl ${isMobile ? '' : 'q-pt-xl' } `">

    <LoginForm v-if="!loggedInUser" />

    <LoggedInForm v-if="loggedInUser" />
    
  </div>
</template>

<script setup>
  import { useLoginStore } from '@/stores/LoginStore.ts';
  import { storeToRefs } from 'pinia';
  import LoginForm from '../components/LoginForm.vue';
  import LoggedInForm from '../components/LoggedInForm.vue';
  import { inject } from 'vue'

  const store = useLoginStore();
  const { loggedInUser } = storeToRefs(store);

  const isMobile = inject('isMobile')

</script>