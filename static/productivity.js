"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {
        const graphPanel =
            document.getElementById(
                "productivityGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "productivityGraph"
            );


        if (
            !graphPanel
            || !graphTarget
        ) {
            console.error(
                "The Productivity graph "
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
                "#productivityGraph",

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