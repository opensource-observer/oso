/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/* prettier-ignore-start */

/** @jsxRuntime classic */
/** @jsx createPlasmicElementProxy */
/** @jsxFrag React.Fragment */

// This class is auto-generated by Plasmic; please do not edit!
// Plasmic Project: 2CtczDeUz9jL9qnFi6NWuQ
// Component: _F-nuwBX0XMK

import * as React from "react";

import {
  Flex as Flex__,
  MultiChoiceArg,
  PlasmicDataSourceContextProvider as PlasmicDataSourceContextProvider__,
  PlasmicIcon as PlasmicIcon__,
  PlasmicImg as PlasmicImg__,
  PlasmicLink as PlasmicLink__,
  PlasmicPageGuard as PlasmicPageGuard__,
  SingleBooleanChoiceArg,
  SingleChoiceArg,
  Stack as Stack__,
  StrictProps,
  Trans as Trans__,
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts,
  ensureGlobalVariants,
  generateOnMutateForSpec,
  generateStateOnChangeProp,
  generateStateOnChangePropForCodeComponents,
  generateStateValueProp,
  get as $stateGet,
  hasVariant,
  initializeCodeComponentStates,
  initializePlasmicStates,
  makeFragment,
  omit,
  pick,
  renderPlasmicSlot,
  set as $stateSet,
  useCurrentUser,
  useDollarState,
  usePlasmicTranslator,
  useTrigger,
  wrapWithClassName,
} from "@plasmicapp/react-web";
import {
  DataCtxReader as DataCtxReader__,
  useDataEnv,
  useGlobalActions,
} from "@plasmicapp/react-web/lib/host";

import "@plasmicapp/react-web/lib/plasmic.css";

import projectcss from "./plasmic.module.css"; // plasmic-import: 2CtczDeUz9jL9qnFi6NWuQ/projectcss
import sty from "./PlasmicLinkCard.module.css"; // plasmic-import: _F-nuwBX0XMK/css

createPlasmicElementProxy;

export type PlasmicLinkCard__VariantMembers = {
  noTitle: "noTitle";
  theme: "dark";
};
export type PlasmicLinkCard__VariantsArgs = {
  noTitle?: SingleBooleanChoiceArg<"noTitle">;
  theme?: SingleChoiceArg<"dark">;
};
type VariantPropType = keyof PlasmicLinkCard__VariantsArgs;
export const PlasmicLinkCard__VariantProps = new Array<VariantPropType>(
  "noTitle",
  "theme",
);

export type PlasmicLinkCard__ArgsType = {
  link?: string;
  image?: React.ReactNode;
  title?: React.ReactNode;
  children?: React.ReactNode;
};
type ArgPropType = keyof PlasmicLinkCard__ArgsType;
export const PlasmicLinkCard__ArgProps = new Array<ArgPropType>(
  "link",
  "image",
  "title",
  "children",
);

export type PlasmicLinkCard__OverridesType = {
  root?: Flex__<"a">;
  icon?: Flex__<"div">;
  header?: Flex__<"div">;
  body?: Flex__<"div">;
};

export interface DefaultLinkCardProps {
  link?: string;
  image?: React.ReactNode;
  title?: React.ReactNode;
  children?: React.ReactNode;
  noTitle?: SingleBooleanChoiceArg<"noTitle">;
  theme?: SingleChoiceArg<"dark">;
  className?: string;
}

const $$ = {};

function PlasmicLinkCard__RenderFunc(props: {
  variants: PlasmicLinkCard__VariantsArgs;
  args: PlasmicLinkCard__ArgsType;
  overrides: PlasmicLinkCard__OverridesType;
  forNode?: string;
}) {
  const { variants, overrides, forNode } = props;

  const args = React.useMemo(
    () =>
      Object.assign(
        {},
        Object.fromEntries(
          Object.entries(props.args).filter(([_, v]) => v !== undefined),
        ),
      ),
    [props.args],
  );

  const $props = {
    ...args,
    ...variants,
  };

  const $ctx = useDataEnv?.() || {};
  const refsRef = React.useRef({});
  const $refs = refsRef.current;

  const stateSpecs: Parameters<typeof useDollarState>[0] = React.useMemo(
    () => [
      {
        path: "noTitle",
        type: "private",
        variableType: "variant",
        initFunc: ({ $props, $state, $queries, $ctx }) => $props.noTitle,
      },
      {
        path: "theme",
        type: "private",
        variableType: "variant",
        initFunc: ({ $props, $state, $queries, $ctx }) => $props.theme,
      },
    ],
    [$props, $ctx, $refs],
  );
  const $state = useDollarState(stateSpecs, {
    $props,
    $ctx,
    $queries: {},
    $refs,
  });

  return (
    <PlasmicLink__
      data-plasmic-name={"root"}
      data-plasmic-override={overrides.root}
      data-plasmic-root={true}
      data-plasmic-for-node={forNode}
      className={classNames(
        projectcss.all,
        projectcss.a,
        projectcss.root_reset,
        projectcss.plasmic_default_styles,
        projectcss.plasmic_mixins,
        projectcss.plasmic_tokens,
        sty.root,
        { [sty.roottheme_dark]: hasVariant($state, "theme", "dark") },
      )}
      href={args.link}
      platform={"react"}
    >
      <div
        data-plasmic-name={"icon"}
        data-plasmic-override={overrides.icon}
        className={classNames(projectcss.all, sty.icon, {
          [sty.iconnoTitle]: hasVariant($state, "noTitle", "noTitle"),
          [sty.icontheme_dark]: hasVariant($state, "theme", "dark"),
        })}
      >
        <div
          className={classNames(projectcss.all, sty.freeBox__nBx8I, {
            [sty.freeBoxnoTitle__nBx8It2Mzw]: hasVariant(
              $state,
              "noTitle",
              "noTitle",
            ),
            [sty.freeBoxtheme_dark__nBx8IGyFc5]: hasVariant(
              $state,
              "theme",
              "dark",
            ),
          })}
        >
          {renderPlasmicSlot({
            defaultContents: (
              <PlasmicImg__
                alt={""}
                className={classNames(sty.img__qJbGi)}
                displayHeight={"50px"}
                displayMaxHeight={"none"}
                displayMaxWidth={"50px"}
                displayMinHeight={"0"}
                displayMinWidth={"0"}
                displayWidth={"auto"}
                loading={"lazy"}
                src={{
                  src: "/plasmic/plasmic/docs_opensource_observer/images/osoIconSvg2.svg",
                  fullWidth: 120,
                  fullHeight: 120,
                  aspectRatio: 1,
                }}
              />
            ),

            value: args.image,
          })}
        </div>
      </div>
      <div
        data-plasmic-name={"header"}
        data-plasmic-override={overrides.header}
        className={classNames(projectcss.all, sty.header, {
          [sty.headernoTitle]: hasVariant($state, "noTitle", "noTitle"),
          [sty.headertheme_dark]: hasVariant($state, "theme", "dark"),
        })}
      >
        <div
          className={classNames(projectcss.all, sty.freeBox__djG7F, {
            [sty.freeBoxnoTitle__djG7Ft2Mzw]: hasVariant(
              $state,
              "noTitle",
              "noTitle",
            ),
            [sty.freeBoxtheme_dark__djG7FGyFc5]: hasVariant(
              $state,
              "theme",
              "dark",
            ),
          })}
        >
          {renderPlasmicSlot({
            defaultContents: "Card title",
            value: args.title,
            className: classNames(sty.slotTargetTitle, {
              [sty.slotTargetTitletheme_dark]: hasVariant(
                $state,
                "theme",
                "dark",
              ),
            }),
          })}
        </div>
      </div>
      <div
        data-plasmic-name={"body"}
        data-plasmic-override={overrides.body}
        className={classNames(projectcss.all, sty.body, {
          [sty.bodynoTitle]: hasVariant($state, "noTitle", "noTitle"),
          [sty.bodytheme_dark]: hasVariant($state, "theme", "dark"),
        })}
      >
        {renderPlasmicSlot({
          defaultContents: (
            <div
              className={classNames(
                projectcss.all,
                projectcss.__wab_text,
                sty.text___2AACg,
              )}
            >
              {"something here"}
            </div>
          ),
          value: args.children,
          className: classNames(sty.slotTargetChildren, {
            [sty.slotTargetChildrentheme_dark]: hasVariant(
              $state,
              "theme",
              "dark",
            ),
          }),
        })}
      </div>
    </PlasmicLink__>
  ) as React.ReactElement | null;
}

const PlasmicDescendants = {
  root: ["root", "icon", "header", "body"],
  icon: ["icon"],
  header: ["header"],
  body: ["body"],
} as const;
type NodeNameType = keyof typeof PlasmicDescendants;
type DescendantsType<T extends NodeNameType> =
  (typeof PlasmicDescendants)[T][number];
type NodeDefaultElementType = {
  root: "a";
  icon: "div";
  header: "div";
  body: "div";
};

type ReservedPropsType = "variants" | "args" | "overrides";
type NodeOverridesType<T extends NodeNameType> = Pick<
  PlasmicLinkCard__OverridesType,
  DescendantsType<T>
>;
type NodeComponentProps<T extends NodeNameType> =
  // Explicitly specify variants, args, and overrides as objects
  {
    variants?: PlasmicLinkCard__VariantsArgs;
    args?: PlasmicLinkCard__ArgsType;
    overrides?: NodeOverridesType<T>;
  } & Omit<PlasmicLinkCard__VariantsArgs, ReservedPropsType> & // Specify variants directly as props
    // Specify args directly as props
    Omit<PlasmicLinkCard__ArgsType, ReservedPropsType> &
    // Specify overrides for each element directly as props
    Omit<
      NodeOverridesType<T>,
      ReservedPropsType | VariantPropType | ArgPropType
    > &
    // Specify props for the root element
    Omit<
      Partial<React.ComponentProps<NodeDefaultElementType[T]>>,
      ReservedPropsType | VariantPropType | ArgPropType | DescendantsType<T>
    >;

function makeNodeComponent<NodeName extends NodeNameType>(nodeName: NodeName) {
  type PropsType = NodeComponentProps<NodeName> & { key?: React.Key };
  const func = function <T extends PropsType>(
    props: T & StrictProps<T, PropsType>,
  ) {
    const { variants, args, overrides } = React.useMemo(
      () =>
        deriveRenderOpts(props, {
          name: nodeName,
          descendantNames: PlasmicDescendants[nodeName],
          internalArgPropNames: PlasmicLinkCard__ArgProps,
          internalVariantPropNames: PlasmicLinkCard__VariantProps,
        }),
      [props, nodeName],
    );
    return PlasmicLinkCard__RenderFunc({
      variants,
      args,
      overrides,
      forNode: nodeName,
    });
  };
  if (nodeName === "root") {
    func.displayName = "PlasmicLinkCard";
  } else {
    func.displayName = `PlasmicLinkCard.${nodeName}`;
  }
  return func;
}

export const PlasmicLinkCard = Object.assign(
  // Top-level PlasmicLinkCard renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    icon: makeNodeComponent("icon"),
    header: makeNodeComponent("header"),
    body: makeNodeComponent("body"),

    // Metadata about props expected for PlasmicLinkCard
    internalVariantProps: PlasmicLinkCard__VariantProps,
    internalArgProps: PlasmicLinkCard__ArgProps,
  },
);

export default PlasmicLinkCard;
/* prettier-ignore-end */
