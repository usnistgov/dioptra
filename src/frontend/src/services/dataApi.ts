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
  }
}

interface Pagination {
  rowsPerPage: number,
  index: number,
  sortBy: string,
  descending: boolean,
  search: string,
}

export async function getData<T extends ItemType>(type: T, pagination: Pagination) {
  console.log('pagination = ', pagination)
  const res = await axios.get(`/api/${type}/`, {
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
  const res = await axios.get(`/api/${type}/${id}`)
  return res
}

export async function updateItem<T extends ItemType>(type: T, id: number, params: UpdateParams[T]) {
  const res = await axios.put(`/api/${type}/${id}`, params)
  return res
}

export async function addItem<T extends ItemType>(type: T, params: CreateParams[T]) {
  const res = await axios.post(`/api/${type}/`, params)
  return res
}

export async function deleteItem<T extends ItemType>(type: T, id: number) {
  const res = await axios.delete(`/api/${type}/${id}`)
  return res
}

export async function getFiles(id: number) {
  const res = await axios.get(`/api/plugins/${id}/files`)
  console.log('getFiles = ', res)
  return res
}