import axios from 'axios';

export async function getLoginStatus() {
  const res = await axios.get('/api/users/current');
  console.log('res = ', res)
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

export async function registerUser(username: string, email: string, password: string, confirmPassword: string) {
  const res = await axios.post('/api/users', {
    username: username,
    email: email,
    password: password,
    confirmPassword: confirmPassword
  });
  return res;
}

export async function changePassword(oldPassword: string, newPassword: string, confirmNewPassword: string) {
  const res = await axios.post('/api/users/current/password', {
    oldPassword: oldPassword,
    newPassword: newPassword,
    confirmNewPassword: confirmNewPassword,
  });
  return res;
}

export async function deleteUser(password: string) {
  const res = await axios.delete('/api/users/current', {
    data: { password: password }
  });
  return res;
}