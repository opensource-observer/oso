import { RequestDocument, Variables } from "graphql-request";
import { jsonToGraphQLQuery, VariableType } from "json-to-graphql-query";
import _ from "lodash";

const varTypeMap = {
  String: (i: any) => {
    return i as string;
  },
  "String!": (i: any) => {
    return i as string;
  },
  Int: (i: any) => {
    return i as string;
  },
  "Int!": (i: any) => {
    return i as string;
  },
  PreciseDateTime: (i: any) => {
    const d = i as Date;
    return d.toUTCString();
  },
  "PreciseDateTime!": (i: any) => {
    const d = i as Date;
    return d.toUTCString();
  },
  GitTimestamp: (i: any) => {
    const d = i as Date;
    return d.toUTCString();
  },
  "GitTimestamp!": (i: any) => {
    const d = i as Date;
    return d.toUTCString();
  },
};

export type MultiplexVarType = keyof typeof varTypeMap;

export type MultiplexInputMapping<Input extends object> = Record<
  keyof Input,
  VariableType
>;
export type MultiplexObjectRetreiverResponse = {
  type: string;
  definition: object;
};
export type MultiplexObjectRetreiver<Input extends object> = (
  vars: MultiplexInputMapping<Input>,
) => MultiplexObjectRetreiverResponse;
export type MultiplexRequestResponse<
  R extends { [key: string]: Response },
  Response,
> = {
  raw: R;
  items: Response[];
};

/*
 * This class allows us to make requests for multiple object lookups items given a
 * specific template.
 */
export class MultiplexGithubGraphQLRequester<Input extends object, Response> {
  private retreiver: MultiplexObjectRetreiver<Input>;
  private variableDef: Record<keyof Input, MultiplexVarType>;
  private name: string;

  constructor(
    name: string,
    variableDef: Record<keyof Input, MultiplexVarType>,
    objectRetreiver: MultiplexObjectRetreiver<Input>,
  ) {
    this.name = name;
    this.variableDef = variableDef;
    this.retreiver = objectRetreiver;
  }

  async request<R extends { [key: string]: Response }>(
    inputs: Input[],
    requester: (r: RequestDocument, v: Variables) => Promise<R>,
  ): Promise<MultiplexRequestResponse<R, Response>> {
    const req = this.makeRequest(inputs);
    const res = await requester(req.graphql, req.variables);

    const items: Response[] = inputs.map((_n, index) => {
      return res[`response${index}`];
    });

    return {
      raw: res,
      items: items,
    };
  }

  makeRequest(inputs: Input[]): {
    graphql: string;
    variables: Record<string, any>;
  } {
    if (inputs.length === 0) {
      throw new Error("need inputs");
    }
    const keys = Object.keys(inputs[0]) as (keyof Input)[];
    let index = 0;

    const query = {
      query: {
        __name: this.name,
        __variables: {},
        rateLimit: {
          limit: true,
          cost: true,
          remaining: true,
          resetAt: true,
        },
      },
    };

    let varDefs = {};
    let inputVars: Record<string, any> = {};

    for (const input of inputs) {
      const currentVarName = (c: keyof Input) => {
        return `${c as string}${index}`;
      };
      const currentVarDefs = keys.reduce<Record<string, string>>((a, c) => {
        a[currentVarName(c)] = this.variableDef[c];
        return a;
      }, {});

      // Add variable definitions
      varDefs = _.merge(varDefs, currentVarDefs);

      const mapping = keys.reduce<MultiplexInputMapping<Input>>((a, c) => {
        a[c] = new VariableType(currentVarName(c));
        return a;
      }, {} as MultiplexInputMapping<Input>);

      const currentInputVars = keys.reduce<Record<string, any>>((a, c) => {
        a[currentVarName(c)] = input[c];
        return a;
      }, {});
      inputVars = _.merge(inputVars, currentInputVars);

      const resp = this.retreiver(mapping);
      const definition = _.merge(resp.definition, { __aliasFor: resp.type });

      const queryAddition: Record<string, any> = {};
      queryAddition[`response${index}`] = definition;
      query.query = _.merge(query.query, queryAddition);

      index += 1;
    }

    query.query.__variables = _.merge(query.query.__variables, varDefs);

    return {
      graphql: jsonToGraphQLQuery(query, { pretty: true }),
      variables: inputVars,
    };
  }
}
