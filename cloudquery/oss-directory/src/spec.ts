import { default as Ajv } from "ajv";
import camelcaseKeys from "camelcase-keys";

const spec = {
  type: "object",
  properties: {
    concurrency: { type: "integer" },
    table_suffix: { type: "string" },
  },
};

const ajv = new Ajv.default();
const validate = ajv.compile(spec);

export type Spec = {
  concurrency: number;
  tableSuffix: string;
};

export const parseSpec = (spec: string): Spec => {
  const parsed = JSON.parse(spec) as Partial<Spec>;
  const valid = validate(parsed);
  if (!valid) {
    throw new Error(`Invalid spec: ${JSON.stringify(validate.errors)}`);
  }
  const { concurrency = 10_000, tableSuffix = "_ossd" } = camelcaseKeys(parsed);
  return { concurrency, tableSuffix };
};
