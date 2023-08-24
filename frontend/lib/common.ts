/**
 * Explicitly marks a promise as something we won't await
 * @param _promise
 */
export function spawn(_promise: Promise<any>) {} // eslint-disable-line

/**
 * Explicitly mark that a cast is safe.
 * e.g. `safeCast(x as string[])`.
 */
export function safeCast<T>(x: T): T {
  return x;
}
