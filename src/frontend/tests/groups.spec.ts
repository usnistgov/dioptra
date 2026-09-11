import { randomUUID } from "node:crypto";
import { expect, test as base } from "@playwright/test";

import { ensureLoggedInAsTestUser, testUser } from "./helpers/testUserHelper";

type OtherGroup = { id: number; name: string; user: { username: string } };

const test = base.extend<{ otherGroup: OtherGroup }>({
  otherGroup: async ({ playwright, baseURL }, use) => {
    const username = `e2e_group_owner_${randomUUID()}`;
    const password = "Password123!";
    const ownerApi = await playwright.request.newContext({ baseURL });
    let loggedIn = false;
    try {
      const registration = await ownerApi.post("/api/v1/users", {
        data: { username, email: `${username}@example.com`, password, confirmPassword: password },
      });
      expect(registration.ok()).toBe(true);
      const login = await ownerApi.post("/api/v1/auth/login", { data: { username, password } });
      expect(login.ok()).toBe(true);
      loggedIn = true;
      const creation = await ownerApi.post("/api/v1/groups/", {
        data: { name: `e2e_other_group_${randomUUID()}`, public: true },
      });
      expect(creation.ok()).toBe(true);
      await use(await creation.json());
    } finally {
      try {
        if (loggedIn) {
          const deletion = await ownerApi.delete("/api/v1/users/current", { data: { password } });
          expect(deletion.ok()).toBe(true);
        }
      } finally {
        await ownerApi.dispose();
      }
    }
  },
});

test("focus refresh recovers a remotely deleted active group", async ({ page }) => {
  await ensureLoggedInAsTestUser(page);
  const response = await page.request.post("/api/v1/groups/", {
    data: { name: `e2e_focus_group_${Date.now()}` },
  });
  expect(response.ok()).toBe(true);
  const group = await response.json();
  await page.goto(`/experiments?groupId=${group.id}`);
  await expect(page.getByRole("button", { name: new RegExp(group.name) })).toBeEnabled();
  expect((await page.request.delete(`/api/v1/groups/${group.id}`)).ok()).toBe(true);

  const refreshResponse = page.waitForResponse(
    (res) => new URL(res.url()).pathname === "/api/v1/users/current" && res.request().method() === "GET",
  );
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  expect((await refreshResponse).ok()).toBe(true);
  await expect(page).toHaveURL(
    (url) => url.pathname === "/experiments" && url.searchParams.get("groupId") !== String(group.id),
  );
  await expect(page.getByRole("button", { name: new RegExp(group.name) })).toHaveCount(0);
});

test("a delayed focus refresh cannot restore a logged-out session", async ({ page }) => {
  await ensureLoggedInAsTestUser(page);
  await page.goto("/login");
  await expect(page.getByRole("button", { name: "Log Out", exact: true })).toBeVisible();
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started!: () => void;
  const captured = new Promise<void>((resolve) => {
    started = resolve;
  });
  let requests = 0;
  await page.route("**/api/v1/users/current", async (route) => {
    requests++;
    const response = await route.fetch();
    started();
    await pending;
    await route.fulfill({ response });
  });
  await page.evaluate(() => {
    window.dispatchEvent(new Event("focus"));
    window.dispatchEvent(new Event("focus"));
  });
  await captured;
  await page.getByRole("button", { name: "Log Out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Login", exact: true })).toBeVisible();
  const finished = page.waitForResponse("**/api/v1/users/current");
  release();
  await finished;
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await expect(page.getByRole("heading", { name: "Login", exact: true })).toBeVisible();
  expect(requests).toBe(1);
});

test("created group becomes the active context", async ({ page }) => {
  const groupName = `e2e_created_group_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await page.goto("/groups/new");
  await page.getByRole("textbox", { name: "Name:" }).fill(groupName);

  const createResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/groups/") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  expect(createResponse.ok()).toBe(true);
  const createdGroup = await createResponse.json();

  await expect(page).toHaveURL(/\/groups$/);
  await expect(page.getByRole("button", { name: new RegExp(groupName) })).toBeEnabled();

  const search = page.getByPlaceholder("Search");
  await search.fill(groupName);
  const createdRow = page.locator("tbody tr").filter({ hasText: `${testUser.username}/${groupName}` });
  await expect(createdRow.getByRole("button", { name: "Active Context" })).toBeVisible();
  await expect(createdRow).toHaveClass(/bg-blue-1/);

  await page.goto("/groups/new");
  await page.getByRole("button", { name: new RegExp(groupName) }).click();
  const groupMenu = page.locator(".q-menu:visible");
  await expect(groupMenu.getByText("Your Groups", { exact: true })).toBeVisible();
  await expect(groupMenu.getByText(groupName, { exact: true })).toBeVisible();
  await groupMenu.getByText("View Other Groups", { exact: true }).click();
  await expect(page).toHaveURL(/\/groups$/);

  let groupListRequests = 0;
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (request.method() === "GET" && url.pathname === "/api/v1/groups/") {
      groupListRequests++;
    }
  });

  const searchResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "GET",
  );
  await search.fill(groupName);
  expect((await searchResponsePromise).ok()).toBe(true);
  await expect(createdRow).toBeVisible();
  const requestsBeforeDelete = groupListRequests;
  const deleteResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/v1/groups/${createdGroup.id}`) && response.request().method() === "DELETE",
  );
  const refreshResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "GET",
  );
  await createdRow.getByRole("button", { name: "Delete group" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
  expect((await deleteResponsePromise).ok()).toBe(true);
  expect((await refreshResponsePromise).ok()).toBe(true);
  expect(groupListRequests - requestsBeforeDelete).toBe(1);
  await expect(createdRow).toHaveCount(0);
});

test("group table shows context and owner-specific actions", async ({ page, otherGroup }) => {
  await ensureLoggedInAsTestUser(page);

  const adminGroupName = `e2e_admin_group_${Date.now()}`;

  await page.goto("/groups");

  await expect(page.getByRole("heading", { name: "Groups" })).toBeVisible();
  await expect(
    page.getByText("All users can read and write resources in every group as permissions are not yet implemented."),
  ).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "ID" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Owner" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Context" })).toBeVisible();

  const createGroupResponse = await page.request.post("/api/v1/groups/", { data: { name: adminGroupName } });
  expect(createGroupResponse.ok()).toBe(true);
  const adminGroup = await createGroupResponse.json();

  const search = page.getByPlaceholder("Search");
  await search.fill(testUser.username);
  const ownedRow = page.locator("tbody tr").filter({
    has: page.getByText(`${testUser.username}/${testUser.username}`, { exact: true }),
  });
  await expect(ownedRow.getByText(`${testUser.username}/${testUser.username}`)).toBeVisible();
  await expect(ownedRow.getByRole("button", { name: "Active Context" })).toBeVisible();
  await expect(ownedRow.getByRole("button", { name: "Delete group" })).toBeEnabled();
  await expect(ownedRow).toHaveClass(/bg-blue-1/);

  const adminSearchResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "GET",
  );
  await search.fill(adminGroupName);
  expect((await adminSearchResponsePromise).ok()).toBe(true);
  const adminRow = page.locator("tbody tr").filter({ hasText: adminGroupName });
  await expect(adminRow.getByRole("button", { name: "Set Context" })).toBeVisible();

  const loginStatusRefreshPromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/users/current" && response.request().method() === "GET",
  );
  await adminRow.getByRole("button", { name: "Set Context" }).click();
  expect((await loginStatusRefreshPromise).ok()).toBe(true);
  await expect(adminRow.getByRole("button", { name: "Active Context" })).toBeVisible();
  await expect(adminRow).toHaveClass(/bg-blue-1/);

  const otherSearchResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "GET",
  );
  await search.fill(otherGroup.name);
  expect((await otherSearchResponsePromise).ok()).toBe(true);
  const otherRow = page.locator("tbody tr").filter({
    has: page.getByText(`${otherGroup.user.username}/${otherGroup.name}`, { exact: true }),
  });
  await expect(otherRow.getByText(`${otherGroup.user.username}/${otherGroup.name}`)).toBeVisible();
  await expect(otherRow.getByRole("button", { name: "Delete group" })).toBeDisabled();

  let groupListRequests = 0;
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (request.method() === "GET" && url.pathname === "/api/v1/groups/") {
      groupListRequests++;
    }
  });
  await otherRow.getByRole("button", { name: "Set Context" }).click();
  await expect(otherRow.getByRole("button", { name: "Active Context" })).toBeVisible();
  await expect(otherRow).toHaveClass(/bg-blue-1/);
  expect(groupListRequests).toBe(0);

  await page.getByRole("button", { name: new RegExp(otherGroup.name) }).click();
  const groupMenu = page.locator(".q-menu:visible");
  await expect(groupMenu.getByText(otherGroup.name, { exact: true })).toHaveCount(0);
  await expect(groupMenu.getByText("View Other Groups", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");

  await otherRow.click();
  await expect(page).toHaveURL(new RegExp(`/groups/${otherGroup.id}/admin$`));
  await expect(page.getByRole("heading", { name: "Group Admin" })).toBeVisible();
  await expect(page.getByRole("button", { name: new RegExp(otherGroup.name) })).toBeDisabled();
  await expect(page.getByText(`${otherGroup.user.username}/${otherGroup.name}`, { exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Group Name" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Save Name" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Delete Group" })).toBeDisabled();

  await page.goto(`/groups/${adminGroup.id}/admin`);
  await expect(page.getByText(`${testUser.username}/${adminGroupName}`, { exact: true })).toBeVisible();
  await expect(page.getByText("Group Managers", { exact: true })).toBeVisible();
  await expect(page.getByText("Group Members", { exact: true })).toBeVisible();
  const nameInput = page.getByRole("textbox", { name: "Group Name" });
  await expect(nameInput).toBeEnabled();
  await expect(page.getByRole("button", { name: "Delete Group" })).toBeEnabled();

  const renamedGroupName = `${adminGroupName}_renamed`;
  await nameInput.fill(renamedGroupName);
  const renameResponsePromise = page.waitForResponse(
    (response) => response.url().includes(`/api/v1/groups/${adminGroup.id}`) && response.request().method() === "PUT",
  );
  await page.getByRole("button", { name: "Save Name" }).click();
  expect((await renameResponsePromise).ok()).toBe(true);
  await expect(page.getByText(`${testUser.username}/${renamedGroupName}`, { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Delete Group" }).click();
  await expect(
    page.getByRole("dialog").getByText(`${testUser.username}/${renamedGroupName}`, { exact: true }),
  ).toBeVisible();
  const deleteResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/v1/groups/${adminGroup.id}`) && response.request().method() === "DELETE",
  );
  await page.getByRole("button", { name: "Confirm" }).click();
  expect((await deleteResponsePromise).ok()).toBe(true);
  await expect(page).toHaveURL(/\/groups$/);
});

test("opening a group in a new tab keeps the parent context isolated", async ({ page }) => {
  const groupName = `e2e_new_tab_group_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  await page.goto("/groups");
  await expect(page.getByRole("button", { name: new RegExp(testUser.username) })).toBeEnabled();

  const createResponse = await page.request.post("/api/v1/groups/", { data: { name: groupName } });
  expect(createResponse.ok()).toBe(true);
  const group = await createResponse.json();

  const searchResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "GET",
  );
  await page.getByPlaceholder("Search").fill(groupName);
  expect((await searchResponsePromise).ok()).toBe(true);
  const groupRow = page.locator("tbody tr").filter({ hasText: `${testUser.username}/${groupName}` });
  await expect(groupRow).toBeVisible();

  const popupPromise = page.waitForEvent("popup");
  await groupRow.click({ button: "right" });
  await page.locator(".q-menu:visible").getByText("Open In New Tab", { exact: true }).click();
  const popup = await popupPromise;

  await popup.waitForLoadState();
  await expect(popup).toHaveURL(new RegExp(`/groups/${group.id}/admin$`));
  await expect(popup.getByRole("heading", { name: "Group Admin" })).toBeVisible();
  await expect(popup.getByRole("button", { name: new RegExp(groupName) })).toBeDisabled();
  expect(await popup.evaluate(() => window.opener)).toBeNull();

  await expect(page).toHaveURL(/\/groups$/);
  await expect(page.getByRole("button", { name: new RegExp(testUser.username) })).toBeEnabled();

  await popup.close();
  const deleteResponse = await page.request.delete(`/api/v1/groups/${group.id}`);
  expect(deleteResponse.ok()).toBe(true);
});

test("browser history restores group context from the URL", async ({ page }) => {
  const groupName = `e2e_history_group_${Date.now()}`;

  await ensureLoggedInAsTestUser(page);
  const userResponse = await page.request.get("/api/v1/users/current");
  expect(userResponse.ok()).toBe(true);
  const user = await userResponse.json();
  const originalGroup = user.groups.find(
    (group) => group.name === testUser.username && group.user.username === testUser.username,
  );
  expect(originalGroup).toBeTruthy();

  await page.goto("/groups/new");
  await page.getByRole("textbox", { name: "Name:" }).fill(groupName);
  const createResponsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/groups/" && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Submit" }).click();
  const createResponse = await createResponsePromise;
  expect(createResponse.ok()).toBe(true);
  const group = await createResponse.json();

  await page.getByRole("button", { name: "Navigation Menu" }).click();
  await page.locator(".q-menu:visible").getByText("Experiments", { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/experiments\\?groupId=${group.id}$`));

  await page.getByRole("button", { name: new RegExp(groupName) }).click();
  await page.locator(".q-menu:visible").getByText(originalGroup.name, { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/experiments\\?groupId=${originalGroup.id}$`));

  await page.reload();
  await expect(page).toHaveURL(new RegExp(`/experiments\\?groupId=${originalGroup.id}$`));
  await expect(page.getByRole("button", { name: new RegExp(originalGroup.name) })).toBeEnabled();

  const searchTerm = "history-search";
  const searchResponsePromise = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/v1/experiments/" &&
      response.url().includes(searchTerm) &&
      response.request().method() === "GET",
  );
  await page.getByPlaceholder("Search").fill(searchTerm);
  expect((await searchResponsePromise).ok()).toBe(true);

  await page.getByRole("button", { name: "Navigation Menu" }).click();
  await page.locator(".q-menu:visible").getByText("Plugins", { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/plugins\\?groupId=${originalGroup.id}$`));

  await page.getByRole("button", { name: new RegExp(originalGroup.name) }).click();
  await page.locator(".q-menu:visible").getByText(groupName, { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/plugins\\?groupId=${group.id}$`));

  await page.getByRole("button", { name: "Navigation Menu" }).click();
  await page.locator(".q-menu:visible").getByText("Jobs", { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/jobs\\?groupId=${group.id}$`));

  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`/plugins\\?groupId=${group.id}$`));
  await expect(page.getByRole("button", { name: new RegExp(groupName) })).toBeEnabled();

  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`/experiments\\?groupId=${originalGroup.id}$`));
  await expect(page.getByRole("button", { name: new RegExp(originalGroup.name) })).toBeEnabled();
  await expect(page.getByPlaceholder("Search")).toHaveValue(searchTerm);

  await page.goForward();
  await expect(page).toHaveURL(new RegExp(`/plugins\\?groupId=${group.id}$`));
  await expect(page.getByRole("button", { name: new RegExp(groupName) })).toBeEnabled();

  const deleteResponse = await page.request.delete(`/api/v1/groups/${group.id}`);
  expect(deleteResponse.ok()).toBe(true);
});
