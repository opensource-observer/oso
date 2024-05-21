/**
 * Lazy configuration to allow for some configurations to be skipped for library
 * consumers
 */
export interface LazyConfigVariable {
  asString(def: string): string;
  asNumber(def: number): number;
  asBoolean(def: boolean): boolean;
  isEmpty(): boolean;
}

export interface LazyConfig {
  get(name: string): any;
}

export class BaseLazyConfig {}
