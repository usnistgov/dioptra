import { expect, test } from "@playwright/test";

import { createPlugin, createPluginFile } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

test("create pluginFile", async ({ page }) => {
  const timestamp = Date.now();
  const pluginName = `e2e_plugin_${timestamp}`;
  const filename = `e2e_plugin_file_${timestamp}.py`;

  await ensureLoggedInAsTestUser(page);
  const createdPlugin = await createPlugin(page, pluginName);
  await createPluginFile(page, createdPlugin.id, filename);
});

test("edit pluginFile", async ({ page }) => {
  const timestamp = Date.now();
  const pluginName = `e2e_plugin_${timestamp}`;
  const filenameBase = `e2e_plugin_file_${timestamp}`;
  const filename = `${filenameBase}.py`;
  const updatedFilename = `${filenameBase}_update.py`;

  await ensureLoggedInAsTestUser(page);
  const createdPlugin = await createPlugin(page, pluginName);
  const createdPluginFile = await createPluginFile(page, createdPlugin.id, filename);

  await page.goto(`/plugins/${createdPlugin.id}/files/${createdPluginFile.id}`);
  await page.getByRole("heading", { name: filename }).waitFor();
  await page.getByRole("textbox", { name: "Filename:" }).fill(updatedFilename);
  await page.getByRole("button", { name: "Submit File" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedFilename}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/plugins/${createdPlugin.id}$`));
});

test("delete pluginFile", async ({ page }) => {
  const timestamp = Date.now();
  const pluginName = `e2e_plugin_${timestamp}`;
  const filename = `e2e_plugin_file_${timestamp}.py`;

  await ensureLoggedInAsTestUser(page);
  const createdPlugin = await createPlugin(page, pluginName);
  const createdPluginFile = await createPluginFile(page, createdPlugin.id, filename);

  await page.goto(`/plugins/${createdPlugin.id}/files/${createdPluginFile.id}`);
  await page.getByRole("heading", { name: filename }).waitFor();
  await page.getByRole("button", { name: "Delete Plugin File" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${filename}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/plugins/${createdPlugin.id}$`));
});
