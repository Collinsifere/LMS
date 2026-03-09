// LMS main.js
// - Auto-dismiss flash alerts safely
// - Uses Bootstrap's Alert API if available
// - Supports per-alert opt-in via data-auto-dismiss="true"

(() => {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    /**
     * Configuration
     * If you want to keep the old behavior (dismiss ALL alerts), set:
     *   DISMISS_MODE = "all"
     * Otherwise, "opt-in" means only alerts with data-auto-dismiss="true" will dismiss.
     */
    const DISMISS_MODE = "opt-in"; // "opt-in" | "all"
    const DEFAULT_DELAY_MS = 5000;

    const selector =
      DISMISS_MODE === "all"
        ? ".alert"
        : '.alert[data-auto-dismiss="true"]';

    document.querySelectorAll(selector).forEach((el) => {
      // Allow per-alert override: data-auto-dismiss-ms="8000"
      const delayAttr = el.getAttribute("data-auto-dismiss-ms");
      const delayMs = delayAttr ? Number(delayAttr) : DEFAULT_DELAY_MS;

      if (!Number.isFinite(delayMs) || delayMs <= 0) return;

      window.setTimeout(() => dismissAlert(el), delayMs);
    });
  });

  function dismissAlert(el) {
    if (!el || !el.isConnected) return;

    // If bootstrap Alert API is available, use it
    const bs = window.bootstrap;
    if (bs && bs.Alert) {
      try {
        // Create/get instance and close
        const instance = bs.Alert.getOrCreateInstance(el);
        instance.close();
        return;
      } catch (e) {
        // fall back below
      }
    }

    // Fallback: mimic dismiss behavior
    el.classList.remove("show");
    el.classList.add("fade");

    window.setTimeout(() => {
      if (el && el.isConnected) el.remove();
    }, 200);
  }
})();