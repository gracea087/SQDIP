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
                false,

            onBeforeLoad:
                function () {
                    graphPanel.hidden =
                        false;
                }
        });
    }
);