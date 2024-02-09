import axios from 'axios';

export async function getQueues() {
  const res = await axios.get('/api/queue/');
  return res;
}

export async function registerQueue(name: string) {
  const res = await axios.post('/api/queue/', {
    name: name
  });
  return res;
}

export async function deleteQueue(name : string) {
  const res = await axios.delete(`/api/queue/name/${name}`);
  return res;
}

export async function upadateQueue(name: string, queueId: number) {
  const res = await axios.put(`/api/queue/${queueId}`, {
    name: name
  });
  return res;
}