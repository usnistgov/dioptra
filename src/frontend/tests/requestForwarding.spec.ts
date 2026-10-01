import { createServer } from "node:http";
import type { ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";

import { expect, installApiForwarding, test as base } from "./fixtures/test";

type Backend = {
  url: string;
  requests: string[];
  waitForListing: (name: string) => Promise<void>;
  releaseListing: (name: string) => void;
  releaseAll: () => void;
};

const test = base.extend<object, { backend: Backend }>({
  backend: [
    async ({ browserName: _browserName }, use) => {
      const requests: string[] = [];
      const held = new Map<string, ServerResponse[]>();
      const arrivals = new Map<string, () => void>();
      const server = createServer((request, response) => {
        const path = request.url!;
        requests.push(path);
        const name = new URL(path, "http://localhost").searchParams.get("search");
        if (path.startsWith("/api/v1/queues?") && name !== "forwarded" && name !== "mocked") {
          const responses = held.get(name!) ?? [];
          responses.push(response);
          held.set(name!, responses);
          arrivals.get(name!)?.();
        } else if (path.startsWith("/api/v1/")) {
          response.setHeader("Content-Type", "application/json");
          response.end(JSON.stringify({ path }));
        } else {
          response.setHeader("Content-Type", "text/html");
          response.end("<!doctype html><title>Forwarding test</title>");
        }
      });
      await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
      const url = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
      function releaseListing(name: string) {
        for (const response of held.get(name) ?? []) {
          response.setHeader("Content-Type", "application/json");
          response.end('{"data":[]}');
        }
        held.delete(name);
      }
      function releaseAll() {
        for (const name of held.keys()) releaseListing(name);
      }

      try {
        await use({
          url,
          requests,
          waitForListing: (name) => {
            if (held.has(name)) return Promise.resolve();
            return new Promise<void>((resolve) => arrivals.set(name, resolve));
          },
          releaseListing,
          releaseAll,
        });
      } finally {
        releaseAll();
        server.closeAllConnections();
        await new Promise<void>((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
      }
    },
    { scope: "worker" },
  ],
  apiURL: async ({ backend }, use) => {
    await use(backend.url);
  },
});

test("drain overlapping listings before unregistering forwarding and closing the context", async ({
  browser,
  backend,
}) => {
  const context = await browser.newContext({ baseURL: backend.url });
  const stop = await installApiForwarding(context, backend.url);
  const page = await context.newPage();
  const events: string[] = [];
  context.on("close", () => events.push("context closed"));
  try {
    await page.goto("/");
    await page.evaluate(() => {
      void fetch("/api/v1/queues?search=first");
      void fetch("/api/v1/queues?search=second");
    });
    await Promise.all([backend.waitForListing("first"), backend.waitForListing("second")]);
    events.push("two listings pending");
    const firstResponse = page.waitForResponse((response) => response.url().endsWith("search=first"));
    const secondResponse = page.waitForResponse((response) => response.url().endsWith("search=second"));
    const draining = stop();
    backend.releaseListing("first");
    expect((await firstResponse).ok()).toBe(true);
    events.push("first listing finished");
    backend.releaseListing("second");
    expect((await secondResponse).ok()).toBe(true);
    await draining;
    events.push("both handlers drained");
    expect(page.isClosed()).toBe(false);
    expect(backend.requests.filter((path) => path.endsWith("search=second"))).toHaveLength(1);
  } finally {
    backend.releaseAll();
    try {
      await stop();
    } finally {
      await context.close();
    }
  }
  expect(events).toEqual(["two listings pending", "first listing finished", "both handlers drained", "context closed"]);
});

test("drain an outstanding forward after page navigation", async ({ browser, backend }) => {
  const context = await browser.newContext({ baseURL: backend.url });
  const stop = await installApiForwarding(context, backend.url);
  const page = await context.newPage();
  try {
    await page.goto("/");
    await page.evaluate(() => {
      void fetch("/api/v1/queues?search=navigation");
    });
    await backend.waitForListing("navigation");
    await page.goto("/next");
    await expect(page).toHaveURL(`${backend.url}/next`);
    backend.releaseListing("navigation");
    await stop();
    await expect(page).toHaveTitle("Forwarding test");
    expect(backend.requests.filter((path) => path.endsWith("search=navigation"))).toHaveLength(1);
  } finally {
    backend.releaseAll();
    try {
      await stop();
    } finally {
      await context.close();
    }
  }
});

test("preserve query strings and page mock precedence", async ({ page, backend }) => {
  await page.route("**/api/v1/queues?search=mocked", (route) => route.fulfill({ json: { mocked: true } }));
  await page.goto(backend.url);
  const forwarded = await page.evaluate(async () => (await fetch("/api/v1/queues?search=forwarded")).json());
  const mocked = await page.evaluate(async () => (await fetch("/api/v1/queues?search=mocked")).json());

  expect(forwarded).toEqual({ path: "/api/v1/queues?search=forwarded" });
  expect(mocked).toEqual({ mocked: true });
  expect(backend.requests).toContain("/api/v1/queues?search=forwarded");
  expect(backend.requests).not.toContain("/api/v1/queues?search=mocked");
});
