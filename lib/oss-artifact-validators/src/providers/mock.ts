import {
  AddressLookupProvider,
  AddressLookupSummary,
  ContractLookupProvider,
  ContractLookupSummary,
} from "../common/interfaces.js";

/**
 * Mock address lookup provider for testing
 */
export class MockAddressLookupProvider implements AddressLookupProvider {
  private mockData: Map<string, AddressLookupSummary> = new Map();

  setMockData(address: string, data: AddressLookupSummary): void {
    this.mockData.set(address.toLowerCase(), data);
  }

  async lookup(address: string): Promise<AddressLookupSummary> {
    const data = this.mockData.get(address.toLowerCase());
    if (data) {
      return data;
    }

    // Default response for unknown addresses
    return {
      address: address.toLowerCase(),
      isContract: false,
      exists: false,
      namespaces: [],
    };
  }
}

/**
 * Mock contract lookup provider for testing
 */
export class MockContractLookupProvider implements ContractLookupProvider {
  private mockContractData: Map<string, ContractLookupSummary> = new Map();
  private mockDeployerData: Map<string, boolean> = new Map();
  private mockFactoryData: Map<string, boolean> = new Map();

  setMockContractData(address: string, data: ContractLookupSummary): void {
    this.mockContractData.set(address.toLowerCase(), data);
  }

  setMockDeployerData(address: string, isDeployer: boolean): void {
    this.mockDeployerData.set(address.toLowerCase(), isDeployer);
  }

  setMockFactoryData(address: string, isFactory: boolean): void {
    this.mockFactoryData.set(address.toLowerCase(), isFactory);
  }

  async contractSummary(address: string): Promise<ContractLookupSummary> {
    const data = this.mockContractData.get(address.toLowerCase());
    if (data) {
      return data;
    }

    // Default response for unknown addresses
    return {
      address: address.toLowerCase(),
      isContract: false,
      exists: false,
      namespaces: [],
      isFactory: false,
      isDeployer: false,
    };
  }

  async isDeployerOnChain(address: string, _chain: string): Promise<boolean> {
    return this.mockDeployerData.get(address.toLowerCase()) ?? false;
  }

  async isFactoryOnChain(address: string, _chain: string): Promise<boolean> {
    return this.mockFactoryData.get(address.toLowerCase()) ?? false;
  }
}

/**
 * Combined mock provider that implements both interfaces
 */
export class MockCombinedProvider
  implements AddressLookupProvider, ContractLookupProvider
{
  private addressProvider = new MockAddressLookupProvider();
  private contractProvider = new MockContractLookupProvider();

  setMockAddressData(address: string, data: AddressLookupSummary): void {
    this.addressProvider.setMockData(address, data);
  }

  setMockContractData(address: string, data: ContractLookupSummary): void {
    this.contractProvider.setMockContractData(address, data);
  }

  setMockDeployerData(address: string, isDeployer: boolean): void {
    this.contractProvider.setMockDeployerData(address, isDeployer);
  }

  setMockFactoryData(address: string, isFactory: boolean): void {
    this.contractProvider.setMockFactoryData(address, isFactory);
  }

  async lookup(address: string): Promise<AddressLookupSummary> {
    return this.addressProvider.lookup(address);
  }

  async contractSummary(address: string): Promise<ContractLookupSummary> {
    return this.contractProvider.contractSummary(address);
  }

  async isDeployerOnChain(address: string, chain: string): Promise<boolean> {
    return this.contractProvider.isDeployerOnChain(address, chain);
  }

  async isFactoryOnChain(address: string, chain: string): Promise<boolean> {
    return this.contractProvider.isFactoryOnChain(address, chain);
  }
}
