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

        const tablePanel =
            document.getElementById(
                "inventoryTablePanel"
            );

        const graphColourIndicator =
            document.getElementById(
                "graphColourIndicator"
            );


        if (
            !graphPanel
            || !graphTarget
            || !tablePanel
            || !graphColourIndicator
        ) {
            console.error(
                "The inventory page "
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


        /*
         * GRAPH BUTTONS
         */
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
                    button
                }) {

                    graphPanel.hidden =
                        false;

                    tablePanel.hidden =
                        true;

                    graphColourIndicator.hidden =
                        button.dataset
                            .colourIndicator
                        !== "lost-stock";
                }
        });


        /*
         * TABLE BUTTONS
         */
        SQDIPCharts.mountTableButtons({

            target:
                "#inventoryTable",

            buttons:
                ".button-container "
                + "[data-sqdip-table]",

            endpointBase:
                "/api/sqdip/table/",

            autoLoad:
                false,

            onBeforeLoad:
                function () {

                    graphPanel.hidden =
                        true;

                    tablePanel.hidden =
                        false;

                    graphColourIndicator.hidden =
                        true;
                }
        });
    }
);