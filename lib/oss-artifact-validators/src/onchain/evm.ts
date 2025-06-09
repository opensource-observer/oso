import { ContractsValidator } from "./contracts.js";

export interface EVMNetworkValidator {
  isEOA(addr: string): Promise<boolean>;
  isContract(addr: string): Promise<boolean>;
  isFactory(addr: string): Promise<boolean>;
  isDeployer(addr: string): Promise<boolean>;
}

interface GenericEVMNetworkValidatorOptions {
  apiKey: string;
  apiEndpoint?: string;
}

/**
 * In general most EVM networks should be able to inherit directly from this.
 */
export class GenericEVMNetworkValidator implements EVMNetworkValidator {
  private validator: ContractsValidator;

  static create(
    options: GenericEVMNetworkValidatorOptions,
  ): EVMNetworkValidator {
    return new GenericEVMNetworkValidator(options);
  }

  constructor(options: GenericEVMNetworkValidatorOptions) {
    this.validator = new ContractsValidator(
      'ANY_EVM',
      options.apiKey,
      options.apiEndpoint
    );
  }

  async isEOA(addr: string): Promise<boolean> {
    return this.validator.isEOA(addr);
  }

  async isContract(addr: string): Promise<boolean> {
    return this.validator.isContract(addr);
  }

  async isFactory(addr: string): Promise<boolean> {
    return this.validator.isFactory(addr);
  }

  async isDeployer(addr: string): Promise<boolean> {
    return this.validator.isDeployer(addr);
  }
}

export type EthereumOptions = GenericEVMNetworkValidatorOptions;

export function EthereumValidator(options: EthereumOptions) {
  return GenericEVMNetworkValidator.create(
    options
  );
}

export type ArbitrumOptions = GenericEVMNetworkValidatorOptions;

export function ArbitrumValidator(options: ArbitrumOptions) {
  return GenericEVMNetworkValidator.create(
    options
  );
}

export type BaseOptions = GenericEVMNetworkValidatorOptions;

export function BaseValidator(options: BaseOptions) {
  return GenericEVMNetworkValidator.create(
    options
  );
}

export type OptimismOptions = GenericEVMNetworkValidatorOptions;

export function OptimismValidator(options: OptimismOptions) {
  return GenericEVMNetworkValidator.create(
    options
  );
}
