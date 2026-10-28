import { expect, test } from "@playwright/test";

test("register without an email address", async ({ page }) => {
  await page.route("**/api/v1/users/current", (route) => route.fulfill({ status: 401, json: {} }));
  await page.route("**/api/v1/users", (route) => route.fulfill({ json: { id: 1, username: "new_user" } }));
  await page.goto("/register");

  await expect(page.getByRole("textbox", { name: "Email Address" })).toHaveCount(0);
  await page.getByRole("textbox", { name: "Username" }).fill("new_user");
  await page.getByRole("textbox", { name: "Password", exact: true }).fill("Password123!");
  await page.getByRole("textbox", { name: "Confirm Password" }).fill("Password123!");
  const requestPromise = page.waitForRequest(
    (request) => new URL(request.url()).pathname === "/api/v1/users" && request.method() === "POST",
  );
  await page.getByRole("button", { name: "Register", exact: true }).click();

  expect((await requestPromise).postDataJSON()).toEqual({
    username: "new_user",
    password: "Password123!",
    confirmPassword: "Password123!",
  });
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("alert").filter({ hasText: "Successfully created user 'new_user'" })).toBeVisible();
});
