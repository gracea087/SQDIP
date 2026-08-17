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

        const tablePanel =
            document.getElementById(
                "deliverablesTablePanel"
            );


        if (
            !graphPanel
            || !graphTarget
            || !tablePanel
        ) {
            console.error(
                "The deliverables page "
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

                    /*
                     * Show graph,
                     * hide table.
                     */
                    graphPanel.hidden =
                        false;

                    tablePanel.hidden =
                        true;
                }
        });


        /*
         * TABLE BUTTONS
         */
        SQDIPCharts.mountTableButtons({

            target:
                "#deliverablesTable",

            buttons:
                ".button-container "
                + "[data-sqdip-table]",

            endpointBase:
                "/api/sqdip/table/",

            autoLoad:
                false,

            onBeforeLoad:
                function () {

                    /*
                     * Hide graph,
                     * show table.
                     */
                    graphPanel.hidden =
                        true;

                    tablePanel.hidden =
                        false;
                }
        });
    }
);