import { test } from "node:test";
import assert from "node:assert/strict";
import { request, ApiError } from "./client.ts";
test("request sends memory token and maps fixed error without disclosing arbitrary response", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (_url, options) => {
    assert.equal(
      new Headers(options?.headers).get("Authorization"),
      "Bearer local-token",
    );
    return new Response(
      JSON.stringify({ error: { code: "stale", message: "Revision changed" } }),
      { status: 409 },
    );
  };
  try {
    await assert.rejects(
      request("local-token", "/config"),
      (error: unknown) =>
        error instanceof ApiError &&
        error.status === 409 &&
        error.message === "Revision changed",
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("unexpected failure bodies get a bounded generic error", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response("secret raw exception", { status: 502 });
  try {
    await assert.rejects(request("token", "/config"), /Request failed \(502\)/);
  } finally {
    globalThis.fetch = original;
  }
});
