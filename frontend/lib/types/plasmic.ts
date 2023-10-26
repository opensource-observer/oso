import { PropType } from "@plasmicapp/loader-nextjs";

export type RegistrationProps<P> = {
  [prop: string]: PropType<P>;
};
