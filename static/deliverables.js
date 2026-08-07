"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {
        const graphPanel =
            document.getElementById(
                "deliverablesGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "deliverablesGraph"
            );


        if (
            !graphPanel
            || !graphTarget
        ) {
            console.error(
                "The Deliverables graph "
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
                "#deliverablesGraph",

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