import { expect, Page } from "@playwright/test";

const runId = Date.now();

export const testUser = {
  username: `e2e_user_${runId}`,
  email: `e2e_user_${runId}@example.com`,
  password: "Password123!",
};

export async function loginAsTestUser(page: Page): Promise<boolean> {
  await page.goto("/login");

  const alreadyLoggedIn = await page
    .getByText(`You are currently logged in as ${testUser.username}`)
    .isVisible({ timeout: 3_000 })
    .catch(() => false);

  if (alreadyLoggedIn) {
    return true;
  }

  await page.getByRole("textbox", { name: "Username" }).fill(testUser.username);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(testUser.password);
  await page.getByRole("button", { name: "Login" }).click();

  try {
    await expect(
      page.getByRole("alert").filter({
        hasText: `Login successful for ${testUser.username}`,
      }),
    ).toBeVisible({ timeout: 3_000 });
    return true;
  } catch {
    return false;
  }
}

export async function registerTestUser(page: Page) {
  await page.goto("/register");

  await page.getByRole("textbox", { name: "Username" }).fill(testUser.username);
  await page.getByRole("textbox", { name: "Email Address" }).fill(testUser.email);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(testUser.password);
  await page.getByRole("textbox", { name: "Confirm Password" }).fill(testUser.password);
  await page.getByRole("button", { name: "Register" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created user '${testUser.username}'`,
    }),
  ).toBeVisible();
  await page.waitForURL(/\/login$/);
}

export async function ensureLoggedInAsTestUser(page: Page) {
  if (await loginAsTestUser(page)) {
    return;
  }

  await registerTestUser(page);

  const loggedIn = await loginAsTestUser(page);
  expect(loggedIn).toBe(true);
}
