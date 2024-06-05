import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useLoginStore = defineStore('login', () => {
  // ref()'s are state properties
  const loggedInUser = ref({});

  const groups = ref([])

  const loggedInGroup = computed(() => {
    if(groups.value.length === 1) {
      return groups.value[0]
    }
    return ''
  })


  const users = ref([
    { name: 'Tatum', id: '1', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Jaylen', id: '2', read: false, write: false, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Kristaps', id: '3', read: false, write: false, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Jrue', id: '4', read: true, write: false, shareRead: false, shareWrite: true, admin: false, owner: false },
    { name: 'Derrick', id: '5', read: true, write: true, shareRead: false, shareWrite: true, admin: false, owner: false },
    { name: 'Payton', id: '6', read: false, write: true, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Sam', id: '7', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Al', id: '8', read: false, write: false, shareRead: true, shareWrite: true, admin: false, owner: false },
    { name: 'Luke', id: '9', read: true, write: true, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Paul', id: '10', read: true, write: true, shareRead: true, shareWrite: true, admin: false, owner: false },
    { name: 'Kevin', id: '11', read: false, write: false, shareRead: false, shareWrite: true, admin: false, owner: false },
    { name: 'Ray', id: '12', read: true, write: false, shareRead: false, shareWrite: true, admin: false, owner: false },
    { name: 'Antoine', id: '13', read: false, write: false, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Marcus', id: '14', read: false, write: true, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Larry', id: '15', read: true, write: true, shareRead: true, shareWrite: true, admin: true, owner: true },
    { name: 'Isiah', id: '16', read: true, write: false, shareRead: true, shareWrite: true, admin: false, owner: false },
    { name: 'Rajon', id: '17', read: false, write: false, shareRead: false, shareWrite: false, admin: false, owner: false },
    { name: 'Sofia', id: '18', read: true, write: false, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Avery', id: '19', read: true, write: true, shareRead: true, shareWrite: false, admin: false, owner: false },
    { name: 'Mila', id: '20', read: true, write: false, shareRead: true, shareWrite: true, admin: false, owner: false }
  ])
  
  

  // computed()'s are getters

  // function()'s are actions
  

  return { loggedInUser, loggedInGroup, groups, users, };
})