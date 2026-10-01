import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

type ApiFixtures = {
  apiURL: string | undefined;
};

export const test = base.extend<ApiFixtures>({
  apiURL: [process.env.DIOPTRA_E2E_API_URL, { option: true }],
  context: async ({ context, apiURL }, use) => {
    if (apiURL) {
      // Context routes also cover new pages; page-level mocks take precedence.
      await context.route("**/api/v1/**", async (route) => {
        const url = new URL(route.request().url());
        const response = await route.fetch({ url: new URL(url.pathname + url.search, apiURL).href });
        await route.fulfill({ response });
      });
    }

    try {
      await use(context);
    } finally {
      // Finish handlers while their fetched responses and browser context still exist.
      // Waiting preserves handler failures instead of ignoring errors during cleanup.
      await context.unrouteAll({ behavior: "wait" });
    }
  },
});
