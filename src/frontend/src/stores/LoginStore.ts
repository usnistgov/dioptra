import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLoginStore = defineStore('login', () => {
  // ref()'s are state properties
  const loggedInUser = ref('');

  // computed()'s are getters

  // function()'s are actions
  

  return { loggedInUser };
})