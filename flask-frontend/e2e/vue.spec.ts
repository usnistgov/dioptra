import { test, expect } from '@playwright/test';

test('login and logout', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(page.getByText('Login').nth(2)).toHaveText('Login');
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Password').click();
  await page.getByLabel('Password').fill('test');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.getByText('Logged In', { exact: true })).toHaveText('Logged In');
  await expect(page.getByText('You are currently logged in as testuser')).toHaveText('You are currently logged in as testuser');
  await expect(page.getByRole('button', { name: 'Log Out' })).toBeVisible()
  await page.getByRole('button', { name: 'Log Out' }).click();
  await expect(page.getByText('Login').nth(2)).toHaveText('Login');
});

test('change password', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Username').press('Tab');
  await page.getByLabel('Password').fill('test');
  await page.getByLabel('Password').press('Enter');
  await page.getByLabel('Expand "Change Password"').click();
  await expect(page.getByText('To change your password, enter your current and new password.')).toBeVisible()
  await page.getByLabel('Current Password').click();
  await page.getByLabel('Current Password').fill('test');
  await page.getByLabel('New Password').click();
  await page.getByLabel('New Password').fill('test1');
  await page.getByRole('button', { name: 'Change Password', exact: true }).click();
  await expect(page.getByText('Successfully changed password for user: testuser')).toBeVisible()
  await expect(page.getByText('Login').nth(2)).toHaveText('Login');

  // change password back to test
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Username').press('Tab');
  await page.getByLabel('Password').fill('test1');
  await page.getByLabel('Password').press('Enter');
  await page.getByLabel('Expand "Change Password"').click();
  await page.getByLabel('Current Password').click();
  await page.getByLabel('Current Password').fill('test1');
  await page.getByLabel('New Password').click();
  await page.getByLabel('New Password').fill('test');
  await page.getByRole('button', { name: 'Change Password', exact: true }).click();
  await expect(page.getByText('Login').nth(2)).toHaveText('Login');
});

test('test endpoint', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Username').press('Tab');
  await page.getByLabel('Password').fill('test');
  await page.getByLabel('Password').press('Enter');
  await page.getByRole('tab', { name: 'API' }).click();
  await expect(page.getByRole('heading', { name: 'API' })).toBeVisible();
  await page.getByLabel('Expand "Test Endpoints"').click();
  await page.getByRole('button', { name: 'GET' }).click();
  await expect(page.getByText('Response Code:')).toBeVisible();
});

test('required field warnings', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.locator('div').filter({ hasText: /^This field is required$/ }).first()).toBeVisible();
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testuser');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page.locator('div').filter({ hasText: /^This field is required$/ }).first()).toBeVisible();
  await page.getByLabel('Password').click();
  await page.getByLabel('Password').fill('test');
  await page.getByLabel('Password').press('Enter');
  await page.getByLabel('Expand "Change Password"').click();
  await page.getByRole('button', { name: 'Change Password', exact: true }).click();
  await expect(page.locator('div').filter({ hasText: /^This field is required$/ }).first()).toBeVisible();
  await page.getByLabel('Current Password').click();
  await page.getByLabel('Current Password').fill('test');
  await page.getByRole('button', { name: 'Change Password', exact: true }).click();
  await expect(page.locator('div').filter({ hasText: /^This field is required$/ }).first()).toBeVisible();
  await page.getByLabel('New Password').click();
  await page.getByLabel('New Password').fill('test');
  await page.getByLabel('Collapse "Change Password"').click();
  await page.getByLabel('Expand "Delete Account"').click();
  await page.getByRole('button', { name: 'Delete User' }).click();
  await expect(page.locator('div').filter({ hasText: /^This field is required$/ }).first()).toBeVisible();
});

test('create and delete user', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByRole('button', { name: 'Signup.' }).click();
  await expect(page.getByText('Register a new user account')).toBeVisible();
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testdeletion');
  await page.getByLabel('Username').press('Tab');
  await page.getByLabel('Password', { exact: true }).fill('test');
  await page.getByLabel('Confirm Password').click();
  await page.getByLabel('Confirm Password').fill('test');
  await page.getByLabel('Confirm Password').press('Enter');
  await page.getByLabel('Username').click();
  await page.getByLabel('Username').fill('testdeletion');
  await page.getByLabel('Username').press('Tab');
  await page.getByLabel('Password').fill('test');
  await page.getByLabel('Password').press('Enter');
  await page.getByLabel('Expand "Delete Account"').click();
  await expect(page.getByText('To delete your account, enter your password and press the delete button.')).toBeVisible();
  await page.getByLabel('Password', { exact: true }).click();
  await page.getByLabel('Password', { exact: true }).fill('test');
  await page.getByRole('button', { name: 'Delete User' }).click();
  await expect(page.getByText('Login').nth(2)).toHaveText('Login');
});