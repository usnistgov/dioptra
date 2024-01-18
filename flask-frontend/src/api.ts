import axios from 'axios';
import { useLoginStore } from './stores/LoginStore';

axios.interceptors.request.use(config => {
  const authStore = useLoginStore();
  if(authStore.oktaToken) {
    config.headers['Authorization'] = `Bearer ${authStore.oktaToken}`
  }
  return config;
}, function(error) {
  console.log('error = ', error)
  return Promise.reject(error)
})

export async function getLoginStatus() {
  const res = await axios.get('/api/world/');
  return res;
}

export async function login(username: string, password: string) {
  const res = await axios.post('/api/auth/login', {
    username: username,
    password: password
  });
  return res;
}

export async function logout(everywhere: boolean = false) {
  const res = await axios.post(`/api/auth/logout?everywhere=${everywhere}`);
  return res;
}

export async function registerUser(name: string, password: string, confirmPassword: string) {
  const res = await axios.post('/api/user/', {
    name: name,
    password: password,
    confirmPassword: confirmPassword
  });
  return res;
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const res = await axios.post('/api/user/password', {
    currentPassword: currentPassword,
    newPassword: newPassword
  });
  return res;
}

export async function deleteUser(password: string) {
  const res = await axios.delete('/api/user/', {
    data: { password: password }
  });
  return res;
}

// this is for endpoints that don't have any parameters
// simply pass the method (get, put, post) and the endpoint url
export async function genericCall(method: string, url: string) {
  const res = await axios({ method, url });
  return res;
}