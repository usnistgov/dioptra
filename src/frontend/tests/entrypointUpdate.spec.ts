import { expect, test, type Locator, type Page } from "@playwright/test";

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

async function mockEditor(page: Page) {
  const current = {
    id: 101,
    snapshot: 1001,
    name: "coordinated-entrypoint",
    description: "",
    group: 1,
    queues: [],
    parameters: [],
    artifactParameters: [],
    taskGraph: "step: task_1",
    artifactGraph: "",
    plugins: [plugin(1, 11, false), plugin(2, 21, false)],
    artifactPlugins: [plugin(1, 11, false), plugin(3, 31, false)],
  };
  function latestPlugin(id: number, snapshot: number) {
    const { snapshotId: _snapshotId, latestSnapshot: _latestSnapshot, ...resource } = plugin(id, snapshot);
    return { ...resource, snapshot };
  }
  const latest = new Map([1, 2, 3, 4].map((id) => [id, latestPlugin(id, id * 10 + 2)]));
  const mutations: { method: string; path: string; dryRun: boolean; body: any }[] = [];
  const failures: string[] = [];
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
      await route.fulfill({ json: latest.get(Number(path.split("/").at(-1))) });
    } else {
      await route.fulfill({
        json: { data: path === "/api/v1/plugins/" ? [...latest.values()] : [], next: null, totalNumItems: 0 },
      });
    }
  });
  await page.goto("/entrypoints/101");
  await expect(page.getByRole("heading", { name: current.name })).toBeVisible();
  return { current, latest, latestPlugin, mutations, failures };
}

function taskInfo(page: Page) {
  return page.locator("fieldset").filter({ has: page.locator("legend", { hasText: "Task Graph Info" }) });
}

function artifactInfo(page: Page) {
  return page.locator("fieldset").filter({ has: page.locator("legend", { hasText: "Artifact Info" }) });
}

async function sync(info: Locator, id: number) {
  await info
    .getByRole("button", { name: `Sync plugin-${id} to latest version`, exact: true })
    .first()
    .click();
  await expect(info.locator(".q-field .q-chip").filter({ hasText: `plugin-${id}` })).not.toContainText("outdated");
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
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect.poll(() => mutations.length).toBe(1);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([11, 21]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([11, 31]);
  await sync(taskInfo(page), 1);
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect.poll(() => mutations.length).toBe(2);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(3);
  expect(mutations.every(({ method, path }) => method === "PUT" && path === "/api/v1/entrypoints/101")).toBe(true);
  expect(mutations.map(({ dryRun }) => dryRun)).toEqual([true, true, false]);
  expect(mutations[1].body).toEqual(mutations[2].body);
  expect(mutations[2].body.pluginSnapshotIds).toEqual([12, 21]);
  expect(mutations[2].body.artifactPluginSnapshotIds).toEqual([11, 31]);
  expect(mutations[2].body).not.toHaveProperty("plugins");
  expect(mutations[2].body).not.toHaveProperty("artifactPlugins");
});

test("artifact synchronization retains task-role pins including the same plugin", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await sync(artifactInfo(page), 1);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(1);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([11, 21]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([12, 31]);
});

test("stage additions and removals in both roles with complete latest selections", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await remove(taskInfo(page), 1);
  await remove(artifactInfo(page), 3);
  await add(page, taskInfo(page), 4);
  await add(page, artifactInfo(page), 4);
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect.poll(() => mutations.length).toBe(1);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(2);
  expect(mutations[0].body).toEqual(mutations[1].body);
  expect(mutations[1].body.pluginSnapshotIds).toEqual([21, 42]);
  expect(mutations[1].body.artifactPluginSnapshotIds).toEqual([11, 42]);
});

test("send explicit empty association lists", async ({ page }) => {
  const { mutations } = await mockEditor(page);
  await remove(taskInfo(page), 1);
  await remove(taskInfo(page), 2);
  await remove(artifactInfo(page), 1);
  await remove(artifactInfo(page), 3);
  await taskInfo(page).getByRole("textbox").fill("{}");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(1);
  expect(mutations[0].body.pluginSnapshotIds).toEqual([]);
  expect(mutations[0].body.artifactPluginSnapshotIds).toEqual([]);
});

for (const action of ["Validate", "Submit EntryPoint"]) {
  test(`${action} rejection retains edits and allows a newer snapshot correction`, async ({ page }) => {
    const { mutations, failures, latest, latestPlugin } = await mockEditor(page);
    await sync(taskInfo(page), 1);
    await page.getByRole("textbox", { name: "Name:" }).fill("retained-name");
    await taskInfo(page).getByRole("textbox").fill("step: updated_task");
    failures.push("Selected plugin snapshot is no longer latest. Select the latest snapshot and retry.");
    await page.getByRole("button", { name: action, exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("no longer latest");
    await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
    await expect(page).toHaveURL(/\/entrypoints\/101$/);
    await expect(page.getByRole("textbox", { name: "Name:" })).toHaveValue("retained-name");
    await expect(taskInfo(page).getByRole("textbox")).toHaveText("step: updated_task");
    expect(mutations).toHaveLength(1);
    latest.set(1, latestPlugin(1, 13));
    await sync(taskInfo(page), 1);
    await page.getByRole("button", { name: "Submit EntryPoint" }).click();
    await expect(page).toHaveURL(/\/entrypoints$/);
    expect(mutations).toHaveLength(2);
    expect(mutations[1].body).toMatchObject({
      name: "retained-name",
      taskGraph: "step: updated_task",
      pluginSnapshotIds: [13, 21],
      artifactPluginSnapshotIds: [11, 31],
    });
  });
}

test("a rejected graph save keeps the navigation warning and permits graph correction", async ({ page }) => {
  const { failures, mutations } = await mockEditor(page);
  await sync(taskInfo(page), 1);
  await taskInfo(page).getByRole("textbox").fill("step: invalid_task");
  failures.push("Graph invokes an unknown task: invalid_task");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page.getByRole("dialog")).toContainText("unknown task");
  await page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("tab", { name: "Entrypoints", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("unsaved changes");
  await page.getByRole("button", { name: "Cancel", exact: true }).last().click();
  await taskInfo(page).getByRole("textbox").fill("step: corrected_task");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(2);
  expect(mutations[1].body.pluginSnapshotIds).toEqual([12, 21]);
  expect(mutations[1].body.taskGraph).toEqual("step: corrected_task");
});
