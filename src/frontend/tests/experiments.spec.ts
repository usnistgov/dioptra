import { expect, Page, test } from "@playwright/test";

import { createEntrypoint, createQueue } from "./helpers/createResourceHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

async function createExperiment(page: Page, experimentName: string, entrypointName: string) {
  await page.goto("/experiments/new");

  await page.getByRole("heading", { name: "Create Experiment" }).waitFor();
  await page.getByRole("textbox", { name: "Name:" }).fill(experimentName);
  await page.getByRole("textbox", { name: "Description:" }).fill("Created by Playwright");

  const entrypointSelect = page.getByRole("combobox", { name: "Entrypoints:" });
  await entrypointSelect.click();
  await entrypointSelect.fill(entrypointName);
  await page.getByRole("option", { name: entrypointName }).click();

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/experiments") && response.request().method() === "POST",
  );

  await page.getByRole("button", { name: "Submit Experiment" }).click();
  const createResponse = await createResponsePromise;
  expect(
    createResponse.ok(),
    `Expected POST ${createResponse.url()} to succeed, got ${createResponse.status()} ${createResponse.statusText()}`,
  ).toBe(true);
  const createdExperiment = await createResponse.json();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully created '${experimentName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/experiments$/);

  return createdExperiment;
}

test("create experiment", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;
  const experimentName = `e2e_experiment_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  await createEntrypoint(page, entrypointName, queueName);
  await createExperiment(page, experimentName, entrypointName);
});

test("edit experiment", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;
  const experimentName = `e2e_experiment_${timestamp}`;
  const updatedExperimentName = `${experimentName}_update`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  await createEntrypoint(page, entrypointName, queueName);
  const createdExperiment = await createExperiment(page, experimentName, entrypointName);

  await page.goto(`/experiments/${createdExperiment.id}`);
  await page.getByRole("heading", { name: experimentName }).waitFor();
  await page.getByText(`Show "${experimentName}" Metadata`).click();

  await page.locator("tr").filter({ hasText: "Name" }).getByRole("button").click();
  await page.locator(".q-popup-edit input").fill(updatedExperimentName);
  await page.keyboard.press("Enter");

  await page.getByRole("button", { name: "Save" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully updated '${updatedExperimentName}'`,
    }),
  ).toBeVisible();
});

test("experiment detail sets and locks group context", async ({ page }) => {
  const timestamp = Date.now();
  const groupName = `e2e_group_${timestamp}`;
  const experimentName = `e2e_context_experiment_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  const groupResponse = await page.request.post("/api/v1/groups/", {
    data: { name: groupName },
  });
  expect(groupResponse.ok()).toBe(true);
  const group = await groupResponse.json();

  const experimentResponse = await page.request.post("/api/v1/experiments/", {
    data: {
      name: experimentName,
      description: "Created to test detail context",
      group: group.id,
      entrypoints: [],
    },
  });
  expect(experimentResponse.ok()).toBe(true);
  const experiment = await experimentResponse.json();

  await page.goto(`/experiments/${experiment.id}`);
  await page.getByRole("heading", { name: experimentName }).waitFor();

  const groupSwitcher = page.getByRole("button", { name: new RegExp(groupName) });
  await expect(groupSwitcher).toBeDisabled();

  await page.goto("/experiments/new");
  await page.getByRole("heading", { name: "Create Experiment" }).waitFor();
  await expect(page.getByRole("button", { name: new RegExp(groupName) })).toBeEnabled();
});

test("job form only shows linked entrypoints and queues", async ({ page }) => {
  const timestamp = Date.now();
  const linkedQueueName = `e2e_linked_queue_${timestamp}`;
  const unlinkedQueueName = `e2e_unlinked_queue_${timestamp}`;
  const linkedEntrypointName = `e2e_linked_entrypoint_${timestamp}`;
  const unlinkedEntrypointName = `e2e_unlinked_entrypoint_${timestamp}`;
  const experimentName = `e2e_linked_experiment_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, linkedQueueName);
  await createQueue(page, unlinkedQueueName);
  await createEntrypoint(page, linkedEntrypointName, linkedQueueName);
  await createEntrypoint(page, unlinkedEntrypointName, unlinkedQueueName);
  const experiment = await createExperiment(page, experimentName, linkedEntrypointName);

  await page.goto(`/experiments/${experiment.id}/jobs/new`);
  await page.getByRole("heading", { name: "Create Job" }).waitFor();

  const entrypointSelect = page.getByRole("combobox", { name: "Entrypoint:" });
  await entrypointSelect.click();
  await expect(page.getByRole("option", { name: linkedEntrypointName })).toBeVisible();
  await expect(page.getByRole("option", { name: unlinkedEntrypointName })).toHaveCount(0);
  await page.getByRole("option", { name: linkedEntrypointName }).click();

  const queueSelect = page.getByRole("combobox", { name: "Queue:" });
  await expect(queueSelect).toBeEnabled();
  await queueSelect.click();
  await expect(page.getByRole("option", { name: linkedQueueName })).toBeVisible();
  await expect(page.getByRole("option", { name: unlinkedQueueName })).toHaveCount(0);
});

test("delete experiment", async ({ page }) => {
  const timestamp = Date.now();
  const queueName = `e2e_queue_${timestamp}`;
  const entrypointName = `e2e_entrypoint_${timestamp}`;
  const experimentName = `e2e_experiment_${timestamp}`;

  await ensureLoggedInAsTestUser(page);
  await createQueue(page, queueName);
  await createEntrypoint(page, entrypointName, queueName);
  const createdExperiment = await createExperiment(page, experimentName, entrypointName);

  await page.goto(`/experiments/${createdExperiment.id}`);
  await page.getByRole("heading", { name: experimentName }).waitFor();
  await page.getByRole("button", { name: "Delete Experiment" }).click();
  await page.getByRole("button", { name: "Confirm" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: `Successfully deleted '${experimentName}'`,
    }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/experiments$/);
});
