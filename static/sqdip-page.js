"use strict";

/*
 * This is the only page-specific JavaScript needed when every graph button
 * calls /api/sqdip/chart/<graph_id>.
 */

document.addEventListener("DOMContentLoaded", () => {
    SQDIPCharts.mountButtons({
        target: "#sqdipGraph",
        buttons: "[data-sqdip-chart]",
        endpointBase: "/api/sqdip/chart/"
    });
});