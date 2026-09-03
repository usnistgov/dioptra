import { expect, test } from "@playwright/test";

import { createPlugin } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser, testUser } from "./helpers/testUserHelper";

test("create plugin", async ({ page }) => {
  const pluginName = `e2e_plugin_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await createPlugin(page, pluginName);
});

test("creates a plugin in the context selected after the form opens", async ({ page }) => {
  const groupName = `e2e_plugin_group_${Date.now()}`;
  const pluginName = `e2e_context_plugin_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  const userResponse = await page.request.get("/api/v1/users/current");
  expect(userResponse.ok()).toBe(true);
  const user = await userResponse.json();
  const originalGroup = user.groups.find(
    (group) => group.name === testUser.username && group.user.username === testUser.username,
  );
  expect(originalGroup).toBeTruthy();

  await page.goto("/groups/new");
  await page.getByRole("textbox", { name: "Name:" }).fill(groupName);
  const groupResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Submit" }).click();
  const groupResponse = await groupResponsePromise;
  expect(groupResponse.ok()).toBe(true);
  const group = await groupResponse.json();

  await page.goto("/plugins/new");
  await page.getByRole("textbox", { name: "Name:" }).fill(pluginName);
  await page.getByRole("button", { name: new RegExp(groupName) }).click();
  await page.locator(".q-menu:visible").getByText(originalGroup.name, { exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Group:" })).toHaveValue(originalGroup.name);

  const pluginResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/plugins/" && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Submit" }).click();
  const pluginResponse = await pluginResponsePromise;
  expect(pluginResponse.ok()).toBe(true);
  expect(pluginResponse.request().postDataJSON().group).toBe(originalGroup.id);
  const plugin = await pluginResponse.json();
  expect(plugin.group.id).toBe(originalGroup.id);

  expect((await page.request.delete(`/api/v1/plugins/${plugin.id}`)).ok()).toBe(true);
  expect((await page.request.delete(`/api/v1/groups/${group.id}`)).ok()).toBe(true);
});

test("edit plugin", async ({ page }) => {
  const pluginName = `e2e_plugin_${Date.now()}`;
  const updatedPluginName = `${pluginName}_update`;

  await ensureLoggedInAsTestUser(page);
  const createdPlugin = await createPlugin(page, pluginName);

  await page.goto(`/plugins/${createdPlugin.id}`);
  await page.getByRole("heading", { name: pluginName }).waitFor();
  await page.getByText(`Show "${pluginName}" Metadata`).click();

  await page.locator("tr").filter({ hasText: "Name" }).getByRole("button").click();
  await page.locator(".q-popup-edit input").fill(updatedPluginName);
  await page.keyboard.press("Enter");

  await page.getByRole("button", { name: "Save" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedPluginName}'`,
    }),
  ).toBeVisible();
});

test("delete plugin", async ({ page }) => {
  const pluginName = `e2e_plugin_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  const createdPlugin = await createPlugin(page, pluginName);

  await page.goto(`/plugins/${createdPlugin.id}`);
  await page.getByRole("heading", { name: pluginName }).waitFor();
  await page.getByRole("button", { name: "Delete Plugin" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${pluginName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/plugins$/);
});

test("does not restore another user's unsaved plugin form", async ({ page }) => {
  const unsavedPluginName = `unsaved_plugin_${Date.now()}`;
  const secondUser = {
    username: `e2e_second_user_${Date.now()}`,
    email: `e2e_second_user_${Date.now()}@example.com`,
    password: "Password123!",
  };

  await ensureLoggedInAsTestUser(page);
  await page.goto("/plugins/new");
  await page.getByRole("textbox", { name: "Name:" }).fill(unsavedPluginName);

  await page.locator('a[href="/login"]:visible').click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByRole("button", { name: "Log Out" }).click();
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();

  const registerResponse = await page.request.post("/api/v1/users", {
    data: {
      username: secondUser.username,
      email: secondUser.email,
      password: secondUser.password,
      confirmPassword: secondUser.password,
    },
  });
  expect(registerResponse.ok()).toBe(true);

  await page.getByRole("textbox", { name: "Username" }).fill(secondUser.username);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(secondUser.password);
  await page.getByRole("button", { name: "Login" }).click();
  await expect(
    page.getByRole("alert").filter({
      hasText: `Login successful for ${secondUser.username}`,
    }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Navigation Menu" }).click();
  await page.locator(".q-menu:visible").getByText("Plugins", { exact: true }).click();
  await page.getByRole("button", { name: "Create" }).click();
  await expect(page).toHaveURL(/\/plugins\/new$/);
  await expect(page.getByRole("heading", { name: "Load Unsaved Form?" })).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "Name:" })).toHaveValue("");
});
