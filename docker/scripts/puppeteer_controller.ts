// puppeteer_controller.ts
//
// This script connects to an existing Brave Browser instance (with remote debugging enabled),
// then selects the active page and performs scraping (for instance, taking a screenshot and logging the title).
// Customize selectors and scraping logic as needed.

import puppeteer from "puppeteer";

(async () => {
  try {
    // Connect to the running Brave instance via remote debugging (ensure port matches entrypoint.sh)
    const browser = await puppeteer.connect({
      browserURL: "http://localhost:9222",
    });

    // Retrieve all open pages/tabs.
    const pages = await browser.pages();
    if (pages.length === 0) {
      console.error("No pages found in the connected browser instance.");
      process.exit(1);
    }

    // Use the first page (or apply your own filtering logic)
    const page = pages[0];
    console.log(`Connected to page with URL: ${page.url()}`);

    // Example scraping action: take a screenshot.
    await page.screenshot({ path: "controlled_screenshot.png" });
    console.log("Screenshot taken and saved as 'controlled_screenshot.png'.");

    // Example scraping action: log the page title.
    const pageTitle = await page.title();
    console.log(`The page title is: ${pageTitle}`);

    // Add further scraping logic as needed.

    // Disconnect from the browser when done.
    await browser.disconnect();
  } catch (error) {
    console.error("Error in Puppeteer controller:", error);
  }
})();
