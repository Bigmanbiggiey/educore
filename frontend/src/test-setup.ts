import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

// RTL's automatic cleanup-after-each-test relies on detecting a global
// `afterEach` (e.g. from Jest); `vitest.config`'s `test.globals` isn't
// enabled here (kept explicit-import style rather than adding ambient
// globals), so it never registers unless done explicitly — without this,
// every render() in a file accumulates in the DOM instead of being torn
// down between tests.
afterEach(() => {
  cleanup();
});
