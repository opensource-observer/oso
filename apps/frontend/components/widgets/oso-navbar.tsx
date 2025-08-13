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
        href: "/pricing",
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
type OsoNavbarProps = {
  className?: string; // Plasmic CSS class
  menuItems?: NavBarItem[]; // Override default menu items
};

const OsoNavbarMeta: CodeComponentMeta<OsoNavbarProps> = {
  name: "OsoNavbar",
  description: "shadcn-based NavBar",
  props: {
    menuItems: {
      type: "object",
      helpText: "Override default menu items",
    },
  },
};

function OsoNavbar(props: OsoNavbarProps) {
  const menuItems: NavBarItem[] = props.menuItems ?? DEFAULT_MENU_ITEMS;
  return (
    <NavigationMenu className={props.className}>
      <NavigationMenuList>
        {menuItems.map((item) =>
          item.type === "link" ? (
            <NavigationMenuItem key={item.href}>
              <NavigationMenuLink
                asChild
                className="group inline-flex h-9 w-full items-center justify-center rounded-md bg-transparent px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=open]:text-accent-foreground data-[state=open]:bg-accent/50 data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
              >
                <Link href={item.href}>{item.title}</Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          ) : item.type === "menu" ? (
            <NavigationMenuItem className="relative" key={item.title}>
              <NavigationMenuTrigger className="bg-transparent">
                {item.title}
              </NavigationMenuTrigger>
              <NavigationMenuContent className="absolute top-0 left-100">
                <ul className="w-80 grid grid-cols-1">
                  {item.items.map((listItem) => (
                    <li key={listItem.href}>
                      <NavigationMenuLink
                        className="group inline-flex h-9 w-80 items-center justify-center rounded-md bg-transparent px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=open]:text-accent-foreground data-[state=open]:bg-accent/50 data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
                        asChild
                      >
                        <Link className="w-48" href={listItem.href}>
                          <div className="">{listItem.title}</div>
                        </Link>
                      </NavigationMenuLink>
                    </li>
                  ))}
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

export { OsoNavbar, OsoNavbarMeta };
