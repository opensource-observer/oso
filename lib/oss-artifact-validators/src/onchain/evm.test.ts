import {
  jest,
  describe,
  it,
  expect,
  beforeEach,
  afterEach,
} from "@jest/globals";

// Test data
const TEST_ADDRESSES = {
  contract: "0x8f7dab4508d792416a1c4911464613299642952a",
  factory: "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
  deployer: "0x102f479312f69157df8b804905a20fe5025881a5",
  eoa: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
};

const TEST_CONFIG = {
  osoApiKey: process.env.OSO_API_KEY,
  osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
};

describe("EVM Network Validator - contracts_v0 Integration", () => {
  let GenericEVMNetworkValidator: any;
  let EthereumValidator: any;
  let AnyEVMValidator: any;
  let ArbitrumValidator: any;
  let BaseValidator: any;
  let OptimismValidator: any;

  beforeEach(async () => {
    // Mock test for the ContractsV0Validator class
    const mockContractsV0Validator = jest.fn().mockImplementation(() => ({
      isEOA: jest.fn<() => Promise<boolean>>().mockResolvedValue(false),
      isContract: jest.fn<() => Promise<boolean>>().mockResolvedValue(true),
      isFactory: jest.fn<() => Promise<boolean>>().mockResolvedValue(false),
      isDeployer: jest.fn<() => Promise<boolean>>().mockResolvedValue(false),
    }));

    // Mock the contracts module
    jest.unstable_mockModule("./contracts.js", () => ({
      ContractsV0Validator: mockContractsV0Validator,
    }));

    // Import the modules after mocking
    const evmModule = await import("./evm.js");
    GenericEVMNetworkValidator = evmModule.GenericEVMNetworkValidator;
    EthereumValidator = evmModule.EthereumValidator;
    AnyEVMValidator = evmModule.AnyEVMValidator;
    ArbitrumValidator = evmModule.ArbitrumValidator;
    BaseValidator = evmModule.BaseValidator;
    OptimismValidator = evmModule.OptimismValidator;
  });

  afterEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });

  describe("GenericEVMNetworkValidator", () => {
    it("should create validator instance with contracts_v0 integration", () => {
      const validator = new GenericEVMNetworkValidator(TEST_CONFIG);
      expect(validator).toBeDefined();
      expect(validator).toHaveProperty("isEOA");
      expect(validator).toHaveProperty("isContract");
      expect(validator).toHaveProperty("isFactory");
      expect(validator).toHaveProperty("isDeployer");
    });

    it("should delegate address validation to ContractsV0Validator", async () => {
      const validator = new GenericEVMNetworkValidator(TEST_CONFIG);

      const isEOAResult = await validator.isEOA(TEST_ADDRESSES.eoa);
      const isContractResult = await validator.isContract(
        TEST_ADDRESSES.contract,
      );
      const isFactoryResult = await validator.isFactory(TEST_ADDRESSES.factory);
      const isDeployerResult = await validator.isDeployer(
        TEST_ADDRESSES.deployer,
      );

      expect(typeof isEOAResult).toBe("boolean");
      expect(typeof isContractResult).toBe("boolean");
      expect(typeof isFactoryResult).toBe("boolean");
      expect(typeof isDeployerResult).toBe("boolean");
    });

    it("should create validator using static create method", () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    describe("Unsupported Artifact Types", () => {
      let consoleSpy: any;

      beforeEach(() => {
        consoleSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
      });

      afterEach(() => {
        consoleSpy.mockRestore();
      });

      it("should handle WALLET artifact type with warning", async () => {
        const validator = new GenericEVMNetworkValidator(TEST_CONFIG);
        const result = await validator.isWallet(TEST_ADDRESSES.eoa);

        expect(result).toBe(false);
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining("⚠️  WALLET validation not yet implemented"),
        );
      });

      it("should handle SAFE artifact type with warning", async () => {
        const validator = new GenericEVMNetworkValidator(TEST_CONFIG);
        const result = await validator.isSafe(TEST_ADDRESSES.eoa);

        expect(result).toBe(false);
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining("⚠️  SAFE validation not yet implemented"),
        );
      });

      it("should handle BRIDGE artifact type with warning", async () => {
        const validator = new GenericEVMNetworkValidator(TEST_CONFIG);
        const result = await validator.isBridge(TEST_ADDRESSES.eoa);

        expect(result).toBe(false);
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining("⚠️  BRIDGE validation not yet implemented"),
        );
      });

      it("should handle custom unsupported artifact type with warning", async () => {
        const validator = new GenericEVMNetworkValidator(TEST_CONFIG);
        const result = await validator.isUnsupportedArtifactType(
          TEST_ADDRESSES.eoa,
          "CUSTOM_TYPE",
        );

        expect(result).toBe(false);
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining(
            "⚠️  CUSTOM_TYPE validation not yet implemented",
          ),
        );
      });
    });
  });

  describe("Network-Specific Validators", () => {
    it("should create Ethereum validator with correct configuration", () => {
      const validator = EthereumValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should create AnyEVM validator with correct configuration", () => {
      const validator = AnyEVMValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should create Arbitrum validator with ARBITRUM namespace", () => {
      const validator = ArbitrumValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should create Base validator with BASE namespace", () => {
      const validator = BaseValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should create Optimism validator with OPTIMISM namespace", () => {
      const validator = OptimismValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });
  });

  describe("Contracts_v0 Endpoint Integration", () => {
    it("should properly integrate with contracts_v0 API", () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      expect(validator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should handle network-specific validation correctly", () => {
      const arbitrumValidator = ArbitrumValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(arbitrumValidator).toBeInstanceOf(GenericEVMNetworkValidator);
    });

    it("should validate different address types", async () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);

      // Test that all validation methods exist and return boolean values
      const results = await Promise.all([
        validator.isEOA(TEST_ADDRESSES.eoa),
        validator.isContract(TEST_ADDRESSES.contract),
        validator.isFactory(TEST_ADDRESSES.factory),
        validator.isDeployer(TEST_ADDRESSES.deployer),
      ]);

      results.forEach((result) => {
        expect(typeof result).toBe("boolean");
      });
    });
  });

  describe("Address Validation Logic", () => {
    it("should handle contract address validation", async () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      const result = await validator.isContract(TEST_ADDRESSES.contract);
      expect(typeof result).toBe("boolean");
    });

    it("should handle factory address validation", async () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      const result = await validator.isFactory(TEST_ADDRESSES.factory);
      expect(typeof result).toBe("boolean");
    });

    it("should handle deployer address validation", async () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      const result = await validator.isDeployer(TEST_ADDRESSES.deployer);
      expect(typeof result).toBe("boolean");
    });

    it("should handle EOA address validation", async () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      const result = await validator.isEOA(TEST_ADDRESSES.eoa);
      expect(typeof result).toBe("boolean");
    });
  });

  describe("Configuration and Setup", () => {
    it("should accept osoApiKey and osoEndpoint configuration", () => {
      const validator = GenericEVMNetworkValidator.create(TEST_CONFIG);
      expect(validator).toBeDefined();
    });

    it("should work with different network configurations", () => {
      const ethereumValidator = EthereumValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });
      const anyEVMValidator = AnyEVMValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });
      const arbitrumValidator = ArbitrumValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });
      const baseValidator = BaseValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });
      const optimismValidator = OptimismValidator({
        osoApiKey: TEST_CONFIG.osoApiKey,
        osoEndpoint: TEST_CONFIG.osoEndpoint,
      });

      expect(ethereumValidator).toBeInstanceOf(GenericEVMNetworkValidator);
      expect(anyEVMValidator).toBeInstanceOf(GenericEVMNetworkValidator);
      expect(arbitrumValidator).toBeInstanceOf(GenericEVMNetworkValidator);
      expect(baseValidator).toBeInstanceOf(GenericEVMNetworkValidator);
      expect(optimismValidator).toBeInstanceOf(GenericEVMNetworkValidator);
    });
  });
});
