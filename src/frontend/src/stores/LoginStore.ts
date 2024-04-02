import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLoginStore = defineStore('login', () => {
  // ref()'s are state properties
  const loggedInUser = ref('');
  const loggedInGroup = ref('')

  const groups = ref([
    {name: 'Group 1', id: '1', read: false, write: true, shareRead: true, shareWrite: true, admin: true, owner: true},
    {name: 'Group 2', id: '2', read: true, write: true, shareRead: false, shareWrite: false, admin: false, owner: false},
    {name: 'Group 3', id: '3', read: true, write: false, shareRead: true, shareWrite: false, admin: false, owner: false},
    {name: 'Group 4', id: '4', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true},
    {name: 'Group 5', id: '5', read: false, write: false, shareRead: false, shareWrite: false, admin: false, owner: false},
    {name: 'Group 6', id: '6', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true},
  ])

  // computed()'s are getters

  // function()'s are actions
  

  return { loggedInUser, loggedInGroup, groups };
})