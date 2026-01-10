export interface Context<T> {
  enter(): Promise<T>;
  exit(): Promise<void>;
}

/**
 * Allows us to use a simple context manager pattern similar to python's `with`
 * statement. For some reason the `using` keyword in TS is not working as
 * expected with our current setup.
 *
 * @param context
 * @param fn
 * @returns
 */
export async function withContext<T, R>(
  context: Context<T>,
  fn: (ctxValue: T) => Promise<R>,
): Promise<R> {
  const ctxValue = await context.enter();
  try {
    return await fn(ctxValue);
  } finally {
    await context.exit();
  }
}
