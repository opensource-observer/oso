import {
  GenericAddressValidator,
  GenericAddressValidatorConfig,
} from "./generic-address-validator.js";
import {
  ContractsV0Provider,
  ContractsV0Config,
} from "../providers/contracts-v0.js";
import { RpcProvider, RpcConfig } from "../providers/rpc.js";
import { AddressValidator } from "../common/interfaces.js";
import {
  OSSDirectoryValidator,
  OSSDirectoryValidatorConfig,
} from "./oss-directory-validator.js";

export interface ValidatorFactoryConfig {
  contractsV0?: ContractsV0Config;
  rpc?: RpcConfig;
  expectedNetwork?: string;
  timeout?: number; // Timeout in milliseconds, default 15000ms
}

/**
 * Factory function to create a properly configured address validator
 */
export function createAddressValidator(
  config: ValidatorFactoryConfig,
): AddressValidator {
  const validatorConfig: GenericAddressValidatorConfig = {
    expectedNetwork: config.expectedNetwork,
  };

  const validator = new GenericAddressValidator({}, {}, validatorConfig);

  // Add contracts v0 provider
  if (config.contractsV0) {
    const contractsProvider = new ContractsV0Provider({
      ...config.contractsV0,
      timeout: config.timeout || config.contractsV0.timeout,
    });
    validator.addContractProvider("contracts-v0", contractsProvider);
    validator.addAddressProvider("contracts-v0", contractsProvider);
  }

  // Add RPC provider (as fallback)
  if (config.rpc) {
    const rpcProvider = new RpcProvider(config.rpc);
    validator.addAddressProvider("rpc", rpcProvider);
  }

  return validator;
}

/**
 * function to create a validator with just contracts v0 support
 */
export function createContractsV0Validator(
  osoApiKey: string,
  osoEndpoint: string,
  expectedNetwork?: string,
  timeout?: number,
): AddressValidator {
  return createAddressValidator({
    contractsV0: {
      osoApiKey,
      osoEndpoint,
      timeout,
    },
    expectedNetwork,
    timeout,
  });
}

/**
 *  function to create a validator with both contracts v0 and RPC fallback
 */
export function createHybridValidator(
  osoApiKey: string,
  osoEndpoint: string,
  rpcUrl: string,
  expectedNetwork?: string,
): AddressValidator {
  return createAddressValidator({
    contractsV0: {
      osoApiKey,
      osoEndpoint,
    },
    rpc: {
      rpcUrl,
    },
    expectedNetwork,
  });
}

/**
 * Factory function to create an OSS Directory validator
 *  validator for blockchain artifact validation
 */
export function createOSSDirectoryValidator(
  osoApiKey: string,
  osoEndpoint: string,
  expectedNetwork?: string,
  timeout?: number,
): OSSDirectoryValidator {
  return new OSSDirectoryValidator({
    osoApiKey,
    osoEndpoint,
    expectedNetwork,
    timeout,
  });
}
