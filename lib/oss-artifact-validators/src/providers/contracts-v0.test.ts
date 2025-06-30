import { ContractsV0Provider } from "./contracts-v0.js";
import { jest } from "@jest/globals";

describe("ContractsV0Provider", () => {
  const TEST_CONFIG = {
    osoApiKey: "test-api-key",
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
  };

  const CONTRACT_ADDRESS = "0x5c9849e2e0c2b1c2e6e0e7e0e7e0e7e0e7e0e7e0";
  const DEPLOYER_ADDRESS = "0x0ed35b1609ec45c7079e80d11149a52717e4859a";
  const FACTORY_ADDRESS = "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6";

  let provider: ContractsV0Provider;
  let fetchSpy: jest.SpiedFunction<typeof fetch>;

  beforeEach(() => {
    provider = new ContractsV0Provider(TEST_CONFIG);
    fetchSpy = jest.spyOn(global, "fetch" as any);
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  describe("lookup", () => {
    it("should return contract information when found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: null,
                factoryAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await provider.lookup(CONTRACT_ADDRESS);

      expect(result.address).toBe(CONTRACT_ADDRESS.toLowerCase());
      expect(result.isContract).toBe(true);
      expect(result.exists).toBe(true);
      expect(result.namespaces).toContain("ARBITRUM");
    });

    it("should return empty result when contract not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [] },
        }),
      } as any);

      const result = await provider.lookup(
        "0x0000000000000000000000000000000000000000",
      );

      expect(result.isContract).toBe(false);
      expect(result.exists).toBe(false);
      expect(result.namespaces).toEqual([]);
    });
  });

  describe("contractSummary", () => {
    it("should return complete contract summary", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: DEPLOYER_ADDRESS,
                factoryAddress: FACTORY_ADDRESS,
              },
            ],
          },
        }),
      } as any);

      const result = await provider.contractSummary(CONTRACT_ADDRESS);

      expect(result.isContract).toBe(true);
      expect(result.isFactory).toBe(true);
      expect(result.isDeployer).toBe(true);
      expect(result.namespaces).toContain("ARBITRUM");
    });

    it("should handle contracts without factory/deployer info", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: null,
                factoryAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await provider.contractSummary(CONTRACT_ADDRESS);

      expect(result.isContract).toBe(true);
      expect(result.isFactory).toBe(false);
      expect(result.isDeployer).toBe(false);
    });
  });

  describe("isDeployerOnChain", () => {
    it("should return true when deployer is found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: {
            oso_contractsV0: [{ originatingAddress: DEPLOYER_ADDRESS }],
          },
        }),
      } as any);

      const result = await provider.isDeployerOnChain(
        DEPLOYER_ADDRESS,
        "ARBITRUM",
      );
      expect(result).toBe(true);
    });

    it("should return false when deployer is not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [] },
        }),
      } as any);

      const result = await provider.isDeployerOnChain(
        "0x0000000000000000000000000000000000000000",
        "ARBITRUM",
      );
      expect(result).toBe(false);
    });
  });

  describe("isFactoryOnChain", () => {
    it("should return true when factory is found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: {
            oso_contractsV0: [{ factoryAddress: FACTORY_ADDRESS }],
          },
        }),
      } as any);

      const result = await provider.isFactoryOnChain(
        FACTORY_ADDRESS,
        "ARBITRUM",
      );
      expect(result).toBe(true);
    });

    it("should return false when factory is not found", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({
          data: { oso_contractsV0: [] },
        }),
      } as any);

      const result = await provider.isFactoryOnChain(
        "0x0000000000000000000000000000000000000000",
        "ARBITRUM",
      );
      expect(result).toBe(false);
    });
  });

  describe("API calls", () => {
    it("should make correct API calls with proper headers", async () => {
      fetchSpy.mockResolvedValue({
        json: async () => ({ data: { oso_contractsV0: [] } }),
      } as any);

      await provider.lookup(CONTRACT_ADDRESS);

      expect(fetchSpy).toHaveBeenCalledWith(
        TEST_CONFIG.osoEndpoint,
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${TEST_CONFIG.osoApiKey}`,
          },
          body: expect.stringContaining(CONTRACT_ADDRESS.toLowerCase()),
        }),
      );
    });
  });
});
