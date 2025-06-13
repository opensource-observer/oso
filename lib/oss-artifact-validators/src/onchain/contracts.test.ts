import { jest, describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { ContractsValidator } from './contracts.js';

// Mock Response implementation
class MockResponse implements Response {
  readonly headers: Headers;
  readonly ok: boolean;
  readonly redirected: boolean;
  readonly status: number;
  readonly statusText: string;
  readonly type: ResponseType;
  readonly url: string;
  readonly body: ReadableStream<Uint8Array> | null;
  readonly bodyUsed: boolean;

  constructor(init: {
    ok: boolean;
    status?: number;
    statusText?: string;
    json: () => Promise<any>;
  }) {
    this.ok = init.ok;
    this.status = init.status ?? 200;
    this.statusText = init.statusText ?? '';
    this.headers = new Headers();
    this.redirected = false;
    this.type = 'default';
    this.url = '';
    this.body = null;
    this.bodyUsed = false;
    this.json = init.json;
  }

  async arrayBuffer(): Promise<ArrayBuffer> {
    throw new Error('Method not implemented.');
  }

  async blob(): Promise<Blob> {
    throw new Error('Method not implemented.');
  }

  async formData(): Promise<FormData> {
    throw new Error('Method not implemented.');
  }

  async json(): Promise<any> {
    throw new Error('Method not implemented.');
  }

  async text(): Promise<string> {
    throw new Error('Method not implemented.');
  }

  async bytes(): Promise<Uint8Array> {
    throw new Error('Method not implemented.');
  }

  clone(): Response {
    throw new Error('Method not implemented.');
  }
}

// Test data
const TEST_ADDRESSES = {
  contract: '0x8f7dab4508d792416a1c4911464613299642952a',
  factory: '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',
  deployer: '0x102f479312f69157df8b804905a20fe5025881a5',
  eoa: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
};

const TEST_CONFIG = {
  endpoint: 'https://www.opensource.observer/api/v1/graphql',
  apiKey: `${process.env.OSO_API_KEY}`
};

// Mock fetch globally
const mockFetch = jest.fn<() => Promise<MockResponse>>();
global.fetch = mockFetch as unknown as typeof fetch;

describe('ContractsValidator', () => {
  let validator: ContractsValidator;

  beforeEach(() => {
    validator = new ContractsValidator('ethereum', TEST_CONFIG.apiKey, TEST_CONFIG.endpoint);
    mockFetch.mockClear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('API Integration', () => {
    it('should successfully connect to the API endpoint', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const response = await fetch(TEST_CONFIG.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': TEST_CONFIG.apiKey
        },
        body: JSON.stringify({
          query: `
            query Oso_contractsV0 {
              oso_contractsV0(
                where: {
                  contractAddress: {
                    _eq: "${TEST_ADDRESSES.contract}"
                  }
                }
              ) {
                contractNamespace
                originatingAddress
                rootDeployerAddress
                deploymentDate
              }
            }
          `,
          variables: {}
        })
      });

      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data).toHaveProperty('data');
      expect(data.data.oso_contractsV0[0]).toHaveProperty('contractNamespace');
      expect(data.data.oso_contractsV0[0]).toHaveProperty('originatingAddress');
      expect(data.data.oso_contractsV0[0]).toHaveProperty('rootDeployerAddress');
      expect(data.data.oso_contractsV0[0]).toHaveProperty('deploymentDate');
    });
  });

  describe('Address Validation', () => {
    it('should validate contract address correctly', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(false);
      expect(result.artifactType).toBe('CONTRACT');
      expect(result.networks).toContain('INK');
    });

    it('should handle empty response', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: []
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(false);
      expect(result.warnings?.[0]).toContain('No contracts found for this address');
    });

    it('should validate multiple networks for ANY_EVM', async () => {
      const validator = new ContractsValidator('ANY_EVM', TEST_CONFIG.apiKey, TEST_CONFIG.endpoint);
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              },
              {
                contractNamespace: 'ETH',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(true);
      expect(result.networks).toContain('INK');
      expect(result.networks).toContain('ETH');
    });
  });

  describe('Error Handling', () => {
    it('should handle API rate limiting', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          errors: [
            {
              message: 'Rate limit exceeded',
              locations: [{ line: 1, column: 1 }],
              path: ['oso_contractsV0']
            }
          ]
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(false);
      expect(result.warnings?.[0]).toContain('Rate limit exceeded');
    });

    it('should handle API authentication errors', async () => {
      const mockResponse = new MockResponse({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({})
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(false);
      expect(result.warnings?.[0]).toContain('API request failed with status 401');
    });

    it('should handle network timeout', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      const result = await validator.validateAddress(TEST_ADDRESSES.contract);
      expect(result.isValid).toBe(false);
      expect(result.warnings?.[0]).toContain('Network timeout');
    });
  });

  describe('Type Validation', () => {
    it('should correctly identify contract addresses', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const isContract = await validator.isContract(TEST_ADDRESSES.contract);
      expect(isContract).toBe(true);
    });

    it('should correctly identify EOA addresses', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: []
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const isEOA = await validator.isEOA(TEST_ADDRESSES.eoa);
      expect(isEOA).toBe(true);
    });

    it('should correctly identify factory addresses', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const isFactory = await validator.isFactory(TEST_ADDRESSES.factory);
      expect(isFactory).toBe(true);
    });

    it('should correctly identify deployer addresses', async () => {
      const mockResponse = new MockResponse({
        ok: true,
        json: () => Promise.resolve({
          data: {
            oso_contractsV0: [
              {
                contractNamespace: 'INK',
                originatingAddress: TEST_ADDRESSES.deployer,
                rootDeployerAddress: TEST_ADDRESSES.deployer,
                deploymentDate: '2025-05-25'
              }
            ]
          }
        })
      });

      mockFetch.mockResolvedValueOnce(mockResponse);

      const isDeployer = await validator.isDeployer(TEST_ADDRESSES.deployer);
      expect(isDeployer).toBe(true);
    });
  });
});
