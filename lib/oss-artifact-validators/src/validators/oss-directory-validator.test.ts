import { OSSDirectoryValidator } from "./oss-directory-validator.js";
import { jest } from "@jest/globals";
import * as dotenv from "dotenv";

dotenv.config();

describe("OSSDirectoryValidator", () => {
  const TEST_CONFIG = {
    osoApiKey: process.env.OSO_API_KEY as string,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    timeout: 20000,
  };

  const CONTRACT_ADDRESS = "0x5c9849e2e0c2b1c2e6e0e7e0e7e0e7e0e7e0e7e0";
  const DEPLOYER_ADDRESS = "0x0ed35b1609ec45c7079e80d11149a52717e4859a";
  const FACTORY_ADDRESS = "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6";
  const UNKNOWN_ADDRESS = "0x0000000000000000000000000000000000000000";

  let validator: OSSDirectoryValidator;
  let fetchSpy: jest.SpiedFunction<typeof fetch>;

  beforeEach(() => {
    validator = new OSSDirectoryValidator(TEST_CONFIG);
    fetchSpy = jest.spyOn(global, "fetch" as any);
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  describe("validateArtifact", () => {
    it("should validate CONTRACT type correctly", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: null,
                rootDeployerAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await validator.validateArtifact(
        CONTRACT_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(true);
      expect(result.expectedType).toBe("CONTRACT");
      expect(result.validationSummary.isContract).toBe(true);
      expect(result.validationSummary.namespaces).toContain("ARBITRUM");
      expect(result.warning).toBeUndefined();
    }, 20000);

    it("should validate FACTORY type correctly", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: FACTORY_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: null,
                rootDeployerAddress: FACTORY_ADDRESS,
              },
            ],
          },
        }),
      } as any);

      const result = await validator.validateArtifact(
        FACTORY_ADDRESS,
        "FACTORY",
      );

      expect(result.isValid).toBe(true);
      expect(result.expectedType).toBe("FACTORY");
      expect(result.validationSummary.isFactory).toBe(true);
      expect(result.warning).toBeUndefined();
    }, 20000);

    it("should validate DEPLOYER type correctly", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: DEPLOYER_ADDRESS,
                rootDeployerAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await validator.validateArtifact(
        DEPLOYER_ADDRESS,
        "DEPLOYER",
      );

      expect(result.isValid).toBe(true);
      expect(result.expectedType).toBe("DEPLOYER");
      expect(result.validationSummary.isDeployer).toBe(true);
      expect(result.warning).toBeUndefined();
    }, 20000);

    it("should handle unknown addresses", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: { oso_contractsV0: [] },
        }),
      } as any);

      const result = await validator.validateArtifact(
        UNKNOWN_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(false);
      expect(result.validationSummary.exists).toBe(false);
      expect(result.validationSummary.isContract).toBe(false);
    }, 20000);

    it("should handle unsupported artifact types with warnings", async () => {
      const result = await validator.validateArtifact(CONTRACT_ADDRESS, "EOA");

      expect(result.isValid).toBe(false);
      expect(result.warning).toContain("EOA validation not yet implemented");
    }, 20000);

    it("should handle unknown artifact types", async () => {
      const result = await validator.validateArtifact(
        CONTRACT_ADDRESS,
        "UNKNOWN_TYPE",
      );

      expect(result.isValid).toBe(false);
      expect(result.warning).toContain("Unknown artifact type: UNKNOWN_TYPE");
    }, 20000);
  });

  describe("network validation", () => {
    it("should validate against specific network", async () => {
      const networkValidator = new OSSDirectoryValidator({
        ...TEST_CONFIG,
        expectedNetwork: "ARBITRUM",
      });

      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ETHEREUM", // Wrong network
                originatingAddress: null,
                rootDeployerAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await networkValidator.validateArtifact(
        CONTRACT_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(false); // Should fail because it's on ETHEREUM, not ARBITRUM
    }, 20000);

    it("should accept ANY_EVM network", async () => {
      const anyEvmValidator = new OSSDirectoryValidator({
        ...TEST_CONFIG,
        expectedNetwork: "ANY_EVM",
      });

      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "POLYGON", // Any EVM network should be accepted
                originatingAddress: null,
                rootDeployerAddress: null,
              },
            ],
          },
        }),
      } as any);

      const result = await anyEvmValidator.validateArtifact(
        CONTRACT_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(true);
    }, 20000);
  });

  describe("validateArtifacts", () => {
    it("should validate multiple artifacts", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            oso_contractsV0: [
              {
                contractAddress: CONTRACT_ADDRESS,
                contractNamespace: "ARBITRUM",
                originatingAddress: null,
                rootDeployerAddress: null,
              },
            ],
          },
        }),
      } as any);

      const artifacts = [
        { address: CONTRACT_ADDRESS, expectedType: "CONTRACT" },
        { address: UNKNOWN_ADDRESS, expectedType: "FACTORY" },
      ];

      const results = await validator.validateArtifacts(artifacts);

      expect(results).toHaveLength(2);
      expect(results[0].isValid).toBe(true);
      expect(results[1].isValid).toBe(false);
    }, 20000);
  });

  describe("getContractsProvider", () => {
    it("should return the contracts provider", () => {
      const provider = validator.getContractsProvider();
      expect(provider).toBeDefined();
      expect(typeof provider.contractSummary).toBe("function");
    });
  });

  describe("timeout handling", () => {
    it("should handle timeout errors gracefully", async () => {
      fetchSpy.mockImplementation(() => {
        return new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error("Request timeout after 20000ms"));
          }, 100);
        });
      });

      const result = await validator.validateArtifact(
        CONTRACT_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(false);
      expect(result.warning).toContain(
        "API Error: Contracts v0 API request failed: Request timeout after 20000ms",
      );
      expect(result.validationSummary.exists).toBe(false);
    }, 20000);

    it("should handle network errors gracefully", async () => {
      fetchSpy.mockRejectedValue(new Error("Network error"));

      const result = await validator.validateArtifact(
        CONTRACT_ADDRESS,
        "CONTRACT",
      );

      expect(result.isValid).toBe(false);
      expect(result.warning).toContain(
        "API Error: Contracts v0 API request failed: Network error",
      );
      expect(result.validationSummary.exists).toBe(false);
    }, 20000);
  });

  describe("real endpoint integration", () => {
    it("should work with real contracts v0 endpoint", async () => {
      if (!process.env.OSO_API_KEY) {
        console.log("Skipping real endpoint test - OSO_API_KEY not set");
        return;
      }

      const realValidator = new OSSDirectoryValidator({
        osoApiKey: process.env.OSO_API_KEY,
        osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
        timeout: 30000, // Increased timeout for real API calls
      });

      // Test with a known contract address from your curl example
      const result = await realValidator.validateArtifact(
        "0x8f7dab4508d792416a1c4911464613299642952a",
        "CONTRACT",
      );

      expect(result).toBeDefined();
      expect(typeof result.isValid).toBe("boolean");
      expect(typeof result.validationSummary).toBe("object");

      console.log("Real endpoint test result:", {
        address: result.address,
        isValid: result.isValid,
        namespaces: result.validationSummary.namespaces,
        warning: result.warning,
      });

      // Don't fail the test if we get a 504 - just log it
      if (result.warning && result.warning.includes("504")) {
        console.log(
          "Note: Got 504 Gateway Timeout - this might be a temporary API issue",
        );
      }
    }, 30000); // Extended timeout for real API call
  });
});
