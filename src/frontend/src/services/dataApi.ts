import axios from 'axios'

type ItemType = keyof CreateParams

type CreateParams = {
  plugins: {
    name: string,
    description: string,
    group: number
  },
  queues: {
    name: string,
    description: string,
    group: number
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
  const res = await axios.get(`/api/${type}/`, {
    params: {
      index: pagination.index,
      pageLength: pagination.rowsPerPage,
      search: pagination.search
    }
  })
  console.log('getData = ', res)
  return res
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