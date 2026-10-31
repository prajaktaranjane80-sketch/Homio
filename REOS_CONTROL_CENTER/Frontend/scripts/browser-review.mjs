
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import process from "node:process";
import { spawn, spawnSync } from "node:child_process";
import { once } from "node:events";
import { createServer } from "node:net";
import { setTimeout as delay } from "node:timers/promises";

const ROOT = process.cwd();
const OUTPUT_DIR = path.join(ROOT, "artifacts", "visual-review");
const PORT = await findAvailablePort();
const BASE_URL = `http://127.0.0.1:${PORT}`;

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1000, mobile: false, screenshot: true },
  { name: "breakpoint-desktop-901", width: 901, height: 900, mobile: false, screenshot: false },
  { name: "breakpoint-mobile-900", width: 900, height: 900, mobile: true, screenshot: false },
  { name: "navigation-boundary-641", width: 641, height: 900, mobile: true, screenshot: false },
  { name: "navigation-grid-640", width: 640, height: 900, mobile: true, screenshot: false },
  { name: "tablet", width: 834, height: 1112, mobile: true, screenshot: true },
  { name: "mobile", width: 390, height: 844, mobile: true, screenshot: true },
  { name: "compact-mobile", width: 320, height: 740, mobile: true, screenshot: true },
];

const report = {
  schemaVersion: 1,
  project: "HOMIO / REOS",
  purpose: "Production-build browser, responsive, keyboard and accessibility review",
  commit: process.env.GITHUB_SHA ?? null,
  generatedAt: new Date().toISOString(),
  browser: null,
  baseUrl: BASE_URL,
  viewports: [],
  checks: [],
  runtimeExceptions: [],
  failedLocalResponses: [],
  fatalError: null,
  result: "RUNNING",
};

let failed = false;
let serverProcess;
let chromeProcess;
let cdp;
let chromeProfile;
let serverOutput = "";
let chromeOutput = "";

function log(message) {
  console.log(`[HOMIO BROWSER REVIEW] ${message}`);
}

function check(scope, name, passed, details = {}) {
  const item = {
    scope,
    name,
    status: passed ? "PASS" : "FAIL",
    details,
  };

  report.checks.push(item);
  log(
    `${item.status} | ${scope} | ${name}${
      Object.keys(details).length ? ` | ${JSON.stringify(details)}` : ""
    }`,
  );

  if (!passed) failed = true;

  return passed;
}

async function findAvailablePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();

    server.once("error", reject);

    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port =
        typeof address === "object" && address ? address.port : null;

      server.close((error) => {
        if (error) reject(error);
        else if (!port) reject(new Error("Could not allocate a local port."));
        else resolve(port);
      });
    });
  });
}

async function waitFor(
  predicate,
  label,
  timeoutMs = 30000,
  intervalMs = 250,
) {
  const started = Date.now();
  let lastError;

  while (Date.now() - started < timeoutMs) {
    try {
      const value = await predicate();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }

    if (
      serverProcess?.exitCode !== null &&
      serverProcess?.exitCode !== undefined
    ) {
      throw new Error(
        `Production server exited before ${label}.\n${serverOutput}`,
      );
    }

    if (
      chromeProcess?.exitCode !== null &&
      chromeProcess?.exitCode !== undefined
    ) {
      throw new Error(`Chrome exited before ${label}.\n${chromeOutput}`);
    }

    await delay(intervalMs);
  }

  throw new Error(
    `Timed out waiting for ${label}.${
      lastError ? ` Last error: ${lastError.message}` : ""
    }`,
  );
}

function resolveChromeExecutable() {
  const candidates = [
    process.env.CHROME_BIN,
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) {
      return candidate;
    }

    const found = spawnSync("which", [candidate], {
      encoding: "utf8",
    });

    if (found.status === 0 && found.stdout.trim()) {
      return found.stdout.trim();
    }
  }

  throw new Error(
    "A Chrome/Chromium executable was not found. The browser review requires the pinned Ubuntu 24.04 runner image.",
  );
}

class CdpClient {
  constructor(socket) {
    this.socket = socket;
    this.sequence = 0;
    this.pending = new Map();
    this.events = [];

    socket.addEventListener("message", (event) => {
      let message;

      try {
        message = JSON.parse(String(event.data));
      } catch {
        return;
      }

      if (message.id !== undefined) {
        const pending = this.pending.get(message.id);
        if (!pending) return;

        clearTimeout(pending.timeout);
        this.pending.delete(message.id);

        if (message.error) {
          pending.reject(
            new Error(
              `${pending.method} failed: ${
                message.error.message ?? JSON.stringify(message.error)
              }`,
            ),
          );
        } else {
          pending.resolve(message.result ?? {});
        }

        return;
      }

      if (message.method) {
        this.events.push(message);
      }
    });

    socket.addEventListener("close", () => {
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timeout);
        pending.reject(new Error("Chrome DevTools connection closed."));
      }

      this.pending.clear();
    });
  }

  send(method, params = {}, sessionId) {
    const id = ++this.sequence;
    const packet = { id, method, params };

    if (sessionId) packet.sessionId = sessionId;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Chrome DevTools command timed out: ${method}`));
      }, 20000);

      this.pending.set(id, {
        resolve,
        reject,
        timeout,
        method,
      });

      this.socket.send(JSON.stringify(packet));
    });
  }

  close() {
    try {
      this.socket.close();
    } catch {
      // Cleanup is best-effort after the review has finished.
    }
  }
}

async function connectWebSocket(url) {
  const NativeWebSocket = globalThis.WebSocket;

  if (typeof NativeWebSocket !== "function") {
    throw new Error(
      "Node.js 24 native WebSocket support is required for Chrome DevTools Protocol.",
    );
  }

  const socket = new NativeWebSocket(url);

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(
      () => reject(new Error("Chrome DevTools WebSocket connection timed out.")),
      15000,
    );

    socket.addEventListener(
      "open",
      () => {
        clearTimeout(timeout);
        resolve();
      },
      { once: true },
    );

    socket.addEventListener(
      "error",
      () => {
        clearTimeout(timeout);
        reject(new Error("Could not connect to Chrome DevTools WebSocket."));
      },
      { once: true },
    );
  });

  return new CdpClient(socket);
}

async function evaluate(expression, sessionId) {
  const response = await cdp.send(
    "Runtime.evaluate",
    {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
      includeCommandLineAPI: false,
    },
    sessionId,
  );

  if (response.exceptionDetails) {
    const detail =
      response.exceptionDetails.exception?.description ??
      response.exceptionDetails.text;

    throw new Error(`Browser evaluation failed: ${detail}`);
  }

  return response.result?.value;
}

async function pressKey(sessionId, key, code, virtualKeyCode) {
  await cdp.send(
    "Input.dispatchKeyEvent",
    {
      type: "keyDown",
      key,
      code,
      windowsVirtualKeyCode: virtualKeyCode,
      nativeVirtualKeyCode: virtualKeyCode,
    },
    sessionId,
  );

  await cdp.send(
    "Input.dispatchKeyEvent",
    {
      type: "keyUp",
      key,
      code,
      windowsVirtualKeyCode: virtualKeyCode,
      nativeVirtualKeyCode: virtualKeyCode,
    },
    sessionId,
  );
}

async function startProductionServer() {
  const nextCli = path.join(
    ROOT,
    "node_modules",
    "next",
    "dist",
    "bin",
    "next",
  );

  if (!fs.existsSync(nextCli)) {
    throw new Error(
      "Next.js CLI is missing. Run the existing production build before the browser review.",
    );
  }

  serverProcess = spawn(
    process.execPath,
    [
      nextCli,
      "start",
      "--hostname",
      "127.0.0.1",
      "--port",
      String(PORT),
    ],
    {
      cwd: ROOT,
      env: {
        ...process.env,
        NODE_ENV: "production",
        NEXT_TELEMETRY_DISABLED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  serverProcess.stdout.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });

  serverProcess.stderr.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });

  await waitFor(
    async () => {
      const response = await fetch(`${BASE_URL}/`, {
        redirect: "manual",
      });

      return response.status === 200;
    },
    "production homepage HTTP 200",
    45000,
  );

  log(`Production Next.js server returned HTTP 200 at ${BASE_URL}.`);
}

async function startChrome() {
  const executable = resolveChromeExecutable();

  chromeProfile = fs.mkdtempSync(
    path.join(os.tmpdir(), "homio-browser-review-"),
  );

  chromeProcess = spawn(
    executable,
    [
      "--headless=new",
      "--no-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-debugging-port=0",
      `--user-data-dir=${chromeProfile}`,
      "about:blank",
    ],
    {
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  chromeProcess.stdout.on("data", (chunk) => {
    chromeOutput += chunk.toString();
  });

  chromeProcess.stderr.on("data", (chunk) => {
    chromeOutput += chunk.toString();
  });

  const activePortFile = path.join(
    chromeProfile,
    "DevToolsActivePort",
  );

  await waitFor(
    () => {
      if (!fs.existsSync(activePortFile)) return false;

      const port = Number(
        fs.readFileSync(activePortFile, "utf8").split(/\r?\n/)[0],
      );

      return Number.isInteger(port) && port > 0 ? port : false;
    },
    "Chrome DevTools endpoint",
    20000,
    100,
  );

  const port = Number(
    fs.readFileSync(activePortFile, "utf8").split(/\r?\n/)[0],
  );

  const version = await (
    await fetch(`http://127.0.0.1:${port}/json/version`)
  ).json();

  report.browser = {
    product: version.Browser ?? "unknown",
    protocolVersion: version["Protocol-Version"] ?? null,
    executable,
  };

  cdp = await connectWebSocket(version.webSocketDebuggerUrl);

  const { targetId } = await cdp.send(
    "Target.createTarget",
    { url: "about:blank" },
  );

  const { sessionId } = await cdp.send(
    "Target.attachToTarget",
    { targetId, flatten: true },
  );

  await cdp.send("Page.enable", {}, sessionId);
  await cdp.send("Runtime.enable", {}, sessionId);
  await cdp.send("Network.enable", {}, sessionId);
  await cdp.send("Accessibility.enable", {}, sessionId);

  log(
    `Connected to ${report.browser.product} using the native Node.js WebSocket client.`,
  );

  return sessionId;
}

async function loadViewport(sessionId, viewport) {
  await cdp.send(
    "Emulation.setDeviceMetricsOverride",
    {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile,
      screenWidth: viewport.width,
      screenHeight: viewport.height,
    },
    sessionId,
  );

  await cdp.send(
    "Emulation.setTouchEmulationEnabled",
    {
      enabled: viewport.mobile,
      maxTouchPoints: viewport.mobile ? 5 : 1,
    },
    sessionId,
  );

  await cdp.send(
    "Emulation.setEmulatedMedia",
    {
      features: [
        {
          name: "prefers-reduced-motion",
          value: "no-preference",
        },
      ],
    },
    sessionId,
  );

  const navigation = await cdp.send(
    "Page.navigate",
    { url: BASE_URL },
    sessionId,
  );

  if (navigation.errorText) {
    throw new Error(
      `Browser navigation failed for ${viewport.name}: ${navigation.errorText}`,
    );
  }

  await waitFor(
    async () =>
      evaluate(
        `(() => document.readyState === "complete" && Boolean(document.querySelector("#homio-hero-title")))()`,
        sessionId,
      ),
    `${viewport.name} homepage render`,
    30000,
  );

  await delay(500);
}

async function captureScreenshot(sessionId, viewport) {
  if (!viewport.screenshot) return null;

  const response = await cdp.send(
    "Page.captureScreenshot",
    {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    },
    sessionId,
  );

  const fileName = `${viewport.name}-${viewport.width}x${viewport.height}.png`;

  fs.writeFileSync(
    path.join(OUTPUT_DIR, fileName),
    Buffer.from(response.data, "base64"),
  );

  return fileName;
}

async function captureFooterScreenshot(sessionId, viewport) {
  if (!viewport.screenshot) return null;

  await evaluate(
    "window.scrollTo(0, document.documentElement.scrollHeight)",
    sessionId,
  );

  await delay(250);

  const response = await cdp.send(
    "Page.captureScreenshot",
    {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    },
    sessionId,
  );

  const fileName =
    `${viewport.name}-${viewport.width}x${viewport.height}-footer.png`;

  fs.writeFileSync(
    path.join(OUTPUT_DIR, fileName),
    Buffer.from(response.data, "base64"),
  );

  await evaluate("window.scrollTo(0, 0)", sessionId);

  return fileName;
}

async function inspectViewport(sessionId, viewport) {
  const scope = `${viewport.name} ${viewport.width}x${viewport.height}`;

  const metrics = await evaluate(`(() => {
    const box = (element) => {
      if (!element) return null;

      const rect = element.getBoundingClientRect();

      return {
        x: Math.round(rect.x * 10) / 10,
        y: Math.round(rect.y * 10) / 10,
        width: Math.round(rect.width * 10) / 10,
        height: Math.round(rect.height * 10) / 10,
        right: Math.round(rect.right * 10) / 10,
        bottom: Math.round(rect.bottom * 10) / 10,
      };
    };

    const visible = (element) => {
      if (!element) return false;

      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();

      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        rect.width > 0 &&
        rect.height > 0
      );
    };

    const desktopNav = document.querySelector(".responsive-nav__desktop");
    const mobileNav = document.querySelector(".responsive-nav__mobile");
    const search = document.querySelector(
      '.global-search__form input[aria-label="Search HOMIO"]'
    );
    const hero = document.querySelector("#homio-hero-title");
    const summary = document.querySelector(
      ".responsive-nav__mobile summary"
    );

    return {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      h1Count: document.querySelectorAll("h1").length,
      heroText: hero?.innerText?.replace(/\\s+/g, " ").trim() ?? null,
      heroVisible: visible(hero),
      headerVisible: visible(document.querySelector(".site-header")),
      brandVisible: visible(document.querySelector(".brand")),
      searchVisible: visible(search),
      searchHeight: box(search)?.height ?? null,
      desktopNavVisible: visible(desktopNav),
      mobileNavVisible: visible(mobileNav),
      desktopNavDisplay: desktopNav
        ? getComputedStyle(desktopNav).display
        : null,
      mobileNavDisplay: mobileNav
        ? getComputedStyle(mobileNav).display
        : null,
      summaryHeight: box(summary)?.height ?? null,
      summaryBox: box(summary),
      globalActionHeights: [
        ...document.querySelectorAll(".global-actions__link"),
      ].map((element) => box(element)?.height ?? 0),
      globalActionsVisible: visible(document.querySelector(".global-actions")),
      discoveryNav: (() => {
        const nav = document.querySelector(
          'nav[aria-label="HOMIO discovery navigation"]'
        );
        const container = nav?.firstElementChild;
        const containerRect = container?.getBoundingClientRect();
        const links = [...(nav?.querySelectorAll("a") ?? [])];
        const clippedLabels = links
          .filter((link) => {
            const rect = link.getBoundingClientRect();

            return (
              !containerRect ||
              rect.left < containerRect.left - 1 ||
              rect.right > containerRect.right + 1
            );
          })
          .map((link) => link.textContent.trim());

        return {
          linkCount: links.length,
          labels: links.map((link) => link.textContent.trim()),
          clippedLabels,
          scrollWidth: container?.scrollWidth ?? 0,
          clientWidth: container?.clientWidth ?? 0,
          postLinkVisible: Boolean(
            nav &&
            [...nav.querySelectorAll("a")].some(
              (link) => link.textContent.trim() === "List a Property" &&
                visible(link)
            )
          ),
        };
      })(),
      footerVisible: visible(document.querySelector("footer")),
      pageHeight: document.documentElement.scrollHeight,
      imagesMissingAlt: [...document.images]
        .filter((image) => !image.hasAttribute("alt"))
        .map((image) => image.currentSrc || image.src)
        .slice(0, 20),
      positiveTabIndexes: [...document.querySelectorAll("[tabindex]")]
        .filter((element) => Number(element.getAttribute("tabindex")) > 0)
        .map((element) => element.outerHTML.slice(0, 180))
        .slice(0, 20),
      landmarks: {
        header: document.querySelectorAll("header").length,
        main: document.querySelectorAll("main").length,
        footer: document.querySelectorAll("footer").length,
        namedNavigation: [...document.querySelectorAll("nav")]
          .filter((nav) =>
            Boolean(
              nav.getAttribute("aria-label") ||
              nav.getAttribute("aria-labelledby")
            )
          ).length,
      },
    };
  })()`, sessionId);

  const screenshot = await captureScreenshot(sessionId, viewport);
  const footerScreenshot = await captureFooterScreenshot(sessionId, viewport);

  report.viewports.push({
    ...viewport,
    metrics,
    screenshot,
    footerScreenshot,
  });

  check(
    scope,
    "No horizontal page overflow",
    metrics.documentWidth <= viewport.width + 1 &&
      metrics.bodyWidth <= viewport.width + 1,
    {
      viewportWidth: viewport.width,
      documentWidth: metrics.documentWidth,
      bodyWidth: metrics.bodyWidth,
    },
  );

  check(
    scope,
    "Discovery navigation shows all six links and the property CTA without clipping",
    metrics.discoveryNav.linkCount === 7 &&
      metrics.discoveryNav.clippedLabels.length === 0 &&
      metrics.discoveryNav.scrollWidth <= metrics.discoveryNav.clientWidth + 1 &&
      metrics.discoveryNav.postLinkVisible,
    metrics.discoveryNav,
  );

  const quickActionsExpectedVisible = viewport.width > 900;

  check(
    scope,
    "Global quick actions do not cover content on touch-first layouts",
    metrics.globalActionsVisible === quickActionsExpectedVisible &&
      (!quickActionsExpectedVisible ||
        (metrics.globalActionHeights.length === 3 &&
          metrics.globalActionHeights.every((height) => height >= 44))),
    {
      expectedVisible: quickActionsExpectedVisible,
      visible: metrics.globalActionsVisible,
      linkHeights: metrics.globalActionHeights,
    },
  );

  check(
    scope,
    "HOMIO shell, brand and homepage hero render",
    metrics.headerVisible &&
      metrics.brandVisible &&
      metrics.heroVisible &&
      metrics.h1Count === 1,
    {
      headerVisible: metrics.headerVisible,
      brandVisible: metrics.brandVisible,
      heroVisible: metrics.heroVisible,
      h1Count: metrics.h1Count,
      heroText: metrics.heroText,
    },
  );

  check(
    scope,
    "Global search is visible and usable",
    metrics.searchVisible && metrics.searchHeight >= 44,
    {
      searchVisible: metrics.searchVisible,
      searchHeight: metrics.searchHeight,
    },
  );

  const expectDesktopNav = viewport.width > 900;

  check(
    scope,
    "Responsive navigation switches at the canonical 900px breakpoint",
    expectDesktopNav
      ? metrics.desktopNavVisible && !metrics.mobileNavVisible
      : metrics.mobileNavVisible && !metrics.desktopNavVisible,
    {
      expected: expectDesktopNav
        ? "desktop navigation"
        : "mobile disclosure navigation",
      desktopVisible: metrics.desktopNavVisible,
      mobileVisible: metrics.mobileNavVisible,
    },
  );

  check(
    scope,
    "Homepage has visible footer and named structural landmarks with one main region",
    metrics.footerVisible &&
      metrics.landmarks.header >= 1 &&
      metrics.landmarks.main === 1 &&
      metrics.landmarks.footer >= 1 &&
      metrics.landmarks.namedNavigation >= 1,
    {
      ...metrics.landmarks,
      footerVisible: metrics.footerVisible,
      pageHeight: metrics.pageHeight,
    },
  );

  check(
    scope,
    "All rendered images provide an alt attribute",
    metrics.imagesMissingAlt.length === 0,
    {
      missingAltCount: metrics.imagesMissingAlt.length,
      examples: metrics.imagesMissingAlt,
    },
  );

  check(
    scope,
    "No positive tabindex values disrupt natural keyboard order",
    metrics.positiveTabIndexes.length === 0,
    {
      count: metrics.positiveTabIndexes.length,
      examples: metrics.positiveTabIndexes,
    },
  );

  if (viewport.mobile) {
    const menuResult = await evaluate(`(() => {
      const details = document.querySelector(
        ".responsive-nav__mobile details"
      );
      const summary = details?.querySelector("summary");

      if (!details || !summary) {
        return { available: false };
      }

      details.open = true;

      const menu = details.querySelector(
        ".responsive-nav__mobile-menu"
      );
      const links = [...(menu?.querySelectorAll("a") ?? [])];
      const rect = menu?.getBoundingClientRect();

      return {
        available: true,
        open: details.open,
        menuVisible: Boolean(
          menu &&
          getComputedStyle(menu).display !== "none" &&
          rect?.width > 0
        ),
        menuInsideViewport: Boolean(
          rect &&
          rect.left >= -1 &&
          rect.right <= window.innerWidth + 1 &&
          rect.top >= -1 &&
          rect.bottom <= window.innerHeight + 1
        ),
        summaryHeight: summary.getBoundingClientRect().height,
        linkCount: links.length,
        linkHeights: links.map(
          (link) =>
            Math.round(link.getBoundingClientRect().height * 10) / 10
        ),
        menuLabels: links.map((link) => link.textContent.trim()),
      };
    })()`, sessionId);

    check(
      scope,
      "Mobile menu opens and remains inside the viewport",
      menuResult.available &&
        menuResult.open &&
        menuResult.menuVisible &&
        menuResult.menuInsideViewport,
      menuResult,
    );

    check(
      scope,
      "Mobile menu disclosure and every menu link meet 44px touch target height",
      menuResult.summaryHeight >= 44 &&
        menuResult.linkCount >= 1 &&
        menuResult.linkHeights.every((height) => height >= 44),
      menuResult,
    );

    await evaluate(`(() => {
      const details = document.querySelector(
        ".responsive-nav__mobile details"
      );

      details?.querySelector("summary")?.focus();

      return Boolean(details?.open);
    })()`, sessionId);

    await pressKey(sessionId, "Escape", "Escape", 27);

    const escapeResult = await evaluate(`(() => {
      const details = document.querySelector(
        ".responsive-nav__mobile details"
      );
      const summary = details?.querySelector("summary");

      return {
        closed: details ? !details.open : false,
        focusRestored: Boolean(
          summary && document.activeElement === summary
        ),
      };
    })()`, sessionId);

    check(
      scope,
      "Escape closes the mobile menu and restores focus to Menu",
      escapeResult.closed && escapeResult.focusRestored,
      escapeResult,
    );
  }

  const reducedMotion = await (async () => {
    await cdp.send(
      "Emulation.setEmulatedMedia",
      {
        features: [
          {
            name: "prefers-reduced-motion",
            value: "reduce",
          },
        ],
      },
      sessionId,
    );

    const result = await evaluate(`(() => {
      const target = document.querySelector(
        '.global-search__form input[aria-label="Search HOMIO"]'
      );
      const seconds = Number.parseFloat(
        getComputedStyle(target).transitionDuration
      );

      return {
        mediaMatches: matchMedia(
          "(prefers-reduced-motion: reduce)"
        ).matches,
        transitionDuration: getComputedStyle(target).transitionDuration,
        transitionSeconds: seconds,
      };
    })()`, sessionId);

    await cdp.send(
      "Emulation.setEmulatedMedia",
      {
        features: [
          {
            name: "prefers-reduced-motion",
            value: "no-preference",
          },
        ],
      },
      sessionId,
    );

    return result;
  })();

  check(
    scope,
    "Reduced-motion preference is honoured by the shared shell",
    reducedMotion.mediaMatches &&
      Number.isFinite(reducedMotion.transitionSeconds) &&
      reducedMotion.transitionSeconds <= 0.00002,
    reducedMotion,
  );

  if (viewport.mobile) {
    // Disable touch emulation only during the keyboard-only focus assertion.
    // Viewport metrics remain mobile; this prevents the emulated touch device
    // from suppressing desktop-class physical keyboard focus navigation.
    await cdp.send(
      "Emulation.setTouchEmulationEnabled",
      { enabled: false, maxTouchPoints: 1 },
      sessionId,
    );
  }

  await evaluate(
    `(() => {
      window.scrollTo(0, 0);
      document.activeElement?.blur?.();
      document.body.setAttribute("tabindex", "-1");
      document.body.focus();

      return document.activeElement === document.body;
    })()`,
    sessionId,
  );

  await pressKey(sessionId, "Tab", "Tab", 9);

  const skipLinkResult = await evaluate(`(() => {
    const skip = document.querySelector(".skip-link");
    const rect = skip?.getBoundingClientRect();

    return {
      focused: Boolean(skip && document.activeElement === skip),
      position: skip ? getComputedStyle(skip).position : null,
      visible: Boolean(
        rect &&
        rect.width > 0 &&
        rect.height > 0 &&
        rect.top >= 0 &&
        rect.top < 80
      ),
      rect: rect
        ? {
            top: rect.top,
            width: rect.width,
            height: rect.height,
          }
        : null,
    };
  })()`, sessionId);

  check(
    scope,
    "First keyboard Tab reveals and focuses Skip to content",
    skipLinkResult.focused &&
      skipLinkResult.position === "fixed" &&
      skipLinkResult.visible,
    skipLinkResult,
  );

  await evaluate(
    `document.body.removeAttribute("tabindex")`,
    sessionId,
  );

  if (viewport.mobile) {
    await cdp.send(
      "Emulation.setTouchEmulationEnabled",
      { enabled: true, maxTouchPoints: 5 },
      sessionId,
    );
  }

  const axTree = await cdp.send(
    "Accessibility.getFullAXTree",
    {},
    sessionId,
  );

  const unnamedNodes = (axTree.nodes ?? [])
    .filter((node) => !node.ignored)
    .filter((node) =>
      [
        "button",
        "link",
        "textbox",
        "searchbox",
        "checkbox",
        "radio",
        "switch",
      ].includes(node.role?.value)
    )
    .filter((node) => !String(node.name?.value ?? "").trim())
    .map((node) => ({
      role: node.role?.value,
      name: node.name?.value ?? "",
      backendDOMNodeId: node.backendDOMNodeId,
    }))
    .slice(0, 20);

  check(
    scope,
    "Visible interactive controls expose accessible names",
    unnamedNodes.length === 0,
    {
      unnamedCount: unnamedNodes.length,
      examples: unnamedNodes,
    },
  );

  const searchValidation = await evaluate(`(() => {
    const form = document.querySelector(".global-search__form");
    const input = form?.querySelector(
      'input[aria-label="Search HOMIO"]'
    );
    const button = form?.querySelector('button[type="submit"]');

    if (!form || !input || !button) {
      return { available: false };
    }

    input.value = "";
    button.click();

    return { available: true };
  })()`, sessionId);

  await waitFor(
    async () =>
      evaluate(
        `(() => Boolean(
          document.querySelector(".global-search__status")
            ?.textContent?.trim()
        ))()`,
        sessionId,
      ),
    `${viewport.name} empty-search validation feedback`,
    5000,
    100,
  );

  const searchFeedback = await evaluate(`(() => {
    const input = document.querySelector(
      '.global-search__form input[aria-label="Search HOMIO"]'
    );
    const status = document.querySelector(".global-search__status");

    return {
      available: Boolean(input && status),
      invalid: input?.getAttribute("aria-invalid") === "true",
      describedBy: input?.getAttribute("aria-describedby"),
      statusId: status?.id,
      statusText: status?.textContent?.trim(),
      live: status?.getAttribute("aria-live"),
    };
  })()`, sessionId);

  check(
    scope,
    "Empty search gives an accessible inline validation message",
    searchValidation.available &&
      searchFeedback.invalid &&
      searchFeedback.describedBy === searchFeedback.statusId &&
      Boolean(searchFeedback.statusText) &&
      searchFeedback.live === "polite",
    searchFeedback,
  );

  const exceptions = cdp.events
    .filter(
      (event) =>
        event.sessionId === sessionId &&
        event.method === "Runtime.exceptionThrown",
    )
    .map(
      (event) =>
        event.params?.exceptionDetails?.exception?.description ??
        event.params?.exceptionDetails?.text ??
        "Unknown browser exception",
    );

  report.runtimeExceptions.push(
    ...exceptions.map((message) => ({
      viewport: viewport.name,
      message,
    })),
  );

  check(
    scope,
    "No uncaught browser runtime exceptions",
    exceptions.length === 0,
    {
      count: exceptions.length,
      examples: exceptions.slice(0, 5),
    },
  );
}

async function run() {
  fs.rmSync(OUTPUT_DIR, {
    recursive: true,
    force: true,
  });

  fs.mkdirSync(OUTPUT_DIR, {
    recursive: true,
  });

  await startProductionServer();

  const sessionId = await startChrome();

  for (const viewport of VIEWPORTS) {
    log(
      `Reviewing ${viewport.name} (${viewport.width}x${viewport.height}).`,
    );

    await loadViewport(sessionId, viewport);
    await inspectViewport(sessionId, viewport);
  }

  const localFailures = cdp.events
    .filter(
      (event) =>
        event.sessionId === sessionId &&
        event.method === "Network.responseReceived",
    )
    .map((event) => event.params?.response)
    .filter(
      (response) =>
        response?.url?.startsWith(BASE_URL) &&
        response.status >= 400,
    )
    .map((response) => ({
      url: response.url,
      status: response.status,
    }));

  report.failedLocalResponses = localFailures;

  const staticBundleFailures = localFailures.filter((item) => {
    try {
      return new URL(item.url).pathname.startsWith("/_next/static/");
    } catch {
      return false;
    }
  });

  check(
    "all viewports",
    "No Next.js JavaScript or CSS bundle returned HTTP 4xx/5xx",
    staticBundleFailures.length === 0,
    {
      count: staticBundleFailures.length,
      examples: staticBundleFailures.slice(0, 10),
    },
  );

  if (localFailures.length > staticBundleFailures.length) {
    log(
      `Non-bundle local HTTP errors retained as diagnostic warnings: ${
        localFailures.length - staticBundleFailures.length
      }.`,
    );
  }
}

try {
  await run();
} catch (error) {
  failed = true;

  report.fatalError =
    error instanceof Error
      ? `${error.message}\n${error.stack ?? ""}`
      : String(error);

  console.error(report.fatalError);
} finally {
  if (cdp) {
    try {
      await Promise.race([
        cdp.send("Browser.close").catch(() => undefined),
        delay(1000),
      ]);
    } catch {
      // The browser may already have exited after a failed navigation.
    }

    cdp.close();
  }

  async function stopChild(child) {
    if (!child || child.exitCode !== null) return;

    const exited = once(child, "exit").catch(() => undefined);

    child.kill("SIGTERM");

    await Promise.race([
      exited,
      delay(2500),
    ]);

    if (child.exitCode === null) {
      const forceExit = once(child, "exit").catch(() => undefined);

      child.kill("SIGKILL");

      await Promise.race([
        forceExit,
        delay(1500),
      ]);
    }
  }

  await stopChild(chromeProcess);
  await stopChild(serverProcess);

  if (chromeProfile) {
    try {
      fs.rmSync(chromeProfile, {
        recursive: true,
        force: true,
        maxRetries: 10,
        retryDelay: 150,
      });
    } catch (error) {
      console.warn(
        `Could not remove temporary Chrome profile: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  report.result = failed ? "FAIL" : "PASS";

  report.checkSummary = {
    passed: report.checks.filter(
      (item) => item.status === "PASS",
    ).length,
    failed: report.checks.filter(
      (item) => item.status === "FAIL",
    ).length,
    total: report.checks.length,
  };

  report.generatedAt = new Date().toISOString();

  try {
    fs.mkdirSync(OUTPUT_DIR, {
      recursive: true,
    });

    fs.writeFileSync(
      path.join(OUTPUT_DIR, "report.json"),
      `${JSON.stringify(report, null, 2)}\n`,
      "utf8",
    );
  } catch (error) {
    console.error(
      `Could not save browser review report: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );

    failed = true;
  }

  console.log("");
  console.log("====================================================");
  console.log(
    `HOMIO PRODUCTION BROWSER REVIEW = ${report.result}`,
  );
  console.log(
    `CHECKS PASSED                   = ${report.checkSummary.passed}`,
  );
  console.log(
    `CHECKS FAILED                   = ${report.checkSummary.failed}`,
  );
  console.log(
    `VIEWPORTS REVIEWED              = ${report.viewports.length}`,
  );
  console.log(
    `BROWSER                         = ${report.browser?.product ?? "unavailable"}`,
  );
  console.log(
    `EVIDENCE DIRECTORY              = ${OUTPUT_DIR}`,
  );
  console.log("====================================================");
}

if (failed) {
  process.exitCode = 1;
}
