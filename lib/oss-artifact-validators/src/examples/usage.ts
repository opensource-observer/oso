/**
 * usage demo for the contract_v0 validator architecture
 */

import {
  createContractsV0Validator,
  createHybridValidator,
  GenericAddressValidator,
  ContractsV0Provider,
  RpcProvider,
  MockCombinedProvider,
} from "../index.js";

// Example 1: Simple contracts v0 validator
export async function basicContractsV0Example() {
  const validator = createContractsV0Validator(
    process.env.OSO_API_KEY || "api-key",
    "https://www.opensource.observer/api/v1/graphql",
    "ARBITRUM",
  );

  const result = await validator.validate(
    "0x1234567890123456789012345678901234567890",
  );
  console.log("Validation result:", result);

  return result;
}

// Example 2: Hybrid validator with contracts v0 and RPC fallback
export async function hybridValidatorExample() {
  const validator = createHybridValidator(
    process.env.OSO_API_KEY || "api-key",
    "https://www.opensource.observer/api/v1/graphql",
    process.env.RPC_URL || "https://arb1.arbitrum.io/rpc",
    "ARBITRUM",
  );

  const addresses = [
    "0x1234567890123456789012345678901234567890", // Contract
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", // EOA
    "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6", // Factory
  ];

  for (const address of addresses) {
    const result = await validator.validate(address);
    console.log(`Address ${address}:`, {
      isContract: result.isContract,
      isFactory: result.isFactory,
      isDeployer: result.isDeployer,
      namespaces: result.namespaces,
    });
  }
}

// Example 3: Custom validator with manual provider setup
export async function customValidatorExample() {
  const validator = new GenericAddressValidator(
    {},
    {},
    {
      expectedNetwork: "ANY_EVM",
    },
  );

  // Add contracts v0 provider
  const contractsProvider = new ContractsV0Provider({
    osoApiKey: process.env.OSO_API_KEY || "api-key",
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
  });
  validator.addContractProvider("contracts-v0", contractsProvider);
  validator.addAddressProvider("contracts-v0", contractsProvider);

  // Add RPC provider as fallback
  const rpcProvider = new RpcProvider({
    rpcUrl: process.env.RPC_URL || "https://eth.llamarpc.com",
  });
  validator.addAddressProvider("rpc", rpcProvider);

  const result = await validator.validate(
    "0x1234567890123456789012345678901234567890",
  );
  return result;
}

// Example 4: Testing with mock providers
export async function testingExample() {
  const mockProvider = new MockCombinedProvider();

  // Setup mock data
  mockProvider.setMockContractData(
    "0x1234567890123456789012345678901234567890",
    {
      address: "0x1234567890123456789012345678901234567890",
      isContract: true,
      exists: true,
      namespaces: ["ARBITRUM"],
      isFactory: true,
      isDeployer: false,
    },
  );

  const validator = new GenericAddressValidator(
    { mock: mockProvider },
    { mock: mockProvider },
    { expectedNetwork: "ARBITRUM" },
  );

  const result = await validator.validate(
    "0x1234567890123456789012345678901234567890",
  );

  console.log("Mock validation result:", result);
  // Expected: isContract: true, isFactory: true, isDeployer: false

  return result;
}

// Example 5: Validating specific artifact types for OSS Directory
export async function ossDirectoryValidationExample() {
  const validator = createContractsV0Validator(
    process.env.OSO_API_KEY || "api-key",
    "https://www.opensource.observer/api/v1/graphql",
    "ARBITRUM", // or "ANY_EVM" for cross-chain artifacts
  );

  const artifacts = [
    {
      address: "0x1234567890123456789012345678901234567890",
      expectedType: "CONTRACT",
    },
    {
      address: "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
      expectedType: "FACTORY",
    },
    {
      address: "0x4df01754ebd055498c8087b1e9a5c7a9ad19b0f6",
      expectedType: "DEPLOYER",
    },
  ];

  const validationResults = [];

  for (const artifact of artifacts) {
    const result = await validator.validate(artifact.address);

    let isValid = false;
    let warning = "";

    switch (artifact.expectedType) {
      case "CONTRACT":
        isValid = result.isContract;
        break;
      case "FACTORY":
        isValid = result.isFactory;
        break;
      case "DEPLOYER":
        isValid = result.isDeployer;
        break;
      case "EOA":
      case "WALLET":
      case "SAFE":
      case "BRIDGE":
        // These types require special handling - issue warning for now
        warning = `⚠️  ${artifact.expectedType} validation not yet implemented for address: ${artifact.address}. Using contracts_v0 endpoint.`;
        isValid = false;
        break;
      default:
        warning = `Unknown artifact type: ${artifact.expectedType}`;
        isValid = false;
    }

    validationResults.push({
      address: artifact.address,
      expectedType: artifact.expectedType,
      isValid,
      warning,
      result,
    });

    if (warning) {
      console.warn(warning);
    }
  }

  return validationResults;
}
