import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import dynamic from "next/dynamic";
import { AreaChart } from "@tremor/react";
//import { AlgoliaSearchList } from "./components/widgets/algolia";
import { AlgoliaSearchListMeta } from "@/components/widgets/algolia";
import {
  AuthActions,
  AuthActionsMeta,
} from "@/components/widgets/auth-actions";
import { AuthForm, AuthFormMeta } from "@/components/widgets/auth-form";
import {
  DynamicConnectorForm,
  DynamicConnectorFormMeta,
} from "@/components/widgets/connectors/dynamic-connector-form";
import {
  FeedbackWrapper,
  FeedbackWrapperMeta,
} from "@/components/widgets/feedback-farm";
import { Markdown, MarkdownMeta } from "@/components/widgets/markdown";
import {
  MonacoEditor,
  MonacoEditorMeta,
} from "@/components/widgets/monaco-editor";
import { OsoNavbar, OsoNavbarMeta } from "@/components/widgets/oso-navbar";
import { OsoSidebar, OsoSidebarMeta } from "@/components/widgets/oso-sidebar";
import { OSOChat, OSOChatMeta } from "@/components/widgets/oso-chat";
import {
  SupabaseWrite,
  SupabaseWriteMeta,
} from "@/components/widgets/supabase-write";
import { TallyPopup, TallyPopupMeta } from "@/components/widgets/tally";
import {
  AreaChartMeta,
  BarList,
  BarListMeta,
} from "@/components/widgets/tremor";

export function registerAllWidgets(PLASMIC: NextJsPlasmicComponentLoader) {
  // Widgets
  PLASMIC.registerComponent(
    //AlgoliaSearchList,
    dynamic(() => import("./algolia"), { ssr: false }),
    AlgoliaSearchListMeta,
  );

  PLASMIC.registerComponent(AuthActions, AuthActionsMeta);
  PLASMIC.registerComponent(AuthForm, AuthFormMeta);
  PLASMIC.registerComponent(DynamicConnectorForm, DynamicConnectorFormMeta);
  PLASMIC.registerComponent(FeedbackWrapper, FeedbackWrapperMeta);
  PLASMIC.registerComponent(Markdown, MarkdownMeta);
  PLASMIC.registerComponent(MonacoEditor, MonacoEditorMeta);
  PLASMIC.registerComponent(OsoNavbar, OsoNavbarMeta);
  PLASMIC.registerComponent(OsoSidebar, OsoSidebarMeta);
  PLASMIC.registerComponent(OSOChat, OSOChatMeta);
  PLASMIC.registerComponent(SupabaseWrite, SupabaseWriteMeta);
  PLASMIC.registerComponent(TallyPopup, TallyPopupMeta);
  PLASMIC.registerComponent(BarList, BarListMeta);
  PLASMIC.registerComponent(AreaChart, AreaChartMeta);
}
