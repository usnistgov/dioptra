import { expect, Page } from "@playwright/test";

export async function createQueue(page: Page, queueName: string) {
  await page.goto("/queues/new");

  await page.getByRole("heading", { name: "Create Queue" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(queueName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/queues") && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}`,
  ).toBe(true);
  const createdQueue = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${queueName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/queues$/);

  return createdQueue;
}

export async function createEntrypoint(page: Page, entrypointName: string, queueName: string) {
  const pluginName = `${entrypointName}_plugin`;
  const pluginFilename = `${entrypointName}_tasks.py`;
  const createdPlugin = await createPlugin(page, pluginName);
  await createPluginFile(page, createdPlugin.id, pluginFilename);

  await page.goto("/entrypoints/new");

  await page.getByRole("heading", { name: "Create Entrypoint" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(entrypointName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const queueSelect = page.getByRole("combobox", { name: "Queues:" });
  await queueSelect.click();
  await queueSelect.fill(queueName);
  await page.getByRole("option", { name: queueName }).click();

  const pluginSelect = page.getByRole("combobox", { name: "Plugins:" }).first();
  await pluginSelect.click();
  await pluginSelect.fill(pluginName);
  await page.getByRole("option", { name: pluginName }).click();

  await page.locator(".cm-content").first().click();
  await page.keyboard.insertText("e2e_step:\n  task: e2e_task\n");

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/entrypoints") && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  const createResponse = await createResponsePromise;
  const createdEntrypoint = await createResponse.json();
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}: ${JSON.stringify(createdEntrypoint)}`,
  ).toBe(true);

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${entrypointName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/entrypoints$/);

  return createdEntrypoint;
}

export async function createPlugin(page: Page, pluginName: string) {
  await page.goto("/plugins/new");

  await page.getByRole("heading", { name: "Create Plugin" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(pluginName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/plugins") && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}`,
  ).toBe(true);
  const createdPlugin = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${pluginName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/plugins$/);

  return createdPlugin;
}

export async function createPluginFile(page: Page, pluginId: number, filename: string) {
  await page.goto(`/plugins/${pluginId}/files/new`);

  await page.getByRole("heading", { name: "Create Plugin File" }).waitFor();
  await page.getByRole("textbox", { name: "Filename:" }).fill(filename);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");
  await page.locator(".cm-content").first().click();
  await page.keyboard.insertText(
    "from dioptra import pyplugs\n\n@pyplugs.register\ndef e2e_task() -> None:\n    return None\n",
  );

  await page.getByRole("button", { name: "Import Function Tasks" }).click();
  const importTasksDialog = page.getByRole("dialog");
  await expect(importTasksDialog.getByText("Import Plugin Function Tasks", { exact: true })).toBeVisible();
  await expect(importTasksDialog.getByText("e2e_task", { exact: true })).toBeVisible();
  await importTasksDialog.getByRole("button", { name: "Import", exact: true }).click();

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
