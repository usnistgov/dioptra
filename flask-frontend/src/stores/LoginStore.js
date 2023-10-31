import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLoginStore = defineStore('login', () => {
  // state properties
  const loggedInUser = ref('')
  // getters

  // actions (setters)

  return { loggedInUser }
})