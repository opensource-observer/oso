import {
  AddressValidator,
  AddressValidationSummary,
  ContractLookupProvider,
} from "../common/interfaces.js";
import * as dotenv from "dotenv";
import {
  ContractsV0Provider,
  ContractsV0Config,
} from "../providers/contracts-v0.js";

dotenv.config();

export interface ArtifactValidationResult {
  address: string;
  expectedType: string;
  isValid: boolean;
  warning?: string;
  validationSummary: AddressValidationSummary;
}

export interface OSSDirectoryValidatorConfig {
  osoApiKey: string;
  osoEndpoint: string;
  expectedNetwork?: string; // e.g. "ARBITRUM", "BASE", "OPTIMISM", "ANY_EVM"
  timeout?: number; // Timeout in milliseconds, default 15000ms
}

/**
 * Validator specifically designed for OSS Directory blockchain artifact validation
 * Uses contracts_v0 endpoint for address verification
 */
export class OSSDirectoryValidator {
  private contractsProvider: ContractsV0Provider;
  private expectedNetwork?: string;

  constructor(config: OSSDirectoryValidatorConfig) {
    this.contractsProvider = new ContractsV0Provider({
      osoApiKey: config.osoApiKey,
      osoEndpoint: config.osoEndpoint,
      timeout: config.timeout,
    });
    this.expectedNetwork = config.expectedNetwork;
  }

  /**
   * Validate a single artifact
   */
  async validateArtifact(
    address: string,
    expectedType: string,
  ): Promise<ArtifactValidationResult> {
    let validationSummary;
    let error: string | undefined;

    try {
      validationSummary = await this.contractsProvider.contractSummary(address);
    } catch (err) {
      error = err instanceof Error ? err.message : "Unknown error occurred";
      validationSummary = {
        address: address.toLowerCase(),
        isContract: false,
        exists: false,
        namespaces: [],
        isFactory: false,
        isDeployer: false,
      };
    }

    let isValid = false;
    let warning: string | undefined;

    // If there was an error, mark as invalid and include error message
    if (error) {
      warning = `API Error: ${error}`;
      isValid = false;
    } else {
      switch (expectedType.toUpperCase()) {
        case "CONTRACT":
          isValid =
            validationSummary.isContract &&
            this.isOnExpectedNetwork(validationSummary.namespaces);
          break;
        case "FACTORY":
          isValid =
            validationSummary.isFactory &&
            this.isOnExpectedNetwork(validationSummary.namespaces);
          break;
        case "DEPLOYER":
          isValid =
            validationSummary.isDeployer &&
            this.isOnExpectedNetwork(validationSummary.namespaces);
          break;
        case "EOA":
        case "WALLET":
        case "SAFE":
        case "BRIDGE":
          warning = `⚠️  ${expectedType} validation not yet implemented for address: ${address}. Using contracts_v0 endpoint.`;
          isValid = false;
          break;
        default:
          warning = `Unknown artifact type: ${expectedType}`;
          isValid = false;
      }
    }

    return {
      address,
      expectedType,
      isValid,
      warning,
      validationSummary,
    };
  }

  /**
   * Validate multiple artifacts
   */
  async validateArtifacts(
    artifacts: Array<{ address: string; expectedType: string }>,
  ): Promise<ArtifactValidationResult[]> {
    const results: ArtifactValidationResult[] = [];

    for (const artifact of artifacts) {
      const result = await this.validateArtifact(
        artifact.address,
        artifact.expectedType,
      );
      results.push(result);

      if (result.warning) {
        console.warn(result.warning);
      }
    }

    return results;
  }

  /**
   * Check if the address is on the expected network
   */
  private isOnExpectedNetwork(namespaces: string[]): boolean {
    if (!this.expectedNetwork || this.expectedNetwork === "ANY_EVM") {
      return true;
    }
    return namespaces.includes(this.expectedNetwork);
  }

  /**
   * Get the underlying contracts provider for advanced usage
   */
  getContractsProvider(): ContractLookupProvider {
    return this.contractsProvider;
  }
}
