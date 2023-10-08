// Tools for dealing with async coordination

export type PossiblyError = unknown | undefined | null;
export type AsyncResults<T> = {
  success: T[];
  errors: PossiblyError[];
};

export function collectAsyncResults<T>(
  promises: Promise<T>[],
): Promise<AsyncResults<T>> {
  const caughtPromises: Promise<AsyncResults<T>>[] = promises.map((p) => {
    return p
      .then((s: T) => {
        return {
          success: [s],
          errors: [],
        };
      })
      .catch((err) => {
        return {
          success: [],
          errors: [err],
        };
      });
  });

  return Promise.all(caughtPromises).then((results) => {
    return results.reduce<AsyncResults<T>>(
      (acc, result) => {
        acc.errors.push(...result.errors);
        acc.success.push(...result.success);
        return acc;
      },
      {
        errors: [],
        success: [],
      },
    );
  });
}
