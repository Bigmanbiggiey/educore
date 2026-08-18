import { afterEach, describe, expect, it, vi } from "vitest";

import { generateCorrelationId } from "./api";

const UUID_V4_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Captured before any stubbing replaces `globalThis.crypto` — the fallback
// test doubles below delegate to this so they still produce real random
// bytes without recursing into themselves.
const realGetRandomValues = globalThis.crypto.getRandomValues.bind(globalThis.crypto);

describe("generateCorrelationId", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("prefers crypto.randomUUID() when available", () => {
    const randomUUID = vi.fn(() => "11111111-1111-4111-8111-111111111111");
    vi.stubGlobal("crypto", { ...globalThis.crypto, randomUUID });

    expect(generateCorrelationId()).toBe("11111111-1111-4111-8111-111111111111");
    expect(randomUUID).toHaveBeenCalledOnce();
  });

  it("falls back to crypto.getRandomValues() when randomUUID is unavailable", () => {
    // Simulates a non-secure-context browser (e.g. staging served over
    // plain HTTP): `randomUUID` is missing but `getRandomValues` still works.
    vi.stubGlobal("crypto", {
      randomUUID: undefined,
      getRandomValues: (arr: Uint8Array) => realGetRandomValues(arr),
    });

    const id = generateCorrelationId();
    expect(id).toMatch(UUID_V4_RE);
  });

  it("produces well-formed, non-repeating IDs via the getRandomValues fallback", () => {
    vi.stubGlobal("crypto", {
      randomUUID: undefined,
      getRandomValues: (arr: Uint8Array) => realGetRandomValues(arr),
    });

    const a = generateCorrelationId();
    const b = generateCorrelationId();
    expect(a).toMatch(UUID_V4_RE);
    expect(b).toMatch(UUID_V4_RE);
    expect(a).not.toBe(b);
  });

  it("falls back to a non-cryptographic UUID when Web Crypto is entirely unavailable", () => {
    vi.stubGlobal("crypto", undefined);

    const id = generateCorrelationId();
    expect(id).toMatch(UUID_V4_RE);
  });
});
