interface GenericValidator {
  isValid(addr: string): Promise<boolean>;
}

export { GenericValidator };
