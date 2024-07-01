import axios from 'axios'

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
  }
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
    entrypoints: any
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
  }
}

interface Pagination {
  rowsPerPage: number,
  index: number,
  sortBy: string,
  descending: boolean,
  search: string,
}

export async function getData<T extends ItemType>(type: T, pagination: Pagination, showDrafts: boolean) {
  const res = await axios.get(`/api/${type}/${showDrafts ? 'drafts/' : ''}`, {
    params: {
      index: pagination.index,
      pageLength: pagination.rowsPerPage,
      // search: pagination.search,
      search: urlEncode(pagination.search),
      //search: pagination.search ? `"${pagination.search}"` : ''
      draftType: showDrafts ? 'new' : ''
    },
    // paramsSerializer: {
    //   encode: (param) => encodeURIComponent(param).replaceAll("+", "%20"),
    // },
  })
  if(showDrafts && res.data.data) {
    res.data.data.forEach((obj: any) => {
      Object.assign(obj, obj.payload)
    })
  }
  console.log('getData = ', res)
  return res
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

export async function addItem<T extends ItemType>(type: T, params: CreateParams[T]) {
  return await axios.post(`/api/${type}/`, params)
}

export async function addDraft<T extends ItemType>(type: T, params: CreateParams[T], id: number) {
  if(id) {
    return await axios.post(`/api/${type}/${id}/draft`, params)
  } else {
    return await axios.post(`/api/${type}/drafts/`, params)
  }
}

export async function updateDraft<T extends ItemType>(type: T, draftId: string, params: UpdateParams[T]) {
  return await axios.put(`/api/${type}/drafts/${draftId}`, params)
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

export async function updateTags<T extends ItemType>(type: T, id: number, tagIDs: Array<number>) {
  return await axios.put(`/api/${type}/${id}/tags`, { ids: tagIDs })
}