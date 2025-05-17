import { PropType, CodeComponentMeta } from "@plasmicapp/loader-nextjs";

export type RegistrationProps<P> = {
  [prop: string]: PropType<P>;
};

export type RegistrationRefActions<P> = CodeComponentMeta<P>["refActions"];
