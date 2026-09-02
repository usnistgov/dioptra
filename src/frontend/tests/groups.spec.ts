import { expect, test } from "@playwright/test";

import { ensureLoggedInAsTestUser, testUser } from "./helpers/testUserHelper";

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
  await groupMenu.getByRole("link", { name: "View Other Groups" }).click();
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

test("group table shows context and owner-specific actions", async ({ page }) => {
  await ensureLoggedInAsTestUser(page);

  const adminGroupName = `e2e_admin_group_${Date.now()}`;
  const groupsResponse = await page.request.get("/api/v1/groups/?pageLength=100");
  expect(groupsResponse.ok()).toBe(true);
  const groups = (await groupsResponse.json()).data;
  const otherGroup = groups.find((group) => group.user.username !== testUser.username);
  expect(otherGroup).toBeTruthy();

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
  const ownedRow = page.locator("tbody tr").filter({ hasText: testUser.username });
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
  const otherRow = page.locator("tbody tr").filter({ hasText: otherGroup.name });
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
  await expect(groupMenu.getByRole("link", { name: "View Other Groups" })).toBeVisible();
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
