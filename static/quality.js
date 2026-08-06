"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {
        const graphPanel =
            document.getElementById(
                "qualityGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "qualityGraph"
            );


        if (
            !graphPanel
            || !graphTarget
        ) {
            console.error(
                "The Quality graph "
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
                "#qualityGraph",

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