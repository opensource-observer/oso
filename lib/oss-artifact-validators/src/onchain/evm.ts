import { ContractsV0Validator } from "./contracts.js";

export interface EVMNetworkValidator {
  isEOA(addr: string): Promise<boolean>;
  isContract(addr: string): Promise<boolean>;
  isFactory(addr: string): Promise<boolean>;
  isDeployer(addr: string): Promise<boolean>;
}

interface GenericEVMNetworkValidatorOptions {
  osoApiKey: string;
  osoEndpoint: string;
  namespace?: string;
}

/**
 * Enhanced EVM network validator using contracts_v0 endpoint
 * Replaces BigQuery and Alchemy-based validation with OSO's contracts_v0 API
 */
export class GenericEVMNetworkValidator implements EVMNetworkValidator {
  private contractsValidator: ContractsV0Validator;

  static create(
    options: GenericEVMNetworkValidatorOptions,
  ): EVMNetworkValidator {
    return new GenericEVMNetworkValidator(options);
  }

  constructor(options: GenericEVMNetworkValidatorOptions) {
    this.contractsValidator = new ContractsV0Validator(options);
  }

  async isEOA(addr: string): Promise<boolean> {
    return await this.contractsValidator.isEOA(addr);
  }

  async isContract(addr: string): Promise<boolean> {
    return await this.contractsValidator.isContract(addr);
  }

  async isFactory(addr: string): Promise<boolean> {
    return await this.contractsValidator.isFactory(addr);
  }

  async isDeployer(addr: string): Promise<boolean> {
    return await this.contractsValidator.isDeployer(addr);
  }

  /**
   * Warning method for unsupported artifact types
   * @param addr The address to check
   * @param artifactType The unsupported artifact type (WALLET, SAFE, BRIDGE, etc.)
   * @returns Promise that resolves to false with a console warning
   */
  async isUnsupportedArtifactType(
    addr: string,
    artifactType: string,
  ): Promise<boolean> {
    console.warn(
      `⚠️  ${artifactType} validation not yet implemented for address: ${addr}. Using contracts_v0 endpoint.`,
    );
    return false;
  }

  /**
   * Convenience method for WALLET artifact type
   */
  async isWallet(addr: string): Promise<boolean> {
    return this.isUnsupportedArtifactType(addr, "WALLET");
  }

  /**
   * Convenience method for SAFE artifact type
   */
  async isSafe(addr: string): Promise<boolean> {
    return this.isUnsupportedArtifactType(addr, "SAFE");
  }

  /**
   * Convenience method for BRIDGE artifact type
   */
  async isBridge(addr: string): Promise<boolean> {
    return this.isUnsupportedArtifactType(addr, "BRIDGE");
  }
}

export type EthereumOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "namespace"
>;

/**
 * Ethereum validator - validates addresses on Ethereum mainnet
 * Ignores contract_namespace (equivalent to ANY_EVM behavior)
 */
export function EthereumValidator(options: EthereumOptions) {
  return GenericEVMNetworkValidator.create({
    ...options,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    namespace: undefined, // Explicitly ignore namespace for ANY_EVM behavior
  });
}

/**
 * AnyEVM validator - validates addresses across all EVM networks
 * Ignores contract_namespace for cross-chain validation
 */
export function AnyEVMValidator(options: EthereumOptions) {
  return GenericEVMNetworkValidator.create({
    ...options,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    namespace: undefined, // Explicitly ignore namespace for cross-chain validation
  });
}

export type ArbitrumOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "namespace"
>;

/**
 * Arbitrum validator - validates addresses specifically on Arbitrum
 * Uses ARBITRUM namespace for chain-specific validation
 */
export function ArbitrumValidator(options: ArbitrumOptions) {
  return GenericEVMNetworkValidator.create({
    ...options,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    namespace: "ARBITRUM",
  });
}

export type BaseOptions = Omit<GenericEVMNetworkValidatorOptions, "namespace">;

/**
 * Base validator - validates addresses specifically on Base
 * Uses BASE namespace for chain-specific validation
 */
export function BaseValidator(options: BaseOptions) {
  return GenericEVMNetworkValidator.create({
    ...options,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    namespace: "BASE",
  });
}

export type OptimismOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "namespace"
>;

/**
 * Optimism validator - validates addresses specifically on Optimism
 * Uses OPTIMISM namespace for chain-specific validation
 */
export function OptimismValidator(options: OptimismOptions) {
  return GenericEVMNetworkValidator.create({
    ...options,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    namespace: "OPTIMISM",
  });
}
