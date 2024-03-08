import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDataStore = defineStore('data', () => {
  // ref()'s are state properties
  const experiments = ref([]);

  // computed()'s are getters

  // function()'s are actions
  

  return { experiments };
})