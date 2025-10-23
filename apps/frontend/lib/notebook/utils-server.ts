"use server";

import puppeteer, { Browser } from "puppeteer-core";
import chromium from "@sparticuz/chromium-min";
import { NODE_ENV, PUPPETEER_CHROMIUM_PATH } from "@/lib/config";
import { logger } from "@/lib/logger";
import { createAdminClient } from "@/lib/supabase/admin";
import { gunzipSync } from "zlib";

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

const LONG_TIMEOUT_MS = 250 * 1000;

async function generateNotebookHtml(browser: Browser, url: string) {
  const page = await browser.newPage();
  const cssRules: string[] = [];
  await page.goto(url, { timeout: 10 * 1000, waitUntil: "networkidle0" });

  logger.info("Page loaded, waiting for spinner...");
  // Wait for the spinner to appear and then disappear
  await page.waitForSelector("[data-testid='large-spinner']", {
    timeout: LONG_TIMEOUT_MS,
  });
  logger.info("Spinner appeared, waiting for it to disappear...");
  await page.waitForSelector("[data-testid='large-spinner']", {
    timeout: LONG_TIMEOUT_MS,
    hidden: true,
  });
  logger.info("Spinner disappeared.");
  const previewButton = await page.waitForSelector("[id='preview-button']", {
    timeout: LONG_TIMEOUT_MS,
  });

  await previewButton?.click();

  logger.info("Clicked preview button, waiting for interrupt button...");
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
    { timeout: LONG_TIMEOUT_MS, polling: 100 },
  );

  await new Promise((resolve) => setTimeout(resolve, 5 * 1000));

  logger.info("Notebook execution appears stable, extracting HTML...");

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
  logger.info("Extracted body HTML, returning result.");

  return `
      <style>
        ${cssRules.join("\n")}
      </style>
      ${body}
    `;
}

export async function getPublishedNotebookByNames(
  orgName: string,
  notebookName: string,
) {
  const supabaseAdmin = createAdminClient();
  const { data, error } = await supabaseAdmin
    .from("published_notebooks")
    .select(
      `
        *,
        notebooks!inner (
          notebook_name,
          organizations!inner (
            org_name
          )
        )
      `,
    )
    .eq("notebooks.notebook_name", notebookName)
    .eq("notebooks.organizations.org_name", orgName)
    .is("deleted_at", null)
    .is("notebooks.deleted_at", null)
    .single();

  if (error) {
    if (error.code !== "PGRST116") {
      logger.error(error);
    }
    return undefined;
  }

  const { notebooks: _, ...publishedNotebookData } = data;

  const { data: blob, error: downloadError } = await supabaseAdmin.storage
    .from("published-notebooks")
    .download(data.data_path);

  if (downloadError) {
    logger.error(downloadError);
    return undefined;
  }

  const html = gunzipSync(await blob.bytes()).toString();

  return {
    ...publishedNotebookData,
    html: html.toString(),
  };
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
