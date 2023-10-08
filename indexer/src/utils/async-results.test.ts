import { collectAsyncResults } from "./async-results.js";

describe("reducePromises", () => {
  it("should reduce promises", async () => {
    const err2 = new Error("two");
    const err4 = new Error("four");
    const results = await collectAsyncResults<string>([
      Promise.resolve("one"),
      Promise.reject(err2),
      Promise.resolve("three"),
      Promise.reject(err4),
    ]);

    expect(results.errors.length).toEqual(2);
    expect(results.success.length).toEqual(2);
    expect(results.success).toEqual(["one", "three"]);
    expect(results.errors).toEqual([err2, err4]);
  });
});
