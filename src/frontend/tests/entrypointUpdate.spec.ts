import type { Locator, Page } from "@playwright/test";

import { expect, test } from "./fixtures/test";

import { navigateToEntrypoints, syncEntrypointPlugin, validateEntrypoint } from "./helpers/entrypointHelper";

type Mutation = { method: string; path: string; dryRun: boolean; body: any };

function expectMutations(mutations: Mutation[], dryRuns: boolean[]) {
  expect(mutations).toHaveLength(dryRuns.length);
  expect(mutations.map(({ method, path, dryRun }) => [method, path, dryRun])).toEqual(
    dryRuns.map((dryRun) => ["PUT", "/api/v1/entrypoints/101", dryRun]),
  );
}

function plugin(id: number, snapshotId: number, latestSnapshot = true) {
  return {
    id,
    snapshotId,
    latestSnapshot,
    name: `plugin-${id}`,
    description: "",
    files: [
      {
        tasks: {
          functions: [{ name: `task_${id}`, inputParams: [], outputParams: [] }],
          artifacts: [{ name: `artifact_${id}`, outputParams: [] }],
        },
      },
    ],
  };
}

async function mockEditor(page: Page, latestSelections = false) {
  const current = {
    id: 101,
    snapshot: 1001,
    name: "coordinated-entrypoint",
    description: "",
    group: 1,
    queues: [],
    parameters: [],
    artifactParameters: [],
    taskGraph: "step:\n  task: task_1\n",
    artifactGraph: "",
    plugins: [plugin(1, 11, latestSelections), plugin(2, 21, latestSelections)],
    artifactPlugins: [plugin(1, 11, latestSelections), plugin(3, 31, latestSelections)],
  };
  function latestPlugin(id: number, snapshot: number) {
    const { snapshotId: _snapshotId, latestSnapshot: _latestSnapshot, ...resource } = plugin(id, snapshot);
    return { ...resource, snapshot };
  }
  const latest = new Map([1, 2, 3, 4].map((id) => [id, latestPlugin(id, id * 10 + (latestSelections ? 1 : 2))]));
  const mutations: Mutation[] = [];
  const failures: string[] = [];
  const pluginGetHolds = new Map<number, { requested: () => void; released: Promise<void> }>();
  function holdNextPluginGet(id: number) {
    let requested!: () => void;
    let release!: () => void;
    const received = new Promise<void>((resolve) => (requested = resolve));
    const released = new Promise<void>((resolve) => (release = resolve));
    pluginGetHolds.set(id, { requested, released });
    return { received, release };
  }
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (request.method() !== "GET") {
      mutations.push({
        method: request.method(),
        path,
        dryRun: url.searchParams.get("validateOnly") === "true",
        body: request.postDataJSON(),
      });
      const message = failures.shift();
      if (!message && url.searchParams.get("validateOnly") !== "true") {
        const { pluginSnapshotIds, artifactPluginSnapshotIds, ...content } = request.postDataJSON();
        Object.assign(current, content);
        for (const [role, snapshots] of [
          ["plugins", pluginSnapshotIds],
          ["artifactPlugins", artifactPluginSnapshotIds],
        ] as const) {
          current[role] = snapshots.map((snapshot: number) => {
            const id = Math.floor(snapshot / 10);
            return plugin(id, snapshot, latest.get(id)?.snapshot === snapshot);
          });
        }
      }
      await route.fulfill({
        status: message ? 400 : 200,
        json: message
          ? { message: "Entrypoint validation failed", detail: { reason: { schema_issues: [message] } } }
          : current,
      });
    } else if (path.endsWith("/users/current")) {
      await route.fulfill({ json: { id: 1, username: "test-user", groups: [{ id: 1, name: "test-group" }] } });
    } else if (path === "/api/v1/entrypoints/101") {
      await route.fulfill({ json: current });
    } else if (/\/plugins\/\d+$/.test(path)) {
      const id = Number(path.split("/").at(-1));
      const hold = pluginGetHolds.get(id);
      if (hold) {
        pluginGetHolds.delete(id);
        hold.requested();
        await hold.released;
      }
      await route.fulfill({ json: latest.get(id) });
    } else {
      await route.fulfill({
        json: { data: path === "/api/v1/plugins/" ? [...latest.values()] : [], next: null, totalNumItems: 0 },
      });
    }
  });
  await page.goto("/entrypoints/101");
  await expect(page.getByRole("heading", { name: current.name })).toBeVisible();
  return { current, latest, latestPlugin, mutations, failures, holdNextPluginGet };
}

function taskInfo(page: Page) {
  return page.locator("fieldset").filter({ has: page.locator("legend", { hasText: "Task Graph Info" }) });
}

function artifactInfo(page: Page) {
  return page.locator("fieldset").filter({ has: page.locator("legend", { hasText: "Artifact Info" }) });
}

async function remove(info: Locator, id: number) {
  await info
    .locator(".q-field .q-chip")
    .filter({ hasText: `plugin-${id}` })
    .getByRole("button", { name: "Remove" })
    .click();
}

async function add(page: Page, info: Locator, id: number) {
  await info.getByRole("combobox", { name: /^Plugins:/ }).fill(`plugin-${id}`);
  await page
    .getByRole("option")
    .filter({ hasText: `plugin-${id}` })
    .click();
  await expect(info.locator(".q-field .q-chip").filter({ hasText: `plugin-${id}` })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("option")).toHaveCount(0);
}

test("validate unchanged bindings and save an independent task plugin update in one PUT", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await expect(page.getByRole("button", { name: "Save Plugin Selection" })).toHaveCount(0);
  await validateEntrypoint(page, 101);
  expectMutations(mutations, [true]);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([11, 21]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([11, 31]);
  await syncEntrypointPlugin(page, taskInfo(page), 1, "plugin-1");
  await validateEntrypoint(page, 101);
  expectMutations(mutations, [true, true]);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expectMutations(mutations, [true, true, false]);
  expect(mutations[1].body).toEqual(mutations[2].body);
  expect(mutations[2].body.pluginSnapshotIds).toEqual([12, 21]);
  expect(mutations[2].body.artifactPluginSnapshotIds).toEqual([11, 31]);
  expect(mutations[2].body).not.toHaveProperty("plugins");
  expect(mutations[2].body).not.toHaveProperty("artifactPlugins");
  await page.goto("/entrypoints/101");
  await expect(page.getByRole("heading", { name: "coordinated-entrypoint" })).toBeVisible();
  await expect(
    taskInfo(page).getByRole("button", { name: "Sync plugin-1 to latest version", exact: true }),
  ).toHaveCount(0);
  await expect(taskInfo(page).locator(".q-field .q-chip").filter({ hasText: "plugin-1" })).not.toContainText(
    "outdated",
  );
  await expect(
    artifactInfo(page).getByRole("button", { name: "Sync plugin-1 to latest version", exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit EntryPoint" })).toBeDisabled();
});

test("artifact synchronization retains task-role pins including the same plugin", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await syncEntrypointPlugin(page, artifactInfo(page), 1, "plugin-1");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expectMutations(mutations, [false]);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([11, 21]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([12, 31]);
  await page.goto("/entrypoints/101");
  await expect(page.getByRole("heading", { name: "coordinated-entrypoint" })).toBeVisible();
  await expect(
    artifactInfo(page).getByRole("button", { name: "Sync plugin-1 to latest version", exact: true }),
  ).toHaveCount(0);
  await expect(artifactInfo(page).locator(".q-field .q-chip").filter({ hasText: "plugin-1" })).not.toContainText(
    "outdated",
  );
  await expect(
    taskInfo(page).getByRole("button", { name: "Sync plugin-1 to latest version", exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit EntryPoint" })).toBeDisabled();
});

test("stage additions and removals in both roles with complete latest selections", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await remove(taskInfo(page), 1);
  await remove(artifactInfo(page), 3);
  await add(page, taskInfo(page), 4);
  await add(page, artifactInfo(page), 4);
  await taskInfo(page).getByRole("textbox").fill("step:\n  task: task_2\n");
  await validateEntrypoint(page, 101);
  expectMutations(mutations, [true]);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expectMutations(mutations, [true, false]);
  expect(mutations[0].body).toEqual(mutations[1].body);
  expect(mutations[1].body.pluginSnapshotIds).toEqual([21, 42]);
  expect(mutations[1].body.artifactPluginSnapshotIds).toEqual([11, 42]);
});

test("send explicit empty association lists as transport-only evidence", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await remove(taskInfo(page), 1);
  await remove(taskInfo(page), 2);
  await remove(artifactInfo(page), 1);
  await remove(artifactInfo(page), 3);
  await taskInfo(page).getByRole("textbox").fill("{}");
  // The mock accepts this body; a native entrypoint still requires a valid task graph.
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expectMutations(mutations, [false]);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([]);
});

for (const action of ["Validate", "Submit EntryPoint"]) {
  test(`${action} rejection retains edits and allows a newer snapshot correction`, async ({ page }) => {
    const { mutations, failures, latest, latestPlugin, holdNextPluginGet } = await mockEditor(page);
    await syncEntrypointPlugin(page, taskInfo(page), 1, "plugin-1");
    await page.getByRole("textbox", { name: "Name:" }).fill("retained-name");
    await page.getByRole("textbox", { name: "Description:" }).fill("retained-description");
    await artifactInfo(page).getByRole("textbox").fill("retained_artifact: {}\n");
    await add(page, artifactInfo(page), 4);
    const editedGraph = "edited_step:\n  task: task_1\n";
    await taskInfo(page).getByRole("textbox").fill(editedGraph);
    latest.set(1, latestPlugin(1, 13));
    failures.push("Selected plugin snapshot is no longer latest. Select the latest snapshot and retry.");
    await page.getByRole("button", { name: action, exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("no longer latest");
    await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
    await expect(page).toHaveURL(/\/entrypoints\/101$/);
    await expect(page.getByRole("textbox", { name: "Name:" })).toHaveValue("retained-name");
    await expect(taskInfo(page).getByRole("textbox")).toHaveText(editedGraph);
    await expect(page.getByRole("textbox", { name: "Description:" })).toHaveValue("retained-description");
    await expect(artifactInfo(page).getByRole("textbox")).toHaveText("retained_artifact: {}\n");
    await expect(taskInfo(page).locator(".q-field .q-chip").filter({ hasText: "plugin-1" })).toContainText("outdated");
    await expect(
      taskInfo(page).getByRole("button", { name: "Sync plugin-1 to latest version", exact: true }).first(),
    ).toBeVisible();
    const rejectedDryRun = action === "Validate";
    expectMutations(mutations, [rejectedDryRun]);
    expect(mutations[0].body.pluginSnapshotIds).toEqual([12, 21]);
    expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([11, 31, 42]);
    await validateEntrypoint(page, 101);
    expectMutations(mutations, [rejectedDryRun, true]);
    expect(mutations[1].body).toEqual(mutations[0].body);
    const heldGet = holdNextPluginGet(1);
    const synchronization = syncEntrypointPlugin(page, taskInfo(page), 1, "plugin-1");
    await heldGet.received;
    try {
      // A delayed response must not report synchronization before the staged model is updated.
      const state = await Promise.race([
        synchronization.then(() => "completed"),
        new Promise<string>((resolve) => setTimeout(() => resolve("waiting"), 250)),
      ]);
      expect(state).toBe("waiting");
      expectMutations(mutations, [rejectedDryRun, true]);
    } finally {
      heldGet.release();
    }
    await synchronization;
    await page.getByRole("button", { name: "Submit EntryPoint" }).click();
    await expect(page).toHaveURL(/\/entrypoints$/);
    expectMutations(mutations, [rejectedDryRun, true, false]);
    expect(mutations[2].body).toEqual({ ...mutations[1].body, pluginSnapshotIds: [13, 21] });
    expect(mutations[2].body).toMatchObject({
      name: "retained-name",
      description: "retained-description",
      taskGraph: editedGraph,
      artifactGraph: "retained_artifact: {}\n",
      pluginSnapshotIds: [13, 21],
      artifactPluginSnapshotIds: [11, 31, 42],
    });
  });
}

test("a rejected graph save keeps the navigation warning and permits graph correction", async ({ page }) => {
  const { failures, mutations } = await mockEditor(page);
  await syncEntrypointPlugin(page, taskInfo(page), 1, "plugin-1");
  await taskInfo(page).getByRole("textbox").fill("step:\n  task: invalid_task\n");
  failures.push("Graph invokes an unknown task: invalid_task");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page.getByRole("dialog")).toContainText("unknown task");
  await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
  expectMutations(mutations, [false]);
  await navigateToEntrypoints(page);
  await expect(page.getByRole("dialog")).toContainText("unsaved changes");
  await page.getByRole("dialog").getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const correctedGraph = "corrected_step:\n  task: task_1\n";
  await taskInfo(page).getByRole("textbox").fill(correctedGraph);
  await expect(taskInfo(page).getByRole("textbox")).toHaveText(correctedGraph);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expectMutations(mutations, [false, false]);
  expect(mutations[1].body.pluginSnapshotIds).toEqual([12, 21]);
  expect(mutations[1].body.taskGraph).toEqual(correctedGraph);
});

test("latest bindings stay unchanged through reverted content and association edits", async ({ page }) => {
  const { current, mutations } = await mockEditor(page, true);
  const submit = page.getByRole("button", { name: "Submit EntryPoint" });
  for (const info of [taskInfo(page), artifactInfo(page)]) {
    await expect(info.locator(".q-field .q-chip").filter({ hasText: "outdated" })).toHaveCount(0);
    await expect(info.getByRole("button", { name: /^Sync / })).toHaveCount(0);
  }
  await expect(submit).toBeDisabled();
  for (const [name, saved] of [
    ["Name:", current.name],
    ["Description:", current.description],
  ]) {
    const field = page.getByRole("textbox", { name, exact: true });
    await field.fill("temporary edit");
    await expect(submit).toBeEnabled();
    await field.fill(saved);
    await expect(submit).toBeDisabled();
  }
  for (const [info, saved] of [
    [taskInfo(page), current.taskGraph],
    [artifactInfo(page), current.artifactGraph],
  ] as const) {
    await info.getByRole("textbox").fill("temporary: {}\n");
    await expect(submit).toBeEnabled();
    await info.getByRole("textbox").fill(saved);
    await expect(submit).toBeDisabled();
  }
  for (const info of [taskInfo(page), artifactInfo(page)]) {
    const id = 1;
    await remove(info, id);
    await expect(submit).toBeEnabled();
    await add(page, info, id);
    await expect(submit).toBeDisabled();
  }
  await navigateToEntrypoints(page);
  await expect(page).toHaveURL(/\/entrypoints$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(mutations).toHaveLength(0);
});

test("same-snapshot refresh changes display metadata without enabling a save", async ({ page }) => {
  const { latest, latestPlugin, mutations } = await mockEditor(page);
  latest.set(
    1,
    Object.assign(latestPlugin(1, 11), { description: "refreshed display metadata", url: "/api/v1/plugins/1" }),
  );
  for (const info of [taskInfo(page), artifactInfo(page)]) {
    await syncEntrypointPlugin(page, info, 1, "plugin-1");
    await expect(
      page.getByRole("alert").filter({ hasText: "Already selected latest version of 'plugin-1'." }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Submit EntryPoint" })).toBeDisabled();
  }
  await navigateToEntrypoints(page);
  await expect(page).toHaveURL(/\/entrypoints$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(mutations).toHaveLength(0);
});
