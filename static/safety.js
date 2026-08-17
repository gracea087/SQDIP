"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {
        const graphPanel =
            document.getElementById(
                "safetyGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "safetyGraph"
            );


        if (
            !graphPanel
            || !graphTarget
        ) {
            console.error(
                "The safety graph "
                + "panel could not be found."
            );

            return;
        }


        if (
            typeof SQDIPCharts ===
            "undefined"
        ) {
            console.error(
                "sqdip-charts.js "
                + "has not loaded."
            );

            return;
        }


        SQDIPCharts.mountButtons({
            target:
                "#safetyGraph",

            buttons:
                ".button-container "
                + "[data-sqdip-chart]",

            endpointBase:
                "/api/sqdip/chart/",

            autoLoad:
                true,

            onBeforeLoad:
                function () {
                    graphPanel.hidden =
                        false;
                }
        });
        loadDaysSinceLastAccident();
    }
);

async function loadDaysSinceLastAccident() {
    const display =
        document.getElementById(
            "daysSinceLastAccident"
        );

    if (!display) {
        return;
    }

    try {
        const response =
            await fetch(
                "/api/sqdip/chart/S1_days_since_accident"
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const payload =
            await response.json();

        const value =
            payload.data?.[0]?.x;

        if (
            value === null
            || value === undefined
        ) {
            display.textContent = "--";
            return;
        }

        display.textContent =
            value;
    }
    catch (error) {
        console.error(
            "Could not load days since last accident:",
            error
        );

        display.textContent = "--";
    }
}