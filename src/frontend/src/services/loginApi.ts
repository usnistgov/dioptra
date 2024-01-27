import axios from 'axios';

export async function getLoginStatus() {
  const res = await axios.get('/api/user/current');
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

export async function registerUser(username: string, emailAddress: string, password: string, confirmPassword: string) {
  const res = await axios.post('/api/user/', {
    username: username,
    emailAddress: emailAddress,
    password: password,
    confirmPassword: confirmPassword
  });
  return res;
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const res = await axios.post('/api/user/current/password', {
    currentPassword: currentPassword,
    newPassword: newPassword
  });
  return res;
}

export async function deleteUser(password: string) {
  const res = await axios.delete('/api/user/current', {
    data: { password: password }
  });
  return res;
}