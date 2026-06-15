import { expect, Page } from "@playwright/test";

export async function createQueue(page: Page, queueName: string) {
  await page.goto("/queues/new");

  await page.getByRole("heading", { name: "Create Queue" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(queueName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/queues") && response.request().method() === "POST" && response.ok(),
  );

  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
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
  await page.goto("/entrypoints/new");

  await page.getByRole("heading", { name: "Create Entrypoint" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(entrypointName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const queueSelect = page.getByRole("combobox", { name: "Queues:" });
  await queueSelect.click();
  await queueSelect.fill(queueName);
  await page.getByRole("option", { name: queueName }).click();

  await page.locator(".cm-content").first().click();
  await page.keyboard.insertText("graph:\n");

  const createResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/entrypoints") && response.request().method() === "POST" && response.ok(),
  );

  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  const createResponse = await createResponsePromise;
  const createdEntrypoint = await createResponse.json();

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
    (response) => response.url().includes("/api/v1/plugins") && response.request().method() === "POST" && response.ok(),
  );

  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  const createdPlugin = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${pluginName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/plugins$/);

  return createdPlugin;
}
