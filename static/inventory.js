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

        const graphColourIndicator =
            document.getElementById(
                "graphColourIndicator"
            );


        if (
            !graphPanel
            || !graphTarget
            || !graphColourIndicator
        ) {
            console.error(
                "The inventory graph "
                + "elements could not be found."
            );

            return;
        }


        if (
            typeof SQDIPCharts
                === "undefined"
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
                function ({
                    chartId,
                    button
                }) {

                    graphPanel.hidden =
                        false;


                    /*
                     * Show Lost Stock colour
                     * legend only for charts
                     * marked as lost-stock.
                     */
                    graphColourIndicator.hidden =
                        button.dataset
                            .colourIndicator
                        !== "lost-stock";
                }
        });
    }
);