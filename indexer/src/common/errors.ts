export class GenericError extends Error {
  details: Record<string, any>;

  constructor(message: string, details?: Record<string, any>) {
    super(message);
    this.details = details ?? {};
  }

  toJSON(): string {
    return JSON.stringify({ message: this.message, details: this.details });
  }
}
