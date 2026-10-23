
/*
 * Shared ERP sidebar interactions.
 * File: static/js/sidebar.js
 *
 * Preserves drag resizing and width persistence.
 * Admin dropdown state and scroll restoration are handled
 * by the controller in admin_layout.html.
 */
(function () {
    "use strict";

    const WIDTH_KEY = "erpSidebarWidth";
    const DEFAULT_WIDTH = 268;
    const MIN_WIDTH = 220;
    const MAX_WIDTH = 360;
    const DESKTOP_BREAKPOINT = 992;

    function safeGet(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (_) {
            return null;
        }
    }

    function safeSet(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (_) {
            // Storage may be disabled.
        }
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function initSidebar() {
        const sidebar = document.getElementById("sidebar");

        if (!sidebar || sidebar.dataset.erpResizeReady === "true") {
            return;
        }

        sidebar.dataset.erpResizeReady = "true";

        const root = document.documentElement;
        const savedWidth = Number.parseInt(safeGet(WIDTH_KEY), 10);

        let width = Number.isFinite(savedWidth)
            ? clamp(savedWidth, MIN_WIDTH, MAX_WIDTH)
            : DEFAULT_WIDTH;

        function applyWidth(nextWidth, persist) {
            const availableWidth = Math.max(
                MIN_WIDTH,
                window.innerWidth - 24
            );

            width = clamp(
                nextWidth,
                MIN_WIDTH,
                Math.min(MAX_WIDTH, availableWidth)
            );

            root.style.setProperty(
                "--erp-sidebar-current-width",
                width + "px"
            );

            if (persist) {
                safeSet(WIDTH_KEY, String(width));
            }
        }

        applyWidth(width, false);

        const handle = document.createElement("div");

        handle.className = "sidebar-resize-handle";
        handle.setAttribute("role", "separator");
        handle.setAttribute("aria-orientation", "vertical");
        handle.setAttribute("aria-label", "Resize sidebar");
        handle.setAttribute("title", "Drag to resize sidebar");

        sidebar.appendChild(handle);

        let dragging = false;
        let startX = 0;
        let startWidth = width;

        handle.addEventListener("pointerdown", function (event) {
            if (
                window.innerWidth < DESKTOP_BREAKPOINT ||
                sidebar.classList.contains("collapsed")
            ) {
                return;
            }

            if (event.button !== undefined && event.button !== 0) {
                return;
            }

            dragging = true;
            startX = event.clientX;
            startWidth = sidebar.getBoundingClientRect().width;

            handle.classList.add("is-resizing");
            document.body.classList.add("erp-sidebar-resizing");

            if (handle.setPointerCapture) {
                handle.setPointerCapture(event.pointerId);
            }

            event.preventDefault();
        });

        handle.addEventListener("pointermove", function (event) {
            if (!dragging) return;

            applyWidth(
                startWidth + (event.clientX - startX),
                false
            );
        });

        function stopDragging() {
            if (!dragging) return;

            dragging = false;

            handle.classList.remove("is-resizing");
            document.body.classList.remove("erp-sidebar-resizing");

            safeSet(WIDTH_KEY, String(width));
        }

        handle.addEventListener("pointerup", stopDragging);
        handle.addEventListener("pointercancel", stopDragging);
        handle.addEventListener("lostpointercapture", stopDragging);

        window.addEventListener("resize", function () {
            if (window.innerWidth < DESKTOP_BREAKPOINT) {
                document.body.classList.remove("erp-sidebar-resizing");
                handle.classList.remove("is-resizing");
                dragging = false;
            } else {
                applyWidth(width, false);
            }
        });

        /*
         * Keep compatibility with the Admin layout's collapsed-state key.
         * The layout controller remains responsible for toggling it.
         */
        const savedCollapsed = safeGet("erpSidebarCollapsed");

        if (
            window.innerWidth >= DESKTOP_BREAKPOINT &&
            savedCollapsed === "true"
        ) {
            sidebar.classList.add("collapsed");
            document.body.classList.add("sidebar-collapsed-state");
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initSidebar,
            { once: true }
        );
    } else {
        initSidebar();
    }
})();
