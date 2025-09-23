import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { Skeleton, SkeletonMeta } from "@/components/ui/skeleton";
import {
  Sidebar,
  SidebarContent,
  SidebarContentMeta,
  SidebarFooter,
  SidebarFooterMeta,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupActionMeta,
  SidebarGroupContent,
  SidebarGroupContentMeta,
  SidebarGroupLabel,
  SidebarGroupLabelMeta,
  SidebarGroupMeta,
  SidebarHeader,
  SidebarHeaderMeta,
  SidebarInput,
  SidebarInputMeta,
  SidebarInset,
  SidebarInsetMeta,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuActionMeta,
  SidebarMenuBadge,
  SidebarMenuBadgeMeta,
  SidebarMenuButton,
  SidebarMenuButtonMeta,
  SidebarMenuItem,
  SidebarMenuItemMeta,
  SidebarMenuMeta,
  SidebarMenuSkeleton,
  SidebarMenuSkeletonMeta,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubButtonMeta,
  SidebarMenuSubItem,
  SidebarMenuSubItemMeta,
  SidebarMenuSubMeta,
  SidebarMeta,
  SidebarProvider,
  SidebarProviderMeta,
  SidebarRail,
  SidebarRailMeta,
  SidebarSeparator,
  SidebarSeparatorMeta,
  SidebarTrigger,
  SidebarTriggerMeta,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuContentMeta,
  DropdownMenuItem,
  DropdownMenuItemMeta,
  DropdownMenuMeta,
  DropdownMenuTrigger,
  DropdownMenuTriggerMeta,
  DropdownMenuGroup,
  DropdownMenuGroupMeta,
  DropdownMenuPortal,
  DropdownMenuPortalMeta,
  DropdownMenuSub,
  DropdownMenuSubMeta,
  DropdownMenuRadioGroup,
  DropdownMenuRadioGroupMeta,
  DropdownMenuSubTrigger,
  DropdownMenuSubTriggerMeta,
  DropdownMenuSubContent,
  DropdownMenuSubContentMeta,
  DropdownMenuCheckboxItem,
  DropdownMenuCheckboxItemMeta,
  DropdownMenuRadioItem,
  DropdownMenuRadioItemMeta,
  DropdownMenuLabel,
  DropdownMenuLabelMeta,
  DropdownMenuSeparator,
  DropdownMenuSeparatorMeta,
  DropdownMenuShortcut,
  DropdownMenuShortcutMeta,
} from "@/components/ui/dropdown-menu";
import { ToolTip, ToolTipMeta } from "@/components/ui/tooltip";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuContentMeta,
  NavigationMenuIndicator,
  NavigationMenuIndicatorMeta,
  NavigationMenuItem,
  NavigationMenuItemMeta,
  NavigationMenuLink,
  NavigationMenuLinkMeta,
  NavigationMenuList,
  NavigationMenuListMeta,
  NavigationMenuMeta,
  NavigationMenuTrigger,
  NavigationMenuTriggerMeta,
  NavigationMenuViewport,
  NavigationMenuViewportMeta,
} from "@/components/ui/navigation-menu";
import {
  Tabs,
  TabsContent,
  TabsContentMeta,
  TabsList,
  TabsListMeta,
  TabsMeta,
  TabsTrigger,
  TabsTriggerMeta,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableBodyMeta,
  TableCaption,
  TableCaptionMeta,
  TableCell,
  TableCellMeta,
  TableFooter,
  TableFooterMeta,
  TableHead,
  TableHeadMeta,
  TableHeader,
  TableHeaderMeta,
  TableMeta,
  TableRow,
  TableRowMeta,
} from "@/components/ui/table";
import {
  ContextMenu,
  ContextMenuCheckboxItem,
  ContextMenuCheckboxItemMeta,
  ContextMenuContent,
  ContextMenuContentMeta,
  ContextMenuGroup,
  ContextMenuGroupMeta,
  ContextMenuItem,
  ContextMenuItemMeta,
  ContextMenuLabel,
  ContextMenuLabelMeta,
  ContextMenuMeta,
  ContextMenuRadioGroup,
  ContextMenuRadioGroupMeta,
  ContextMenuRadioItem,
  ContextMenuRadioItemMeta,
  ContextMenuSeparator,
  ContextMenuSeparatorMeta,
  ContextMenuShortcut,
  ContextMenuShortcutMeta,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubContentMeta,
  ContextMenuSubMeta,
  ContextMenuSubTrigger,
  ContextMenuSubTriggerMeta,
  ContextMenuTrigger,
  ContextMenuTriggerMeta,
} from "@/components/ui/context-menu";
import {
  Select,
  SelectContent,
  SelectContentMeta,
  SelectGroup,
  SelectGroupMeta,
  SelectItem,
  SelectItemMeta,
  SelectLabel,
  SelectLabelMeta,
  SelectMeta,
  SelectTrigger,
  SelectTriggerMeta,
  SelectValue,
  SelectValueMeta,
} from "@/components/ui/select";
import { Input, InputMeta } from "@/components/ui/input";
import { Textarea, TextareaMeta } from "@/components/ui/textarea";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleContentMeta,
  CollapsibleMeta,
  CollapsibleTrigger,
  CollapsibleTriggerMeta,
} from "@/components/ui/collapsible";
import { Calendar, CalendarMeta } from "@/components/ui/calendar";

export function registerAllUi(PLASMIC: NextJsPlasmicComponentLoader) {
  // shadcn/ui
  PLASMIC.registerComponent(Skeleton, SkeletonMeta);
  PLASMIC.registerComponent(ToolTip, ToolTipMeta);
  PLASMIC.registerComponent(Sidebar, SidebarMeta);
  PLASMIC.registerComponent(SidebarProvider, SidebarProviderMeta);
  PLASMIC.registerComponent(SidebarContent, SidebarContentMeta);
  PLASMIC.registerComponent(SidebarHeader, SidebarHeaderMeta);
  PLASMIC.registerComponent(SidebarFooter, SidebarFooterMeta);
  PLASMIC.registerComponent(SidebarGroup, SidebarGroupMeta);
  PLASMIC.registerComponent(SidebarGroupLabel, SidebarGroupLabelMeta);
  PLASMIC.registerComponent(SidebarGroupContent, SidebarGroupContentMeta);
  PLASMIC.registerComponent(SidebarGroupAction, SidebarGroupActionMeta);
  PLASMIC.registerComponent(SidebarMenu, SidebarMenuMeta);
  PLASMIC.registerComponent(SidebarMenuItem, SidebarMenuItemMeta);
  PLASMIC.registerComponent(SidebarMenuButton, SidebarMenuButtonMeta);
  PLASMIC.registerComponent(SidebarMenuAction, SidebarMenuActionMeta);
  PLASMIC.registerComponent(SidebarMenuBadge, SidebarMenuBadgeMeta);
  PLASMIC.registerComponent(SidebarMenuSkeleton, SidebarMenuSkeletonMeta);
  PLASMIC.registerComponent(SidebarMenuSub, SidebarMenuSubMeta);
  PLASMIC.registerComponent(SidebarMenuSubItem, SidebarMenuSubItemMeta);
  PLASMIC.registerComponent(SidebarMenuSubButton, SidebarMenuSubButtonMeta);
  PLASMIC.registerComponent(SidebarTrigger, SidebarTriggerMeta);
  PLASMIC.registerComponent(SidebarRail, SidebarRailMeta);
  PLASMIC.registerComponent(SidebarInset, SidebarInsetMeta);
  PLASMIC.registerComponent(SidebarInput, SidebarInputMeta);
  PLASMIC.registerComponent(SidebarSeparator, SidebarSeparatorMeta);
  PLASMIC.registerComponent(DropdownMenu, DropdownMenuMeta);
  PLASMIC.registerComponent(DropdownMenuTrigger, DropdownMenuTriggerMeta);
  PLASMIC.registerComponent(DropdownMenuContent, DropdownMenuContentMeta);
  PLASMIC.registerComponent(DropdownMenuItem, DropdownMenuItemMeta);
  PLASMIC.registerComponent(DropdownMenuGroup, DropdownMenuGroupMeta);
  PLASMIC.registerComponent(DropdownMenuPortal, DropdownMenuPortalMeta);
  PLASMIC.registerComponent(DropdownMenuSub, DropdownMenuSubMeta);
  PLASMIC.registerComponent(DropdownMenuRadioGroup, DropdownMenuRadioGroupMeta);
  PLASMIC.registerComponent(DropdownMenuSubTrigger, DropdownMenuSubTriggerMeta);
  PLASMIC.registerComponent(DropdownMenuSubContent, DropdownMenuSubContentMeta);
  PLASMIC.registerComponent(
    DropdownMenuCheckboxItem,
    DropdownMenuCheckboxItemMeta,
  );
  PLASMIC.registerComponent(DropdownMenuRadioItem, DropdownMenuRadioItemMeta);
  PLASMIC.registerComponent(DropdownMenuLabel, DropdownMenuLabelMeta);
  PLASMIC.registerComponent(DropdownMenuSeparator, DropdownMenuSeparatorMeta);
  PLASMIC.registerComponent(DropdownMenuShortcut, DropdownMenuShortcutMeta);
  PLASMIC.registerComponent(NavigationMenu, NavigationMenuMeta);
  PLASMIC.registerComponent(NavigationMenuList, NavigationMenuListMeta);
  PLASMIC.registerComponent(NavigationMenuItem, NavigationMenuItemMeta);
  PLASMIC.registerComponent(NavigationMenuTrigger, NavigationMenuTriggerMeta);
  PLASMIC.registerComponent(NavigationMenuContent, NavigationMenuContentMeta);
  PLASMIC.registerComponent(NavigationMenuLink, NavigationMenuLinkMeta);
  PLASMIC.registerComponent(NavigationMenuViewport, NavigationMenuViewportMeta);
  PLASMIC.registerComponent(
    NavigationMenuIndicator,
    NavigationMenuIndicatorMeta,
  );
  PLASMIC.registerComponent(Tabs, TabsMeta);
  PLASMIC.registerComponent(TabsList, TabsListMeta);
  PLASMIC.registerComponent(TabsTrigger, TabsTriggerMeta);
  PLASMIC.registerComponent(TabsContent, TabsContentMeta);
  PLASMIC.registerComponent(Table, TableMeta);
  PLASMIC.registerComponent(TableHeader, TableHeaderMeta);
  PLASMIC.registerComponent(TableBody, TableBodyMeta);
  PLASMIC.registerComponent(TableFooter, TableFooterMeta);
  PLASMIC.registerComponent(TableRow, TableRowMeta);
  PLASMIC.registerComponent(TableHead, TableHeadMeta);
  PLASMIC.registerComponent(TableCell, TableCellMeta);
  PLASMIC.registerComponent(TableCaption, TableCaptionMeta);
  PLASMIC.registerComponent(ContextMenu, ContextMenuMeta);
  PLASMIC.registerComponent(ContextMenuTrigger, ContextMenuTriggerMeta);
  PLASMIC.registerComponent(ContextMenuContent, ContextMenuContentMeta);
  PLASMIC.registerComponent(ContextMenuItem, ContextMenuItemMeta);
  PLASMIC.registerComponent(
    ContextMenuCheckboxItem,
    ContextMenuCheckboxItemMeta,
  );
  PLASMIC.registerComponent(ContextMenuRadioGroup, ContextMenuRadioGroupMeta);
  PLASMIC.registerComponent(ContextMenuRadioItem, ContextMenuRadioItemMeta);
  PLASMIC.registerComponent(ContextMenuLabel, ContextMenuLabelMeta);
  PLASMIC.registerComponent(ContextMenuSeparator, ContextMenuSeparatorMeta);
  PLASMIC.registerComponent(ContextMenuShortcut, ContextMenuShortcutMeta);
  PLASMIC.registerComponent(ContextMenuGroup, ContextMenuGroupMeta);
  PLASMIC.registerComponent(ContextMenuSub, ContextMenuSubMeta);
  PLASMIC.registerComponent(ContextMenuSubContent, ContextMenuSubContentMeta);
  PLASMIC.registerComponent(ContextMenuSubTrigger, ContextMenuSubTriggerMeta);
  PLASMIC.registerComponent(Select, SelectMeta);
  PLASMIC.registerComponent(SelectGroup, SelectGroupMeta);
  PLASMIC.registerComponent(SelectValue, SelectValueMeta);
  PLASMIC.registerComponent(SelectTrigger, SelectTriggerMeta);
  PLASMIC.registerComponent(SelectContent, SelectContentMeta);
  PLASMIC.registerComponent(SelectLabel, SelectLabelMeta);
  PLASMIC.registerComponent(SelectItem, SelectItemMeta);
  PLASMIC.registerComponent(Input, InputMeta);
  PLASMIC.registerComponent(Textarea, TextareaMeta);
  PLASMIC.registerComponent(Collapsible, CollapsibleMeta);
  PLASMIC.registerComponent(CollapsibleContent, CollapsibleContentMeta);
  PLASMIC.registerComponent(CollapsibleTrigger, CollapsibleTriggerMeta);
  PLASMIC.registerComponent(Calendar, CalendarMeta);
}
