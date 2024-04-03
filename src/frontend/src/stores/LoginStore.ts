import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLoginStore = defineStore('login', () => {
  // ref()'s are state properties
  const loggedInUser = ref('');
  const loggedInGroup = ref('')

  const groups = ref([
    { name: 'Group 1', id: '1', read: false, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Group 2', id: '2', read: true, write: true, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Group 3', id: '3', read: true, write: false, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Group 4', id: '4', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Group 5', id: '5', read: false, write: false, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Group 6', id: '6', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
  ])

  const users = ref([
    { name: 'Henry', id: '1', read: false, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Olivia', id: '2', read: false, write: false, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Emma', id: '3', read: false, write: false, shareRead: false, shareWrite: false, admin: true, owner: true },
    { name: 'Ava', id: '4', read: true, write: false, shareRead: false, shareWrite: true, admin: false, owner: true },
    { name: 'Sophia', id: '5', read: true, write: true, shareRead: false, shareWrite: true, admin: true, owner: false },
    { name: 'Isabella', id: '6', read: false, write: true, shareRead: false, shareWrite: false, admin: true, owner: true },
    { name: 'Charlotte', id: '7', read: false, write: true, shareRead: false, shareWrite: true, admin: true, owner: true },
    { name: 'Amelia', id: '8', read: false, write: false, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Mia', id: '9', read: true, write: true, shareRead: false, shareWrite: false, admin: true, owner: true },
    { name: 'Harper', id: '10', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: false },
    { name: 'Evelyn', id: '11', read: false, write: false, shareRead: false, shareWrite: true, admin: false, owner: false },
    { name: 'Abigail', id: '12', read: true, write: false, shareRead: false, shareWrite: true, admin: false, owner: true },
    { name: 'Emily', id: '13', read: false, write: false, shareRead: true, shareWrite: false, admin: true, owner: true },
    { name: 'Ella', id: '14', read: false, write: true, shareRead: false, shareWrite: false, admin: false, owner: true },
    { name: 'Elizabeth', id: '15', read: false, write: true, shareRead: true, shareWrite: true, admin: false, owner: true },
    { name: 'Camila', id: '16', read: true, write: false, shareRead: true, shareWrite: true, admin: false, owner: false },
    { name: 'Luna', id: '17', read: false, write: false, shareRead: false, shareWrite: false, admin: true, owner: true },
    { name: 'Sofia', id: '18', read: true, write: false, shareRead: true, shareWrite: false, admin: false, owner: true },
    { name: 'Avery', id: '19', read: true, write: true, shareRead: true, shareWrite: false, admin: true, owner: true },
    { name: 'Mila', id: '20', read: true, write: false, shareRead: true, shareWrite: true, admin: false, owner: true }
  ])
  

  // computed()'s are getters

  // function()'s are actions
  

  return { loggedInUser, loggedInGroup, groups, users };
})