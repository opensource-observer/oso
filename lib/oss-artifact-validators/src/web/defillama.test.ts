import { DefiLlamaValidator } from "./defillama.js";

const DEFILLAMA_API_TIMEOUT = 10000; // 10s

describe("sum module", () => {
  let v: DefiLlamaValidator;
  beforeEach(() => {
    v = new DefiLlamaValidator();
  });

  test("isValidUrl", () => {
    expect(v.isValidUrl("abc")).toBe(false);
    expect(v.isValidUrl("https://www.opensource.observer")).toBe(false);
    expect(v.isValidUrl("https://defillama.com/protocol")).toBe(false);
    expect(v.isValidUrl("https://defillama.com/protocol/")).toBe(false);
    expect(v.isValidUrl("https://defillama.com/protocol/slug")).toBe(true);
    expect(v.isValidUrl("https://defillama.com/protocol/slug/")).toBe(true);
    expect(v.isValidUrl("https://defillama.com/protocol/slug/extra")).toBe(
      false,
    );
  });

  test(
    "isValidSlug",
    async () => {
      expect(await v.isValidSlug("INVALID-SLUG")).toBe(false);
      expect(await v.isValidSlug("uniswap-v3")).toBe(true);
    },
    DEFILLAMA_API_TIMEOUT,
  );

  test(
    "isValid",
    async () => {
      expect(await v.isValid("https://www.opensource.observer")).toBe(false);
      expect(await v.isValid("https://defillama.com/protocol/slug")).toBe(
        false,
      );
      expect(await v.isValid("https://defillama.com/protocol/uniswap-v3")).toBe(
        true,
      );
    },
    DEFILLAMA_API_TIMEOUT,
  );

  test("getSlug", () => {
    expect(v.getSlug("https://defillama.com/protocol/uniswap-v3")).toBe(
      "uniswap-v3",
    );
  });
});
