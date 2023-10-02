import { PromisePubSub } from "./pubsub.js";

describe("PromisePubSub", () => {
  it("should pub sub correctly", async () => {
    const ps = new PromisePubSub<number, unknown>();
    const sub0 = ps.sub("test");
    const sub1 = ps.sub("test");
    ps.pub("test", null, 1);
    expect(await Promise.all([sub0, sub1])).toEqual([1, 1]);
  });
});
