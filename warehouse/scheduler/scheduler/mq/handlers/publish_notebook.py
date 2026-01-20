import base64
import gzip
import json
import urllib.parse

import structlog
from lzstring import LZString
from osoprotobufs.publish_notebook_pb2 import PublishNotebookRunRequest
from playwright.async_api import async_playwright
from scheduler.config import CommonSettings
from scheduler.graphql_client.client import Client
from scheduler.mq.common import RunHandler
from scheduler.types import HandlerResponse, RunContext, SuccessResponse

logger = structlog.getLogger(__name__)

WAIT_JS = """
    () => {
      const spinner = document.querySelector(
        "[data-testid='loading-indicator']",
      );
      const interruptButton = document.querySelector(
        '[data-testid="interrupt-button"]',
      );
      const runButton = document.querySelector('[data-testid="run-button"]');
      const needsToRun = runButton?.classList.contains("yellow");
      const hasInactiveClass =
        interruptButton?.classList.contains("inactive-button");

      if (!hasInactiveClass || spinner || needsToRun) {
        window.stableStart = undefined;
        return false;
      } else {
        if (window.stableStart === undefined) {
          window.stableStart = Date.now();
        }
        return Date.now() - window.stableStart >= 10000;
      }
    }
"""

GET_CSS_JS = """
    () => {
      const cssRules = [];
      Object.values(document.styleSheets).forEach((sheet) => {
        Object.values(sheet.cssRules).forEach((rule) => {
          // This will throw a DOMException if the stylesheet is from a different origin
          // and not CORS-enabled. We catch it below.
          try {
            cssRules.push(rule.cssText);
          } catch (e) {
            // Ignore errors
          }
        });
      });
      return cssRules;
    }
"""

GET_BODY_JS = """
    () => {
        const walk = (doc) => {
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
    }
"""


def generateNotebookUrl(
    notebookUrl: str, notebookId: str, initialCode: str, osoApiKey: str
) -> str:
    lz = LZString()
    environment = {"OSO_API_KEY": osoApiKey}
    env_string = lz.compressToEncodedURIComponent(json.dumps(environment))

    fragment_params = {
        "env": env_string,
        "mode": "edit",
        "code": lz.compressToEncodedURIComponent(initialCode),
    }

    query_params = {"notebook": notebookId}

    query_string = urllib.parse.urlencode(query_params)
    fragment_string = urllib.parse.urlencode(fragment_params)

    return f"{notebookUrl}?{query_string}#{fragment_string}"


class PublishNotebookRunRequestHandler(RunHandler[PublishNotebookRunRequest]):
    topic = "publish_notebook_run_requests"
    message_type = PublishNotebookRunRequest
    schema_file_name = "publish-notebook.proto"

    async def handle_run_message(
        self,
        context: RunContext,
        common_settings: CommonSettings,
        message: PublishNotebookRunRequest,
        oso_client: Client,
    ) -> HandlerResponse:
        context.log.info(
            f"Handling PublishNotebookRunRequest with ID: {message.run_id}"
        )

        notebooks = (await oso_client.get_notebook(message.notebook_id)).notebooks.edges
        if len(notebooks) != 1:
            logger.error(
                "Notebook not found or multiple notebooks returned.",
                notebook_id=message.notebook_id,
            )
            raise ValueError(f"Expected exactly one notebook, got {len(notebooks)}")
        notebook = notebooks[0].node
        url = generateNotebookUrl(
            f"{common_settings.marimo_url}/notebook",
            notebook.id,
            notebook.data,
            message.oso_api_key,
        )

        content = None
        async with async_playwright() as p:
            async with await p.chromium.launch(headless=True) as browser:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle")
                logger.info("Page loaded, waiting for preview button...")
                await page.wait_for_selector(
                    "[data-testid='large-spinner']", timeout=30000
                )
                await page.wait_for_selector(
                    "[data-testid='large-spinner']", timeout=30000, state="hidden"
                )
                preview_button = await page.wait_for_selector(
                    "[id='preview-button']", timeout=30000
                )
                assert preview_button is not None
                await preview_button.click()
                logger.info("Preview button clicked, waiting for content...")

                await page.wait_for_function(WAIT_JS, timeout=250000, polling=100)

                await page.wait_for_timeout(5000)

                logger.info("Page is stable, extracting content...")
                css_list: list[str] = await page.evaluate(GET_CSS_JS)
                body_html: str = await page.evaluate(GET_BODY_JS)

                content = f"<style>{'\n'.join(css_list)}</style>\n{body_html}"

        if content is None:
            logger.error("Failed to extract content from the notebook page.")
            raise RuntimeError("Content extraction failed")

        gzip_content = base64.b64encode(gzip.compress(content.encode("utf-8"))).decode(
            "utf-8"
        )

        response = await oso_client.save_published_notebook_html(
            notebook_id=notebook.id, html_content=gzip_content
        )
        if not response.save_published_notebook_html.success:
            logger.error("Failed to save published notebook HTML.")
            raise RuntimeError("Failed to save published notebook HTML")

        logger.info("Notebook published successfully.")
        return SuccessResponse(
            message=f"Processed PublishNotebookRunRequest with ID: {message.run_id}"
        )
