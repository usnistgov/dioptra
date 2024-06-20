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
    group: string,
    structure: object
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
      // search: pagination.search
      search: urlEncode(pagination.search)
      //search: pagination.search ? `"${pagination.search}"` : ''
    },
    // paramsSerializer: {
    //   encode: (param) => encodeURIComponent(param).replaceAll("+", "%20"),
    // },
  })
  if(showDrafts && res.data.data) {
    res.data.data.forEach((obj) => {
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

export async function getItem<T extends ItemType>(type: T, id: number) {
  return await axios.get(`/api/${type}/${id}`)
}

export async function updateItem<T extends ItemType>(type: T, id: number, params: UpdateParams[T]) {
  return await axios.put(`/api/${type}/${id}`, params)
}

export async function addItem<T extends ItemType>(type: T, params: CreateParams[T]) {
  return await axios.post(`/api/${type}/`, params)
}

export async function addDraft<T extends ItemType>(type: T, id: string, params: CreateParams[T]) {
  if(id) {
    return await axios.post(`/api/${type}/${id}/draft`, params)
  } else {
    return await axios.post(`/api/${type}/drafts/`, params)
  }
}

export async function deleteItem<T extends ItemType>(type: T, id: number) {
  return await axios.delete(`/api/${type}/${id}`)
}

export async function getFiles(id: number) {
  return await axios.get(`/api/plugins/${id}/files`)
}