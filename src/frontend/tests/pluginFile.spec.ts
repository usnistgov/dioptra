import { expect, Page, test } from "@playwright/test";

import { createPlugin } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

async function createPluginFile(page: Page, pluginId: number, filename: string) {
  await page.goto(`/plugins/${pluginId}/files/new`);

  await page.getByRole("heading", { name: "Create Plugin File" }).waitFor();
  await page.getByRole("textbox", { name: "Filename:" }).fill(filename);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");
  await page.locator(".cm-content").first().click();
  await page.keyboard.insertText("def e2e_task():\n    return None\n");

  const createResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/v1/plugins/${pluginId}/files`) && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit File" }).click();
  const createResponse = await createResponsePromise;
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}`,
  ).toBe(true);
  const createdPluginFile = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${filename}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/plugins/${pluginId}$`));

  return createdPluginFile;
}

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
