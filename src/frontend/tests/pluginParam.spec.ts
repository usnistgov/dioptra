import { expect, Page, test } from "@playwright/test";

import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

async function createPluginParam(page: Page, pluginParamName: string) {
  await page.goto("/pluginParams/new");

  await page.getByRole("heading", { name: "Create Plugin Parameter" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(pluginParamName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");
  await page.locator(".cm-content").first().click();
  await page.keyboard.insertText("{}");

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/pluginParameterTypes") && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}`,
  ).toBe(true);
  const createdPluginParam = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${pluginParamName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/pluginParams$/);

  return createdPluginParam;
}

test("create pluginParam", async ({ page }) => {
  const pluginParamName = `e2e_plugin_param_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await createPluginParam(page, pluginParamName);
});

test("edit pluginParam", async ({ page }) => {
  const pluginParamName = `e2e_plugin_param_${Date.now()}`;
  const updatedPluginParamName = `${pluginParamName}_update`;

  await ensureLoggedInAsTestUser(page);
  const createdPluginParam = await createPluginParam(page, pluginParamName);

  await page.goto(`/pluginParams/${createdPluginParam.id}`);
  await page.getByRole("heading", { name: pluginParamName }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(updatedPluginParamName);
  await page.getByRole("button", { name: "Submit" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedPluginParamName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/pluginParams$/);
});

test("delete pluginParam", async ({ page }) => {
  const pluginParamName = `e2e_plugin_param_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  const createdPluginParam = await createPluginParam(page, pluginParamName);

  await page.goto(`/pluginParams/${createdPluginParam.id}`);
  await page.getByRole("heading", { name: pluginParamName }).waitFor();
  await page.getByRole("button", { name: "Delete Plugin Parameter" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${pluginParamName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/pluginParams$/);
});
