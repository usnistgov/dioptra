import { expect, test } from "@playwright/test";

import { createPlugin } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

test("create plugin", async ({ page }) => {
  const pluginName = `e2e_plugin_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await createPlugin(page, pluginName);
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
