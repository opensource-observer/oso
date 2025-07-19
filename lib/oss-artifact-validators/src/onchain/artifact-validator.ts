import { ContractsV0Validator } from "./contracts-v0.js";

export type ArtifactType =
  | "CONTRACT"
  | "FACTORY"
  | "DEPLOYER"
  | "EOA"
  | "WALLET"
  | "SAFE"
  | "BRIDGE";

export interface ArtifactValidationOptions {
  contractNamespace?: string;
  apiUrl?: string;
}

export interface ArtifactValidationResult {
  isValid: boolean;
  warnings: string[];
  errors: string[];
}

type ValidatorMethod = (address: string) => Promise<boolean>;

interface ArtifactHandler {
  validator?: ValidatorMethod;
  warning?: string;
}

export class ArtifactValidator {
  private readonly validator: ContractsV0Validator;
  private readonly artifactHandlers: Record<ArtifactType, ArtifactHandler>;

  constructor(options: ArtifactValidationOptions = {}) {
    this.validator = new ContractsV0Validator({
      apiUrl: options.apiUrl,
      contractNamespace: options.contractNamespace,
    });

    this.artifactHandlers = {
      CONTRACT: { validator: this.validator.isContract.bind(this.validator) },
      FACTORY: { validator: this.validator.isFactory.bind(this.validator) },
      DEPLOYER: { validator: this.validator.isDeployer.bind(this.validator) },
      EOA: {
        warning:
          "EOA validation is not supported by contracts_v0 endpoint. Please verify manually.",
      },
      WALLET: {
        warning:
          "WALLET validation is not supported by contracts_v0 endpoint. Please verify manually.",
      },
      SAFE: {
        warning:
          "SAFE validation is not supported by contracts_v0 endpoint. Please verify manually.",
      },
      BRIDGE: {
        warning:
          "BRIDGE validation is not supported by contracts_v0 endpoint. Please verify manually.",
      },
    };
  }

  async validateArtifact(
    address: string,
    artifactType: ArtifactType,
  ): Promise<ArtifactValidationResult> {
    const handler = this.artifactHandlers[artifactType];

    if (!handler) {
      return {
        isValid: false,
        warnings: [],
        errors: [`Unknown artifact type: ${artifactType}`],
      };
    }

    if (handler.warning) {
      return {
        isValid: false,
        warnings: [handler.warning],
        errors: [],
      };
    }

    if (!handler.validator) {
      return {
        isValid: false,
        warnings: [],
        errors: [`No validator available for artifact type: ${artifactType}`],
      };
    }

    try {
      const isValid = await handler.validator(address);
      return {
        isValid,
        warnings: [],
        errors: [],
      };
    } catch (error) {
      return {
        isValid: false,
        warnings: [],
        errors: [
          `Error validating artifact: ${error instanceof Error ? error.message : String(error)}`,
        ],
      };
    }
  }

  static create = (network?: string): ArtifactValidator => {
    const contractNamespace =
      network && network !== "ANY_EVM" ? network : undefined;

    return new ArtifactValidator({
      contractNamespace,
    });
  };
}

export const validateBlockchainArtifact = (
  address: string,
  artifactType: ArtifactType,
  network?: string,
): Promise<ArtifactValidationResult> =>
  ArtifactValidator.create(network).validateArtifact(address, artifactType);
