import axios from 'axios'

export const API_VERSION = 'v1'

axios.interceptors.request.use(function (config) {
  if (config.url) {
    config.url = config.url.replace('/api/', `/api/${API_VERSION}/`)
  }
  return config
})

type ItemType = keyof UpdateParams

type CreateParams = {
  plugins: {
    name: string,
    description: string,
    group: number,
  },
  queues: {
    name: string,
    description: string,
    group: number
  },
  experiments: {
    name: string,
    description: string,
    group: number,
    entrypoints: any,
    tags: any
  },
  pluginParameterTypes: {
    name: string,
    description: string,
    group: number,
    structure: object
  },
  tags: {
    name: string,
    group: number
  },
  files: {
    filename: string,
    contents: string,
    description: string,
    tasks: []
  },
  entrypoints: {
    name: string,
    description: string,
    taskGraph: string,
    parameters: EntrypointParameters[],
    queues: number[],
    plugins: number[]
  },
  models: {
    name: string,
    description: string,
    group: number,
  },
  artifacts: {
    description: string,
    group: number,
    job: number,
    uri: string,
  },
}

type UpdateParams = {
  plugins: {
    name: string,
    description: string,
  },
  queues: {
    name: string,
    description: string,
  },
  experiments: {
    name: string,
    description: string,
    entrypoints: number[]
  },
  tags: {
    name: string
  },
  pluginParameterTypes: {
    name: string,
    description: string,
    structure: object
  },
  files: {
    filename: string,
    contents: string,
    description: string,
    tasks: []
  },
  entrypoints: {
    name: string,
    description: string,
    taskGraph: string,
    parameters: EntrypointParameters[],
    queues: number[]
  },
  models: {
    name: string,
    description: string,
  },
  artifacts: {
    description: string,
  },
}

interface EntrypointParameters {
  name: string,
  defaultValue: string,
  parameterType: string
}

interface Pagination {
  rowsPerPage: number,
  index: number,
  sortBy: string,
  descending: boolean,
  search: string,
}

export async function getData<T extends ItemType>(type: T, pagination: Pagination, showDrafts: boolean = false) {
  const res = await axios.get(`/api/${type}/${showDrafts ? 'drafts/' : ''}`, {
    params: {
      index: pagination.index,
      pageLength: pagination.rowsPerPage,
      search: urlEncode(pagination.search),
      draftType: showDrafts ? 'new' : ''
    },
  })
  if(showDrafts && res.data.data) {
    res.data.data.forEach((obj: any) => {
      Object.assign(obj, obj.payload)
    })
  }
  console.log('getData = ', res)
  return res
}

export async function getJobs(id: number, pagination: Pagination) {
  return await axios.get(`/api/experiments/${id}/jobs`, {
    params: {
      index: pagination.index,
      pageLength: pagination.rowsPerPage,
      search: urlEncode(pagination.search),
    }
  })
}

function urlEncode(string: string) {
  if(!string.trim()) return ''
  if(string.includes(':')) {
    const words = string.split(':')
    console.log('words = ', words)
    return `${words[0]}:"${words[1]}"`
  } else {
    return `"${string}"`
  }
}

export async function getItem<T extends ItemType>(type: T, id: number, isDraft: boolean = false) {
  const res =  await axios.get(`/api/${type}/${id}${isDraft ? '/draft' : ''}`)
  if(isDraft && res.data) {
    console.log('res = ', res)
    Object.assign(res.data, res.data.payload)
  }
  return res
}

export async function getDraft<T extends ItemType>(type: T, id: number) {
  const res = await axios.get(`/api/${type}/${id}/draft`)
  return res
}

export async function updateItem<T extends ItemType>(type: T, id: number, params: UpdateParams[T]) {
  return await axios.put(`/api/${type}/${id}`, params)
}

export async function addItem<T extends keyof CreateParams>(type: T, params: CreateParams[T]) {
  return await axios.post(`/api/${type}/`, params)
}

interface JobParams {
  description: string,
  queue: number,
  entrypoint: number,
  values: object,
  timeout: string
}

export async function addJob(id: number, params: JobParams) {
  return await axios.post(`/api/experiments/${id}/jobs`, params)
}

export async function deleteJob(id: number, jobId: number) {
  return await axios.delete(`/api/experiments/${id}/jobs/${jobId}`)
}

export async function addDraft<T extends keyof CreateParams>(type: T, params: CreateParams[T], id: number) {
  if(id) {
    return await axios.post(`/api/${type}/${id}/draft`, params)
  } else {
    return await axios.post(`/api/${type}/drafts/`, params)
  }
}

export async function updateDraft<T extends ItemType>(type: T, draftId: string, params: UpdateParams[T]) {
  return await axios.put(`/api/${type}/drafts/${draftId}`, params)
}

export async function updateDraftLinkedtoQueue(queueId: number, name: string, description: string) {
  return await axios.put(`/api/queues/${queueId}/draft`, { name, description })
}

export async function deleteItem<T extends ItemType>(type: T, id: number) {
  return await axios.delete(`/api/${type}/${id}`)
}

export async function deleteDraft<T extends ItemType>(type: T, draftId: number) {
  return await axios.delete(`/api/${type}/drafts/${draftId}`)
}

export async function getFiles(id: number, pagination: Pagination) {
  return await axios.get(`/api/plugins/${id}/files`, {
    params: {
      index: pagination.index,
      pageLength: pagination.rowsPerPage,
      search: urlEncode(pagination.search)
    }
  })
}

export async function getFile(pluginID: string, fileID: string) {
  return await axios.get(`/api/plugins/${pluginID}/files/${fileID}`)
}

export async function addFile(id: number, params: CreateParams['files']){
  return await axios.post(`/api/plugins/${id}/files`, params)
}

export async function updateFile(id: number, fileID: string, params: CreateParams['files']){
  console.log('updateFile params = ', params)
  return await axios.put(`/api/plugins/${id}/files/${fileID}`, params)
}

export async function deleteFile(pluginID: string, fileID: string) {
  return await axios.delete(`/api/plugins/${pluginID}/files/${fileID}`)
}

export async function updateTags<T extends ItemType>(type: T, id: number, tagIDs: Array<number>, fileId?: number) {
  if(type === 'files') {
    return await axios.put(`/api/plugins/${id}/files/${fileId}/tags/`, { ids: tagIDs })
  }
  return await axios.put(`/api/${type}/${id}/tags`, { ids: tagIDs })
}

interface ArtifactParams {
  description: string,
  uri: string,
}

export async function addArtifact(expId: string, jobId: string, params: ArtifactParams) {
  return await axios.post(`/api/experiments/${expId}/jobs/${jobId}/artifacts`, params)
}

export async function addPluginsToEntrypoint(id: string, plugins: number[]) {
  return await axios.post(`/api/entrypoints/${id}/plugins`, {plugins})
}

export async function removePluginFromEntrypoint(entrypointId: string, pluginId: number) {
  return await axios.delete(`/api/entrypoints/${entrypointId}/plugins/${pluginId}`)
}

export async function getVersions(id: string,) {
  return await axios.get(`/api/models/${id}/versions`)
}


export async function getLoginStatus() {
  return await axios.get(`/api/users/current`)
}

export async function login(username: string, password: string) {
  return await axios.post(`/api/auth/login`, {
    username: username,
    password: password
  })
}

export async function logout(everywhere: boolean = false) {
  return await axios.post(`/api/auth/logout?everywhere=${everywhere}`);
}

export async function registerUser(username: string, email: string, password: string, confirmPassword: string) {
  return await axios.post(`/api/users`, {
    username: username,
    email: email,
    password: password,
    confirmPassword: confirmPassword
  })
}

export async function changePassword(oldPassword: string, newPassword: string, confirmNewPassword: string) {
  return await axios.post(`/api/users/current/password`, {
    oldPassword: oldPassword,
    newPassword: newPassword,
    confirmNewPassword: confirmNewPassword,
  })
}

export async function deleteUser(password: string) {
  return await axios.delete(`/api/users/current`, {
    data: { password: password }
  })
}