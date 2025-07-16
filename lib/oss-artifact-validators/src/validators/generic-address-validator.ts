import {
  AddressValidator,
  AddressValidationSummary,
  AddressLookupProvider,
  ContractLookupProvider,
} from "../common/interfaces.js";

export interface GenericAddressValidatorConfig {
  expectedNetwork?: string; // e.g. "ARBITRUM", "BASE", "OPTIMISM", "ANY_EVM"
}

/**
 * Generic address validator that uses dependency-injected providers
 */
export class GenericAddressValidator implements AddressValidator {
  private addressLookupProviders: Record<string, AddressLookupProvider>;
  private contractLookupProviders: Record<string, ContractLookupProvider>;
  private config: GenericAddressValidatorConfig;

  constructor(
    addressLookupProviders: Record<string, AddressLookupProvider> = {},
    contractLookupProviders: Record<string, ContractLookupProvider> = {},
    config: GenericAddressValidatorConfig = {},
  ) {
    this.addressLookupProviders = addressLookupProviders;
    this.contractLookupProviders = contractLookupProviders;
    this.config = config;
  }

  async validate(address: string): Promise<AddressValidationSummary> {
    // Try to get detailed contract information first (includes address lookup)
    const contractProvider = this.getFirstContractProvider();
    if (contractProvider) {
      const contractSummary = await contractProvider.contractSummary(address);

      // Check if it's on the expected network
      const isOnExpectedNetwork = this.checkExpectedNetwork(
        contractSummary.namespaces,
      );

      return {
        ...contractSummary,
        // Filter namespaces based on expected network
        namespaces: isOnExpectedNetwork ? contractSummary.namespaces : [],
      };
    }

    // Fallback to basic address lookup
    const addressProvider = this.getFirstAddressProvider();
    if (addressProvider) {
      const addressSummary = await addressProvider.lookup(address);
      const isOnExpectedNetwork = this.checkExpectedNetwork(
        addressSummary.namespaces,
      );

      return {
        ...addressSummary,
        isFactory: false,
        isDeployer: false,
        // Filter namespaces based on expected network
        namespaces: isOnExpectedNetwork ? addressSummary.namespaces : [],
      };
    }

    // No providers available - return minimal validation
    return {
      address: address.toLowerCase(),
      isContract: false,
      exists: false,
      namespaces: [],
      isFactory: false,
      isDeployer: false,
    };
  }

  /**
   * Validates if the address meets network requirements
   */
  private checkExpectedNetwork(namespaces: string[]): boolean {
    if (
      !this.config.expectedNetwork ||
      this.config.expectedNetwork === "ANY_EVM"
    ) {
      return true;
    }
    return namespaces.includes(this.config.expectedNetwork);
  }

  /**
   * Get the first available contract provider
   */
  private getFirstContractProvider(): ContractLookupProvider | null {
    const providers = Object.values(this.contractLookupProviders);
    return providers.length > 0 ? providers[0] : null;
  }

  /**
   * Get the first available address provider
   */
  private getFirstAddressProvider(): AddressLookupProvider | null {
    const providers = Object.values(this.addressLookupProviders);
    return providers.length > 0 ? providers[0] : null;
  }

  /**
   * Add an address lookup provider
   */
  addAddressProvider(name: string, provider: AddressLookupProvider): void {
    this.addressLookupProviders[name] = provider;
  }

  /**
   * Add a contract lookup provider
   */
  addContractProvider(name: string, provider: ContractLookupProvider): void {
    this.contractLookupProviders[name] = provider;
  }
}
