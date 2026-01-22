import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { Skeleton, SkeletonMeta } from "@/components/ui/skeleton";
import { Button, ButtonMeta } from "@/components/ui/button";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
  AccordionMeta,
  AccordionItemMeta,
  AccordionTriggerMeta,
  AccordionContentMeta,
} from "@/components/ui/accordion";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
  BreadcrumbEllipsis,
  BreadcrumbMeta,
  BreadcrumbListMeta,
  BreadcrumbItemMeta,
  BreadcrumbLinkMeta,
  BreadcrumbPageMeta,
  BreadcrumbSeparatorMeta,
  BreadcrumbEllipsisMeta,
} from "@/components/ui/breadcrumb";
import { Badge, BadgeMeta } from "@/components/ui/badge";
import {
  Alert,
  AlertTitle,
  AlertDescription,
  AlertMeta,
  AlertTitleMeta,
  AlertDescriptionMeta,
} from "@/components/ui/alert";
import { Label, LabelMeta } from "@/components/ui/label";
import { Separator, SeparatorMeta } from "@/components/ui/separator";
import {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
  CommandMeta,
  CommandDialogMeta,
  CommandInputMeta,
  CommandListMeta,
  CommandEmptyMeta,
  CommandGroupMeta,
  CommandItemMeta,
  CommandShortcutMeta,
  CommandSeparatorMeta,
} from "@/components/ui/command";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverAnchor,
  PopoverMeta,
  PopoverTriggerMeta,
  PopoverContentMeta,
  PopoverAnchorMeta,
} from "@/components/ui/popover";
import { Progress, ProgressMeta } from "@/components/ui/progress";
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
import { DataTable, DataTableMeta } from "@/components/ui/data-table";
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
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardMeta,
  CardHeaderMeta,
  CardFooterMeta,
  CardTitleMeta,
  CardDescriptionMeta,
  CardContentMeta,
} from "@/components/ui/card";
import {
  FileInput,
  FileInputButton,
  FileInputButtonMeta,
  FileInputMeta,
} from "@/components/ui/file-input";
import {
  ToggleGroup,
  ToggleGroupItem,
  ToggleGroupMeta,
  ToggleGroupItemMeta,
} from "@/components/ui/toggle-group";
import { Toggle, ToggleMeta } from "@/components/ui/toggle";

export function registerAllUi(PLASMIC: NextJsPlasmicComponentLoader) {
  // shadcn/ui
  PLASMIC.registerComponent(Skeleton, SkeletonMeta);
  PLASMIC.registerComponent(Button, ButtonMeta);
  PLASMIC.registerComponent(Accordion, AccordionMeta);
  PLASMIC.registerComponent(AccordionItem, AccordionItemMeta);
  PLASMIC.registerComponent(AccordionTrigger, AccordionTriggerMeta);
  PLASMIC.registerComponent(AccordionContent, AccordionContentMeta);
  PLASMIC.registerComponent(Breadcrumb, BreadcrumbMeta);
  PLASMIC.registerComponent(BreadcrumbList, BreadcrumbListMeta);
  PLASMIC.registerComponent(BreadcrumbItem, BreadcrumbItemMeta);
  PLASMIC.registerComponent(BreadcrumbLink, BreadcrumbLinkMeta);
  PLASMIC.registerComponent(BreadcrumbPage, BreadcrumbPageMeta);
  PLASMIC.registerComponent(BreadcrumbSeparator, BreadcrumbSeparatorMeta);
  PLASMIC.registerComponent(BreadcrumbEllipsis, BreadcrumbEllipsisMeta);
  PLASMIC.registerComponent(Badge, BadgeMeta);
  PLASMIC.registerComponent(Alert, AlertMeta);
  PLASMIC.registerComponent(AlertTitle, AlertTitleMeta);
  PLASMIC.registerComponent(AlertDescription, AlertDescriptionMeta);
  PLASMIC.registerComponent(Label, LabelMeta);
  PLASMIC.registerComponent(Separator, SeparatorMeta);
  PLASMIC.registerComponent(Command, CommandMeta);
  PLASMIC.registerComponent(CommandDialog, CommandDialogMeta);
  PLASMIC.registerComponent(CommandInput, CommandInputMeta);
  PLASMIC.registerComponent(CommandList, CommandListMeta);
  PLASMIC.registerComponent(CommandEmpty, CommandEmptyMeta);
  PLASMIC.registerComponent(CommandGroup, CommandGroupMeta);
  PLASMIC.registerComponent(CommandItem, CommandItemMeta);
  PLASMIC.registerComponent(CommandShortcut, CommandShortcutMeta);
  PLASMIC.registerComponent(CommandSeparator, CommandSeparatorMeta);
  PLASMIC.registerComponent(Popover, PopoverMeta);
  PLASMIC.registerComponent(PopoverTrigger, PopoverTriggerMeta);
  PLASMIC.registerComponent(PopoverContent, PopoverContentMeta);
  PLASMIC.registerComponent(PopoverAnchor, PopoverAnchorMeta);
  PLASMIC.registerComponent(Progress, ProgressMeta);
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
  PLASMIC.registerComponent(DataTable, DataTableMeta);
  PLASMIC.registerComponent(Select, SelectMeta);
  PLASMIC.registerComponent(SelectGroup, SelectGroupMeta);
  PLASMIC.registerComponent(SelectValue, SelectValueMeta);
  PLASMIC.registerComponent(SelectTrigger, SelectTriggerMeta);
  PLASMIC.registerComponent(SelectContent, SelectContentMeta);
  PLASMIC.registerComponent(SelectLabel, SelectLabelMeta);
  PLASMIC.registerComponent(SelectItem, SelectItemMeta);
  PLASMIC.registerComponent(Input, InputMeta);
  PLASMIC.registerComponent(FileInput, FileInputMeta);
  PLASMIC.registerComponent(FileInputButton, FileInputButtonMeta);
  PLASMIC.registerComponent(Textarea, TextareaMeta);
  PLASMIC.registerComponent(Collapsible, CollapsibleMeta);
  PLASMIC.registerComponent(CollapsibleContent, CollapsibleContentMeta);
  PLASMIC.registerComponent(CollapsibleTrigger, CollapsibleTriggerMeta);
  PLASMIC.registerComponent(Calendar, CalendarMeta);
  PLASMIC.registerComponent(Card, CardMeta);
  PLASMIC.registerComponent(CardHeader, CardHeaderMeta);
  PLASMIC.registerComponent(CardTitle, CardTitleMeta);
  PLASMIC.registerComponent(CardDescription, CardDescriptionMeta);
  PLASMIC.registerComponent(CardContent, CardContentMeta);
  PLASMIC.registerComponent(CardFooter, CardFooterMeta);
  PLASMIC.registerComponent(Toggle, ToggleMeta);
  PLASMIC.registerComponent(ToggleGroup, ToggleGroupMeta);
  PLASMIC.registerComponent(ToggleGroupItem, ToggleGroupItemMeta);
}
