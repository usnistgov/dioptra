import { expect, test } from "@playwright/test";

import { syncEntrypointPlugin, validateEntrypoint } from "./helpers/entrypointHelper";
import { ensureLoggedInAsTestUser } from "./helpers/testUserHelper";

test("save a one-to-two-output swap change with its exact plugin snapshots", async ({ page }) => {
  await ensureLoggedInAsTestUser(page);
  const apiUrl = process.env.DIOPTRA_E2E_API_URL ?? "http://localhost:5000";
  const api = page.request;
  async function get(path: string) {
    const response = await api.get(`${apiUrl}/api/v1/${path}`);
    expect(response.ok(), await response.text()).toBe(true);
    return response.json();
  }
  async function post(path: string, data: object) {
    const response = await api.post(`${apiUrl}/api/v1/${path}`, { data });
    expect(response.ok(), await response.text()).toBe(true);
    return response.json();
  }
  const group = (await get("users/current")).groups[0].id;
  const runId = Date.now();
  const stringType = (await get("pluginParameterTypes/?pageLength=100&search=string")).data.find(
    ({ name }: { name: string }) => name === "string",
  );
  expect(stringType).toBeDefined();
  const pairType = await post("pluginParameterTypes/", {
    name: `string_pair_${runId}`,
    group,
    structure: { tuple: ["string", "string"] },
  });
  const plugins = [];
  const files = [];
  for (const name of ["a", "b"]) {
    const plugin = await post("plugins/", { name: `interface_${name}_${runId}`, group });
    const payload = {
      filename: "tasks.py",
      contents: `def task_${name}():\n    return ('one', 'two')\n`,
      tasks: {
        functions: [
          {
            name: `task_${name}`,
            inputParams: [],
            outputParams: [{ name: "pair", parameterType: pairType.id }],
          },
        ],
      },
    };
    const file = await post(`plugins/${plugin.id}/files`, payload);
    plugins.push(await get(`plugins/${plugin.id}`));
    files.push({ id: file.id, payload });
  }
  const graph = (outputs: string) =>
    `choose:\n  ?implementation:\n    ?outputs: [${outputs}]\n    use_a:\n      task_a: []\n    use_b:\n      task_b: []\n`;
  const oldGraph = graph("value");
  const newGraph = graph("first, second");
  const saved = await post("entrypoints/", {
    name: `interface_entrypoint_${runId}`,
    group,
    taskGraph: oldGraph,
    plugins: plugins.map(({ id }) => id),
    artifactPlugins: [],
  });
  const latestSnapshots = [];
  for (const [index, plugin] of plugins.entries()) {
    const payload = files[index].payload;
    const task = payload.tasks.functions[0];
    const response = await api.put(`${apiUrl}/api/v1/plugins/${plugin.id}/files/${files[index].id}`, {
      data: {
        ...payload,
        tasks: {
          functions: [{ ...task, outputParams: ["x", "y"].map((name) => ({ name, parameterType: stringType.id })) }],
        },
      },
    });
    expect(response.ok(), await response.text()).toBe(true);
    latestSnapshots.push((await get(`plugins/${plugin.id}`)).snapshot);
  }
  const baseline = await get(`entrypoints/${saved.id}`);
  const mutations: { method: string; path: string; dryRun: boolean; body: any; status: number }[] = [];
  page.on("response", async (response) => {
    const request = response.request();
    const url = new URL(request.url());
    if (request.method() !== "GET" && url.pathname.startsWith(`/api/v1/entrypoints/${saved.id}`)) {
      mutations.push({
        method: request.method(),
        path: url.pathname,
        dryRun: url.searchParams.get("validateOnly") === "true",
        body: request.postDataJSON(),
        status: response.status(),
      });
    }
  });

  // Browser evidence begins after API setup has saved the old interface and published the new metadata.
  await page.goto(`/entrypoints/${saved.id}`);
  await expect(page.getByRole("heading", { name: saved.name })).toBeVisible();
  const taskInfo = page.locator("fieldset").filter({ has: page.locator("legend", { hasText: "Task Graph Info" }) });
  for (const plugin of plugins) {
    await syncEntrypointPlugin(page, taskInfo, plugin.id, plugin.name);
  }
  await taskInfo.getByRole("textbox").fill(newGraph);
  await validateEntrypoint(page, saved.id);
  expect(await get(`entrypoints/${saved.id}`)).toEqual(baseline);
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  const after = await get(`entrypoints/${saved.id}`);
  expect(mutations).toHaveLength(2);
  expect(mutations.map(({ method, path, dryRun, status }) => [method, path, dryRun, status])).toEqual([
    ["PUT", `/api/v1/entrypoints/${saved.id}`, true, 200],
    ["PUT", `/api/v1/entrypoints/${saved.id}`, false, 200],
  ]);
  expect(mutations[0].body).toEqual(mutations[1].body);
  expect(mutations[1].body.pluginSnapshotIds).toEqual(latestSnapshots);
  expect(mutations[1].body.artifactPluginSnapshotIds).toEqual([]);
  expect(after.taskGraph).toBe(newGraph);
  expect(after.plugins.map(({ snapshotId }: { snapshotId: number }) => snapshotId)).toEqual(latestSnapshots);
  const historical = await get(`entrypoints/${saved.id}/snapshots/${saved.snapshot}`);
  expect(historical.taskGraph).toBe(oldGraph);
  expect(historical.plugins.map(({ snapshotId }: { snapshotId: number }) => snapshotId)).toEqual(
    plugins.map(({ snapshot }) => snapshot),
  );
  for (const alias of ["use_a", "use_b"]) {
    const config = await get(
      `entrypoints/${saved.id}/snapshots/${after.snapshot}/config?swaps[implementation]=${alias}`,
    );
    expect(config.graph.choose["?implementation"]["?outputs"]).toEqual(["first", "second"]);
    for (const name of ["task_a", "task_b"]) {
      expect(config.tasks[name].outputs).toEqual([{ x: "string" }, { y: "string" }]);
    }
  }
  await page.goto(`/entrypoints/${saved.id}`);
  await expect(page.getByRole("heading", { name: saved.name })).toBeVisible();
  await page.getByRole("textbox", { name: "Description:" }).fill("subsequent complete save");
  await page.getByRole("button", { name: "Submit EntryPoint" }).click();
  await expect(page).toHaveURL(/\/entrypoints$/);
  expect(mutations).toHaveLength(3);
  expect(mutations[2]).toMatchObject({
    method: "PUT",
    path: `/api/v1/entrypoints/${saved.id}`,
    dryRun: false,
    status: 200,
  });
  expect(mutations[2].body.pluginSnapshotIds).toEqual(latestSnapshots);
  expect(mutations[2].body.artifactPluginSnapshotIds).toEqual([]);
  expect(
    (await get(`entrypoints/${saved.id}`)).plugins.map(({ snapshotId }: { snapshotId: number }) => snapshotId),
  ).toEqual(latestSnapshots);
});
