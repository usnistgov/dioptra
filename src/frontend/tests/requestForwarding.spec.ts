import { createServer } from "node:http";
import type { AddressInfo } from "node:net";

import { expect, test as base } from "./fixtures/test";

type Backend = {
  url: string;
  requests: string[];
  events: string[];
  listingReceived: Promise<void>;
  releaseListing: () => void;
};

const test = base.extend<object, { backend: Backend }>({
  backend: [
    async ({ browserName: _browserName }, use) => {
      const requests: string[] = [];
      const events: string[] = [];
      let listingStarted!: () => void;
      const listingReceived = new Promise<void>((resolve) => {
        listingStarted = resolve;
      });
      let releaseListing = () => {};
      const server = createServer((request, response) => {
        const path = request.url!;
        requests.push(path);
        if (path === "/api/v1/queues?search=held") {
          events.push("listing requested");
          releaseListing = () => {
            events.push("listing sent");
            response.setHeader("Content-Type", "application/json");
            response.end('{"data":[]}');
          };
          listingStarted();
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

      try {
        await use({ url, requests, events, listingReceived, releaseListing: () => releaseListing() });
        for (let index = 0; index < events.length; index += 6) {
          expect(events.slice(index, index + 6)).toEqual([
            "listing requested",
            "test body finished",
            "cleanup started",
            "listing sent",
            "handlers drained",
            "context closed",
          ]);
        }
      } finally {
        console.log(JSON.stringify({ requests, events }));
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

test("drain an outstanding listing before browser context teardown", async ({ page, context, backend }) => {
  context.on("close", () => backend.events.push("context closed"));

  // Release the held response when fixture cleanup starts, without a timing delay.
  const unrouteAll = context.unrouteAll.bind(context);
  context.unrouteAll = async (options) => {
    backend.events.push("cleanup started");
    const draining = unrouteAll(options);
    backend.releaseListing();
    await draining;
    expect(page.isClosed()).toBe(false);
    backend.events.push("handlers drained");
  };

  await page.goto(backend.url);
  await page.evaluate(() => {
    void fetch("/api/v1/queues?search=held");
  });
  await backend.listingReceived;
  expect(backend.events).toEqual(["listing requested"]);
  backend.events.push("test body finished");
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
