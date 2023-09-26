export class EntityLookup<T> {
  private storage: Array<T>;
  lookup: Record<string, T>;
  private idFunc: (value: T) => string;

  constructor(idFunc: (value: T) => string) {
    this.storage = [];
    this.lookup = {};
    this.idFunc = idFunc;
  }

  push(item: T) {
    this.storage.push(item);
    this.lookup[this.idFunc(item)] = item;
  }

  has(other: T) {
    return this.hasId(this.idFunc(other));
  }

  hasId(id: string) {
    return this.lookup[id] !== undefined;
  }
}
