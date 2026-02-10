export class Table {
  private _catalog: string;
  private _dataset: string;
  private _table: string;

  constructor(catalog: string, dataset: string, table: string) {
    this._catalog = catalog;
    this._dataset = dataset;
    this._table = table;
  }

  public static fromString(tableString: string): Table {
    const parts = tableString.split(".");
    if (parts.length > 3) {
      throw new Error(
        `Invalid table string format: ${tableString}. Expected format: catalog.dataset.table, dataset.table, or table`,
      );
    }
    if (parts.length === 3) {
      const [catalog, dataset, table] = parts;
      return new Table(catalog, dataset, table);
    } else if (parts.length === 2) {
      const [dataset, table] = parts;
      return new Table("", dataset, table);
    }
    return new Table("", "", parts[0]);
  }

  isFQN(): boolean {
    return this._catalog !== "" && this._dataset !== "";
  }

  get catalog(): string {
    return this._catalog;
  }

  get dataset(): string {
    return this._dataset;
  }

  get table(): string {
    return this._table;
  }

  toFQN(): string {
    if (!this.isFQN()) {
      throw new Error("Table is not fully qualified");
    }
    return `${this._catalog}.${this._dataset}.${this._table}`;
  }

  toString(): string {
    if (this._catalog && this._dataset) {
      return `${this._catalog}.${this._dataset}.${this._table}`;
    } else if (this._dataset) {
      return `${this._dataset}.${this._table}`;
    }
    return this._table;
  }
}
