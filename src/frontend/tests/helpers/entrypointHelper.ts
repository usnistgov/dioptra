import { expect, type Locator, type Page } from "@playwright/test";

export async function syncEntrypointPlugin(page: Page, info: Locator, id: number, name: string) {
  const notification = page.getByRole("alert").filter({
    hasText: `Selected latest version of '${name}'. Submit Entrypoint to save.`,
  });
  // A previous notification must expire before it can identify this model update.
  await expect(notification).toHaveCount(0);
  const responsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === `/api/v1/plugins/${id}` && response.request().method() === "GET",
  );
  await info
    .getByRole("button", { name: `Sync ${name} to latest version`, exact: true })
    .first()
    .click();
  const response = await responsePromise;
  expect(response.ok(), await response.text()).toBe(true);
  // The application publishes this notification after replacing the selected plugin.
  await expect(notification).toBeVisible();
  await expect(info.locator(".q-field .q-chip").filter({ hasText: name })).not.toContainText("outdated");
}

export async function validateEntrypoint(page: Page, id: number) {
  const notification = page.getByRole("alert").filter({ hasText: "Entrypoint is valid!" });
  await expect(notification).toHaveCount(0);
  const responsePromise = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === `/api/v1/entrypoints/${id}` &&
      response.request().method() === "PUT" &&
      new URL(response.url()).searchParams.get("validateOnly") === "true",
  );
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  const response = await responsePromise;
  expect(response.ok(), await response.text()).toBe(true);
  await expect(notification).toBeVisible();
}
