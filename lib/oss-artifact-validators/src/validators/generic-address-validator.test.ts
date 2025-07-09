import { GenericAddressValidator } from "./generic-address-validator.js";
import { MockCombinedProvider } from "../providers/mock.js";
import {
  createContractsV0Validator,
  createHybridValidator,
} from "./factory.js";

describe("GenericAddressValidator", () => {
  const TEST_CONTRACT_ADDRESS = "0x5c9849e2e0c2b1c2e6e0e7e0e7e0e7e0e7e0e7e0";
  const TEST_EOA_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";
  const TEST_FACTORY_ADDRESS = "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6";
  const TEST_DEPLOYER_ADDRESS = "0x0ed35b1609ec45c7079e80d11149a52717e4859a";

  describe("with mock providers", () => {
    let validator: GenericAddressValidator;
    let mockProvider: MockCombinedProvider;

    beforeEach(() => {
      mockProvider = new MockCombinedProvider();
      validator = new GenericAddressValidator(
        { mock: mockProvider },
        { mock: mockProvider },
        { expectedNetwork: "ARBITRUM" },
      );
    });

    it("should validate a contract address", async () => {
      mockProvider.setMockContractData(TEST_CONTRACT_ADDRESS, {
        address: TEST_CONTRACT_ADDRESS.toLowerCase(),
        isContract: true,
        exists: true,
        namespaces: ["ARBITRUM"],
        isFactory: false,
        isDeployer: false,
      });

      const result = await validator.validate(TEST_CONTRACT_ADDRESS);

      expect(result.isContract).toBe(true);
      expect(result.exists).toBe(true);
      expect(result.namespaces).toContain("ARBITRUM");
      expect(result.isFactory).toBe(false);
      expect(result.isDeployer).toBe(false);
    });

    it("should validate a factory address", async () => {
      mockProvider.setMockContractData(TEST_FACTORY_ADDRESS, {
        address: TEST_FACTORY_ADDRESS.toLowerCase(),
        isContract: true,
        exists: true,
        namespaces: ["ARBITRUM"],
        isFactory: true,
        isDeployer: false,
      });

      const result = await validator.validate(TEST_FACTORY_ADDRESS);

      expect(result.isContract).toBe(true);
      expect(result.isFactory).toBe(true);
      expect(result.isDeployer).toBe(false);
    });

    it("should validate a deployer address", async () => {
      mockProvider.setMockContractData(TEST_DEPLOYER_ADDRESS, {
        address: TEST_DEPLOYER_ADDRESS.toLowerCase(),
        isContract: false,
        exists: true,
        namespaces: ["ARBITRUM"],
        isFactory: false,
        isDeployer: true,
      });

      const result = await validator.validate(TEST_DEPLOYER_ADDRESS);

      expect(result.isContract).toBe(false);
      expect(result.isFactory).toBe(false);
      expect(result.isDeployer).toBe(true);
    });

    it("should handle non-existent addresses", async () => {
      // Don't set any mock data for this address
      const result = await validator.validate(
        "0x0000000000000000000000000000000000000000",
      );

      expect(result.isContract).toBe(false);
      expect(result.exists).toBe(false);
      expect(result.isFactory).toBe(false);
      expect(result.isDeployer).toBe(false);
    });

    it("should handle ANY_EVM network validation", async () => {
      const anyEvmValidator = new GenericAddressValidator(
        { mock: mockProvider },
        { mock: mockProvider },
        { expectedNetwork: "ANY_EVM" },
      );

      mockProvider.setMockContractData(TEST_CONTRACT_ADDRESS, {
        address: TEST_CONTRACT_ADDRESS.toLowerCase(),
        isContract: true,
        exists: true,
        namespaces: ["ETHEREUM"],
        isFactory: false,
        isDeployer: false,
      });

      const result = await anyEvmValidator.validate(TEST_CONTRACT_ADDRESS);

      expect(result.isContract).toBe(true);
      expect(result.namespaces).toContain("ETHEREUM");
    });

    it("should fallback to address provider when no contract provider", async () => {
      const addressOnlyValidator = new GenericAddressValidator(
        { mock: mockProvider },
        {}, // No contract providers
        { expectedNetwork: "ARBITRUM" },
      );

      mockProvider.setMockAddressData(TEST_EOA_ADDRESS, {
        address: TEST_EOA_ADDRESS.toLowerCase(),
        isContract: false,
        exists: true,
        namespaces: ["ARBITRUM"],
      });

      const result = await addressOnlyValidator.validate(TEST_EOA_ADDRESS);

      expect(result.isContract).toBe(false);
      expect(result.exists).toBe(true);
      expect(result.isFactory).toBe(false);
      expect(result.isDeployer).toBe(false);
    });
  });

  describe("factory functions", () => {
    it("should create a contracts v0 validator", () => {
      const validator = createContractsV0Validator(
        "test-api-key",
        "https://api.example.com/graphql",
        "ARBITRUM",
      );
      expect(validator).toBeDefined();
    });

    it("should create a hybrid validator", () => {
      const validator = createHybridValidator(
        "test-api-key",
        "https://www.opensource.observer/api/v1/graphql",
        "https://rpc.example.com",
        "ARBITRUM",
      );
      expect(validator).toBeDefined();
    });
  });

  describe("provider management", () => {
    it("should allow adding providers dynamically", () => {
      const validator = new GenericAddressValidator();
      const mockProvider = new MockCombinedProvider();

      validator.addAddressProvider("test", mockProvider);
      validator.addContractProvider("test", mockProvider);

      // This is more of a smoke test since the providers are private
      expect(validator).toBeDefined();
    });
  });
});
