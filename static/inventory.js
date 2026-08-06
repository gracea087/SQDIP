"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {
        const graphPanel =
            document.getElementById(
                "inventoryGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "inventoryGraph"
            );


        if (
            !graphPanel
            || !graphTarget
        ) {
            console.error(
                "The inventory graph "
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
                "#inventoryGraph",

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