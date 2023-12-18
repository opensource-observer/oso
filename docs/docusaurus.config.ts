import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "Open Source Observer",
  tagline: "Measure impact on your platform.",
  favicon: "img/oso-emblem-black.svg",

  url: "https://docs.opensource.observer",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "opensource-observer", // Usually your GitHub org/user name.
  projectName: "oso", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  onDuplicateRoutes: "throw",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          editUrl: "https://github.com/opensource-observer/oso/tree/main/docs/",
        },
        blog: {
          showReadingTime: true,
          editUrl: "https://github.com/opensource-observer/oso/tree/main/docs/",
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/oso-primary-black.png",
    navbar: {
      title: "Open Source Observer",
      logo: {
        alt: "OSO Logo",
        src: "img/oso-emblem-black.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "mainSidebar",
          position: "left",
          label: "Docs",
        },
        {
          to: "/blog",
          label: "Blog",
          position: "left",
        },
        {
          href: "https://www.opensource.observer",
          label: "Website",
          position: "left",
        },
        {
          href: "https://github.com/opensource-observer/oso",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [
            {
              label: "Contributing",
              to: "/docs/contributing/intro",
            },
            {
              label: "Data",
              to: "/docs/data/intro",
            },
            {
              label: "API",
              to: "/docs/api/intro",
            },
            {
              label: "Impact Metrics",
              to: "/docs/metrics/intro",
            },
            {
              label: "Ecosystems",
              to: "/docs/ecosystems/intro",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Twitter",
              href: "https://twitter.com/OSObserver",
            },
            {
              label: "Telegram",
              href: "https://t.me/opensourceobserver",
            },
            {
              label: "Discord",
              href: "https://www.opensource.observer/discord",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "Blog",
              to: "/blog",
            },
            {
              label: "Website",
              href: "https://www.opensource.observer",
            },
            {
              label: "GitHub",
              href: "https://github.com/opensource-observer/oso",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Kariba Labs, Inc.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
