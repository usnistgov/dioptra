import axios from 'axios'

interface Plugin {
  name: string,
  description: string
}

export async function getPlugins() {
  const res = await axios.get('/api/plugins/')
  console.log('getPlugins = ', res)
  return res
}

export async function getPlugin(id: number) {
  const res = await axios.get(`/api/plugins/${id}`)
  return res
}

export async function updatePlugin(id: number, plugin: Plugin) {
  console.log('plugin = ', plugin)
  const res = await axios.put(`/api/plugins/${id}`, {
    name: plugin.name,
    description: plugin.description
  })
  return res
}

export async function addPlugin(name: string, groupId: number, description: string) {
  const res = await axios.post('/api/plugins/', {
    name: name,
    group: groupId,
    description: description
  });
  return res
}

export async function deletePlugin(id: number) {
  const res = await axios.delete(`/api/plugins/${id}`)
  return res
}

export async function getFiles(id: number) {
  const res = await axios.get(`/api/plugins/${id}/files`)
  console.log('getFiles = ', res)
  return res
}