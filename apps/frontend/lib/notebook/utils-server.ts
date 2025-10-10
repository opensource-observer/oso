"use server";

import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium-min";
import { NODE_ENV, PUPPETEER_CHROMIUM_PATH } from "@/lib/config";
import { logger } from "@/lib/logger";

export async function tryGenerateNotebookHtml(url: string) {
  try {
    return await generateNotebookHtml(url);
  } catch (error) {
    logger.error("Error rendering page with Puppeteer:", error);
    return null;
  }
}

async function generateNotebookHtml(url: string) {
  const browser = await puppeteer.launch({
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

  const page = await browser.newPage();
  const cssRules: string[] = [];
  await page.goto(url, { timeout: 100 * 1000, waitUntil: "networkidle0" });

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
        if ((window as any).stableStart === undefined) {
          (window as any).stableStart = Date.now();
        }
        return Date.now() - (window as any).stableStart >= 10000;
      } else {
        (window as any).stableStart = undefined;
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
  await browser.close();

  return `
      <style>
        ${cssRules.join("\n")}
      </style>
      ${body}
    `;
}
