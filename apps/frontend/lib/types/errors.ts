/**
 * Explicitly signals that a code path that has not been implemented yet.
 */
export class NotImplementedError extends Error {
  constructor(msg = "Not implemented") {
    super(msg);
  }
}

/**
 * Something is `null` or `undefined` when we don't expect it
 */
export class NullOrUndefinedValueError extends Error {}

/**
 * Unabled to parse a value
 */
export class ParsingError extends Error {}

/**
 * Some value is out of an expected bound
 */
export class OutOfBoundsError extends Error {}

/**
 * Data is malformed
 */
export class InvalidDataError extends Error {}

/**
 * Data is missing
 */
export class MissingDataError extends Error {}

/**
 * Authentication error
 */
export class AuthError extends Error {}
