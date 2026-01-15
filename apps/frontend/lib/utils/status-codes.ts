export function validStatusCodeOr500(code: number | null | undefined): number {
  if (code && code >= 100 && code <= 599) {
    return code;
  }
  return 500;
}
