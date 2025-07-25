import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import Link from "next/link";
import { assertNever } from "@opensource-observer/utils";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuTrigger,
  NavigationMenuContent,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";

type LinkItemData = {
  type: "link";
  title: string;
  href: string;
};
type MenuItemData = {
  type: "menu";
  title: string;
  items: LinkItemData[];
};
type NavBarItem = LinkItemData | MenuItemData;
const DEFAULT_MENU_ITEMS: NavBarItem[] = [
  {
    type: "link",
    title: "Home",
    href: "/",
  },
  {
    type: "menu",
    title: "Overview",
    items: [
      {
        type: "link",
        title: "Homepage",
        href: "/",
      },
      {
        type: "link",
        title: "Why OSO",
        href: "/why-oso",
      },
      {
        type: "link",
        title: "Pricing",
        href: "/test",
      },
    ],
  },
  {
    type: "menu",
    title: "Product",
    items: [
      {
        type: "link",
        title: "Data Marketplace",
        href: "/product/data",
      },
      {
        type: "link",
        title: "Data Integrations",
        href: "/product/integrations",
      },
      {
        type: "link",
        title: "Python SDK",
        href: "/product/pyoso",
      },
      {
        type: "link",
        title: "llmoso AI",
        href: "/product/ai",
      },
      {
        type: "link",
        title: "Developer API",
        href: "/product/api",
      },
      {
        type: "link",
        title: "OSO Terminal",
        href: "/product/terminal",
      },
      {
        type: "link",
        title: "Data Warehouse",
        href: "/product/warehouse",
      },
    ],
  },
  {
    type: "menu",
    title: "Solutions",
    items: [
      {
        type: "link",
        title: "Ecosystem Growth",
        href: "/solutions/ecosystems",
      },
      {
        type: "link",
        title: "Venture Capital",
        href: "/solutions/venture",
      },
      {
        type: "link",
        title: "Reputation Networks",
        href: "/solutions/reputation",
      },
      {
        type: "link",
        title: "Retro Funding",
        href: "/solutions/retrofunding",
      },
      {
        type: "link",
        title: "Politics",
        href: "/solutions/politics",
      },
    ],
  },
  {
    type: "link",
    title: "Docs",
    href: "https://docs.opensource.observer",
  },
];

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
type NavBarProps = {
  className?: string; // Plasmic CSS class
  menuItems?: NavBarItem[]; // Override default menu items
};

const NavbarMeta: CodeComponentMeta<NavBarProps> = {
  name: "MarketingNavbar",
  description: "NavBar for marketing pages",
  props: {
    menuItems: {
      type: "object",
      defaultValue: {},
      helpText: "Override default menu items",
    },
  },
};

function Navbar(props: NavBarProps) {
  const menuItems: NavBarItem[] = props.menuItems ?? DEFAULT_MENU_ITEMS;
  return (
    <NavigationMenu>
      <NavigationMenuList>
        {menuItems.map((item) =>
          item.type === "link" ? (
            <NavigationMenuItem key={item.href}>
              <NavigationMenuLink
                asChild
                className={navigationMenuTriggerStyle()}
              >
                <Link href={item.href}>{item.title}</Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          ) : item.type === "menu" ? (
            <NavigationMenuItem key={item.title}>
              <NavigationMenuTrigger>{item.title}</NavigationMenuTrigger>
              <NavigationMenuContent>
                <ul className="grid w-[300px] gap-4">
                  <li>
                    {item.items.map((listItem) => (
                      <NavigationMenuLink key={listItem.href} asChild>
                        <Link href={listItem.href}>
                          <div className="font-medium">{listItem.title}</div>
                        </Link>
                      </NavigationMenuLink>
                    ))}
                  </li>
                </ul>
              </NavigationMenuContent>
            </NavigationMenuItem>
          ) : (
            assertNever(item)
          ),
        )}
      </NavigationMenuList>
    </NavigationMenu>
  );
}

export { Navbar, NavbarMeta };
