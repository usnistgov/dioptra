import { expect, test } from "@playwright/test";

import { createEntrypoint, createQueue } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

test("create entrypoint", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  await createEntrypoint(page, entrypointName, queueName);
});

test("edit entrypoint", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;
  const updatedEntrypointName = `${entrypointName}_update`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  const createdEntrypoint = await createEntrypoint(page, entrypointName, queueName);

  await page.goto(`/entrypoints/${createdEntrypoint.id}`);
  await page.getByRole("heading", { name: entrypointName }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(updatedEntrypointName);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedEntrypointName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/entrypoints$/);
});

test("delete entrypoint", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  const createdEntrypoint = await createEntrypoint(page, entrypointName, queueName);

  await page.goto(`/entrypoints/${createdEntrypoint.id}`);
  await page.getByRole("heading", { name: entrypointName }).waitFor();
  await page.getByRole("button", { name: "Delete Entrypoint" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${entrypointName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/entrypoints$/);
});
