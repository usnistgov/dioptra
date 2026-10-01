import { test as base } from "@playwright/test";
import type { BrowserContext, Route } from "@playwright/test";

export { expect } from "@playwright/test";

type ApiFixtures = {
  apiURL: string | undefined;
};

export async function installApiForwarding(context: BrowserContext, apiURL: string | undefined) {
  const pending = new Set<Promise<void>>();
  let stopping = false;
  let cleanup: Promise<void> | undefined;

  async function forward(route: Route) {
    if (stopping) {
      await route.abort("aborted");
      return;
    }
    const url = new URL(route.request().url());
    const response = await route.fetch({ url: new URL(url.pathname + url.search, apiURL).href });
    await route.fulfill({ response });
  }

  if (apiURL) {
    // Context routes also cover new pages; page-level mocks take precedence.
    await context.route("**/api/v1/**", async (route) => {
      const completion = forward(route);
      pending.add(completion);
      try {
        await completion;
      } finally {
        pending.delete(completion);
      }
    });
  }

  async function stop() {
    stopping = true;
    const errors: unknown[] = [];
    // Keep routing registered until every forward finishes. Removing it first can
    // make Playwright continue another pending route when the first handler ends.
    while (pending.size) {
      const results = await Promise.allSettled([...pending]);
      for (const result of results) {
        if (result.status === "rejected") errors.push(result.reason);
      }
    }
    await context.unrouteAll({ behavior: "wait" });
    if (errors.length) throw new AggregateError(errors, "API forwarding failed during cleanup");
  }

  return () => (cleanup ??= stop());
}

export const test = base.extend<ApiFixtures>({
  apiURL: [process.env.DIOPTRA_E2E_API_URL, { option: true }],
  context: async ({ context, apiURL }, use) => {
    const stop = await installApiForwarding(context, apiURL);
    try {
      await use(context);
    } finally {
      await stop();
    }
  },
});
