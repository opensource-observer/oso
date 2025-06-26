import * as evm from "./evm.js";
import { ethers } from "ethers";
import { jest } from "@jest/globals";

describe("evm.ts contracts-v0 logic (unit mock)", () => {
  const TEST_CONFIG = {
    osoApiKey: "test-api-key",
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    expectedNetwork: "ARBITRUM",
    rpcUrl: "http://localhost:8545",
  };
  const CONTRACT_ADDRESS = "0x5c9849e2e0c2b1c2e6e0e7e0e7e0e7e0e7e0e7e0";
  const EOA_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";
  const FACTORY_ADDRESS = "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6";
  const DEPLOYER_ADDRESS = "0x0ed35b1609ec45c7079e80d11149a52717e4859a";

  describe("isContractEthers and isEOA", () => {
    let getCodeSpy: jest.SpiedFunction<(address: string) => Promise<string>>;

    beforeEach(() => {
      getCodeSpy = jest.spyOn(ethers.JsonRpcProvider.prototype, "getCode");
    });

    afterEach(() => {
      getCodeSpy.mockRestore();
    });

    it("should detect contract and EOA correctly", async () => {
      //Each test assertion triggers a new call to getCode,
      // so providing a mock value for each call, in the order they occur.
      // If fewer calls, then after 2 calls, it returns undefined, leading to incorrect test results.
      getCodeSpy
        .mockResolvedValueOnce("0x1234") // isContractEthers(CONTRACT_ADDRESS)
        .mockResolvedValueOnce("0x") // isContractEthers(EOA_ADDRESS)
        .mockResolvedValueOnce("0x") // isEOA(EOA_ADDRESS) -> isContractEthers(EOA_ADDRESS)
        .mockResolvedValueOnce("0x1234"); // isEOA(CONTRACT_ADDRESS) -> isContractEthers(CONTRACT_ADDRESS)

      expect(
        await evm.isContractEthers(CONTRACT_ADDRESS, TEST_CONFIG.rpcUrl),
      ).toBe(true);
      expect(await evm.isContractEthers(EOA_ADDRESS, TEST_CONFIG.rpcUrl)).toBe(
        false,
      );
      expect(await evm.isEOA(EOA_ADDRESS, TEST_CONFIG.rpcUrl)).toBe(true);
      expect(await evm.isEOA(CONTRACT_ADDRESS, TEST_CONFIG.rpcUrl)).toBe(false);
    });
  });

  describe("isContractOnChain", () => {
    let fetchSpy: jest.SpiedFunction<typeof fetch>;
    beforeEach(() => {
      fetchSpy = jest.spyOn(global, "fetch" as any);
    });
    afterEach(() => {
      fetchSpy.mockRestore();
    });
    it("should return true if contract is found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [{ contractAddress: CONTRACT_ADDRESS }] },
        }),
      } as any);
      const result = await evm.isContractOnChain(CONTRACT_ADDRESS, TEST_CONFIG);
      expect(result).toBe(true);
    });
    it("should return false if contract is not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({ data: { oso_contractsV0: [] } }),
      } as any);
      const result = await evm.isContractOnChain(
        "0x0000000000000000000000000000000000000000",
        TEST_CONFIG,
      );
      expect(result).toBe(false);
    });
  });

  describe("isDeployerOnChain", () => {
    let fetchSpy: jest.SpiedFunction<typeof fetch>;
    beforeEach(() => {
      fetchSpy = jest.spyOn(global, "fetch" as any);
    });
    afterEach(() => {
      fetchSpy.mockRestore();
    });
    it("should return true if deployer is found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [{ originatingAddress: DEPLOYER_ADDRESS }] },
        }),
      } as any);
      const result = await evm.isDeployerOnChain(DEPLOYER_ADDRESS, TEST_CONFIG);
      expect(result).toBe(true);
    });
    it("should return false if deployer is not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({ data: { oso_contractsV0: [] } }),
      } as any);
      const result = await evm.isDeployerOnChain(
        "0x0000000000000000000000000000000000000000",
        TEST_CONFIG,
      );
      expect(result).toBe(false);
    });
  });

  describe("isFactoryOnChain", () => {
    let fetchSpy: jest.SpiedFunction<typeof fetch>;
    beforeEach(() => {
      fetchSpy = jest.spyOn(global, "fetch" as any);
    });
    afterEach(() => {
      fetchSpy.mockRestore();
    });
    it("should return true if factory is found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [{ factoryAddress: FACTORY_ADDRESS }] },
        }),
      } as any);
      const result = await evm.isFactoryOnChain(
        FACTORY_ADDRESS,
        TEST_CONFIG,
        "ARBITRUM",
      );
      expect(result).toBe(true);
    });
    it("should return false if factory is not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({ data: { oso_contractsV0: [] } }),
      } as any);
      const result = await evm.isFactoryOnChain(
        "0x0000000000000000000000000000000000000000",
        TEST_CONFIG,
        "ARBITRUM",
      );
      expect(result).toBe(false);
    });
  });

  describe("warnUnsupportedArtifactType", () => {
    it("should warn and return false", async () => {
      const spy = jest.spyOn(console, "warn").mockImplementation(() => {});
      const result = await evm.warnUnsupportedArtifactType(EOA_ADDRESS, "SAFE");
      expect(result).toBe(false);
      expect(spy).toHaveBeenCalledWith(
        expect.stringContaining("SAFE validation not yet implemented"),
      );
      spy.mockRestore();
    });
  });
});
