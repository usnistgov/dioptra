import { expect, test } from "@playwright/test";

import { createQueue } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

test("create queue", async ({ page }) => {
  const queueName = `e2e_queue_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
});

test("edit queue", async ({ page }) => {
  const queueName = `e2e_queue_${Date.now()}`;
  const updatedQueueName = `${queueName}_update`;

  await ensureLoggedInAsTestUser(page);
  const createdQueue = await createQueue(page, queueName);

  await page.goto(`/queues/${createdQueue.id}`);
  await page.getByRole("heading", { name: queueName }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(updatedQueueName);
  await page.getByRole("button", { name: "Submit" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedQueueName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/queues$/);
});

test("delete queue", async ({ page }) => {
  const queueName = `e2e_queue_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  const createdQueue = await createQueue(page, queueName);

  await page.goto(`/queues/${createdQueue.id}`);
  await page.getByRole("heading", { name: queueName }).waitFor();
  await page.getByRole("button", { name: "Delete Queue" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${queueName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/queues$/);
});
