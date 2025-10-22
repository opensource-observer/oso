"use server";

import puppeteer, { Browser } from "puppeteer-core";
import chromium from "@sparticuz/chromium-min";
import { NODE_ENV, PUPPETEER_CHROMIUM_PATH } from "@/lib/config";
import { logger } from "@/lib/logger";

export async function tryGenerateNotebookHtml(url: string) {
  const browser = await createBrowserInstance();
  try {
    return await generateNotebookHtml(browser, url);
  } catch (error) {
    logger.error("Error rendering page with Puppeteer:", error);
    return null;
  } finally {
    await browser.close();
  }
}

async function generateNotebookHtml(browser: Browser, url: string) {
  const page = await browser.newPage();
  const cssRules: string[] = [];
  await page.goto(url, { timeout: 10 * 1000, waitUntil: "networkidle0" });

  const previewButton = await page.waitForSelector("[id='preview-button']", {
    timeout: 5000,
  });

  await previewButton?.click();

  // Wait for the interrupt button to have the inactive-button class for at least 10 seconds
  await page.waitForFunction(
    () => {
      const button = document.querySelector('[data-testid="interrupt-button"]');
      const hasInactiveClass = button?.classList.contains("inactive-button");

      if (hasInactiveClass) {
        if (window.stableStart === undefined) {
          window.stableStart = Date.now();
        }
        return Date.now() - window.stableStart >= 10000;
      } else {
        window.stableStart = undefined;
        return false;
      }
    },
    { timeout: 250 * 1000, polling: 100 },
  );

  await new Promise((resolve) => setTimeout(resolve, 5 * 1000));

  cssRules.push(
    ...(await page.evaluate(() => {
      const cssRules: string[] = [];
      Object.values(document.styleSheets).forEach((sheet: CSSStyleSheet) => {
        console.log("processing", sheet);
        Object.values(sheet.cssRules).forEach((rule) => {
          // This will throw a DOMException if the stylesheet is from a different origin
          // and not CORS-enabled. We catch it below.
          try {
            cssRules.push(rule.cssText);
          } catch (e) {
            logger.warn("Could not access rule:", rule, e);
          }
        });
      });
      return cssRules;
    })),
  );
  const body = await page.evaluate(() => {
    const walk = (doc: Element | ShadowRoot) => {
      doc.querySelectorAll("*").forEach((e) => {
        if (e.shadowRoot) {
          e.innerHTML = walk(e.shadowRoot);
        }
      });
      return doc.innerHTML;
    };
    const root = document.querySelector("[id='root']");
    if (!root) {
      return null;
    }
    return walk(root);
  });

  return `
      <style>
        ${cssRules.join("\n")}
      </style>
      ${body}
    `;
}

async function createBrowserInstance() {
  try {
    return await puppeteer.launch({
      args: NODE_ENV === "production" ? chromium.args : puppeteer.defaultArgs(),
      defaultViewport: {
        width: 1280,
        height: 720,
      },
      executablePath:
        NODE_ENV === "production"
          ? await chromium.executablePath(PUPPETEER_CHROMIUM_PATH)
          : PUPPETEER_CHROMIUM_PATH,
      headless: true,
    });
  } catch (error) {
    logger.error("Error launching Puppeteer browser:", error);
    throw error;
  }
}

declare global {
  interface Window {
    stableStart: number | undefined;
  }
}
