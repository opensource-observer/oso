import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import {
  OsoGlobalContext,
  OsoGlobalContextMeta,
} from "@/components/dataprovider/oso-global-context";
import {
  MetricsDataProvider,
  MetricsDataProviderMeta,
} from "@/components/dataprovider/metrics-data-provider";
import {
  SupabaseQuery,
  SupabaseQueryMeta,
} from "@/components/dataprovider/supabase-query";
import {
  AuthRouter,
  AuthRouterMeta,
} from "@/components/dataprovider/auth-router";
import {
  OsoDataProvider,
  OsoDataProviderMeta,
} from "@/components/dataprovider/oso-data-provider";
import {
  OsoChatProvider,
  OsoChatProviderMeta,
} from "@/components/dataprovider/oso-chat-provider";

export function registerAllDataProvider(PLASMIC: NextJsPlasmicComponentLoader) {
  // Global Context
  PLASMIC.registerGlobalContext(OsoGlobalContext, OsoGlobalContextMeta);

  // Data Providers
  PLASMIC.registerComponent(MetricsDataProvider, MetricsDataProviderMeta);
  PLASMIC.registerComponent(SupabaseQuery, SupabaseQueryMeta);
  PLASMIC.registerComponent(OsoDataProvider, OsoDataProviderMeta);
  PLASMIC.registerComponent(AuthRouter, AuthRouterMeta);
  PLASMIC.registerComponent(OsoChatProvider, OsoChatProviderMeta);
}
