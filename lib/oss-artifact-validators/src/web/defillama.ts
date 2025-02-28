import { GenericValidator } from "../common/interfaces.js";

const DEFILLAMA_URL_PREFIX = "https://defillama.com/protocol/";
const DEFILLAMA_API_PROTOCOLS = "https://api.llama.fi/protocols";

class DefiLlamaValidator implements GenericValidator {
  private _validSlugs: string[];

  constructor() {
    this._validSlugs = [];
  }

  private async _refreshValidSlugs() {
    if (this._validSlugs.length > 0) {
      return;
    }
    const protocolsResult = await fetch(DEFILLAMA_API_PROTOCOLS);
    const protocols = await protocolsResult.json();
    this._validSlugs = protocols
      .map((p: any) => p.slug)
      .filter((s: string) => !!s);
  }

  /**
   * Naive implementation of getting the slug in a DefiLlama URL
   * This can definitely be improved
   * @param url
   * @returns
   */
  getPath(u: string): string {
    const noTrailingSlash = u.endsWith("/") ? u.slice(0, -1) : u;
    const noPrefix = noTrailingSlash.startsWith(DEFILLAMA_URL_PREFIX)
      ? noTrailingSlash.replace(DEFILLAMA_URL_PREFIX, "")
      : noTrailingSlash;
    return noPrefix;
  }

  /**
   * Just check whether the URL is properly formed locally
   */
  isValidUrl(addr: string): boolean {
    if (!addr.startsWith(DEFILLAMA_URL_PREFIX)) {
      //Invalid DefiLlama URL: URLs must begin with ${DEFILLAMA_URL_PREFIX}
      return false;
    }
    const path = this.getPath(addr);
    if (path.includes("/")) {
      //Invalid DefiLlama URL: URL must point to root protocol address
      return false;
    }
    return true;
  }

  /**
   * Check whether the slug is valid by querying the DefiLlama API
   */
  async isValidSlug(slug: string): Promise<boolean> {
    await this._refreshValidSlugs();
    const found = this._validSlugs.find((s: string) => s === slug);
    return !!found;
  }

  /**
   * Checks any arbitrary string to see if it is a valid DefiLlama URL
   * @param addr
   * @returns
   */
  async isValid(addr: string): Promise<boolean> {
    const validUrl = this.isValidUrl(addr);
    const slug = this.getPath(addr);
    const validSlug = await this.isValidSlug(slug);
    return validUrl && validSlug;
  }

  /**
   * Get the slug from a DefiLlama URL
   */
  getSlug(addr: string): string {
    const validUrl = this.isValidUrl(addr);
    if (!validUrl) {
      throw new Error("Invalid DefiLlama URL");
    }
    const slug = this.getPath(addr);
    return slug;
  }
}

export { DefiLlamaValidator };
