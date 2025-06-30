export interface AddressLookupSummary {
  address: string;
  isContract: boolean;
  exists: boolean;
  namespaces: string[];
}

export interface ContractLookupSummary extends AddressLookupSummary {
  isFactory: boolean;
  isDeployer: boolean;
  namespaces: string[];
}

// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface AddressValidationSummary {
  address: string;
  isContract: boolean;
  exists: boolean;
  namespaces: string[];
  isFactory: boolean;
  isDeployer: boolean;
  // (Extensible for future validation requirements)
}

// Provider interfaces for dependency injection
export interface AddressLookupProvider {
  lookup(address: string): Promise<AddressLookupSummary>;
}

export interface ContractLookupProvider {
  isDeployerOnChain(address: string, chain: string): Promise<boolean>;
  contractSummary(address: string): Promise<ContractLookupSummary>;
  isFactoryOnChain(address: string, chain: string): Promise<boolean>;
}

// Main validator interface
export interface AddressValidator {
  validate(address: string): Promise<AddressValidationSummary>;
}

interface GenericValidator {
  isValid(addr: string): Promise<boolean>;
}

export { GenericValidator };
