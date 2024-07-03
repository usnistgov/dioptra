import axios from 'axios'

export async function getGroups() {
  const res = await axios.get('/api/groups/')
  return res
}

export async function getGroup(id: string) {
  const res = await axios.get(`/api/groups/${id}`)
  return res
}