import axios from 'axios';

export async function getQueues() {
  const res = await axios.get('/api/queues/');
  console.log('queues res = ', res)
  return res;
}

export async function registerQueue(name: string, groupId: number, description: string) {
  const res = await axios.post('/api/queues/', {
    name: name,
    group: groupId,
    description: description
  });
  return res;
}

export async function deleteQueue(id : number) {
  const res = await axios.delete(`/api/queues/${id}`);
  return res;
}

export async function upadateQueue(name: string, id: number, description: string) {
  const res = await axios.put(`/api/queues/${id}`, {
    name: name,
    description: description
  });
  return res;
}