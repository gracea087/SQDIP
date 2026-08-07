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

        const filterContainer =
            document.getElementById(
                "qualityGraphFilters"
            );


        if (
            !graphPanel
            || !graphTarget
            || !filterContainer
        ) {
            console.error(
                "The Quality graph "
                + "elements could not be found."
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


        /*
         * Keep track of which graph is
         * currently selected.
         */
        let activeChartId = null;


        /*
         * Q2 database-driven location filters.
         */
        const q2Filters =
            SQDIPCharts.mountFilterButtons({

                container:
                    "#qualityGraphFilters",

                target:
                    "#qualityGraph",

                chartId:
                    "Q2_grn",

                filterId:
                    "grn_location",

                parameterName:
                    "location",

                includeAll:
                    true,

                allLabel:
                    "ALL LOCATIONS"
            });


        /*
         * Load the location list from SQL.
         *
         * The buttons are created automatically
         * from the values returned by:
         *
         * /api/sqdip/filter/grn_location
         */
        q2Filters.refresh()
            .then(function () {

                /*
                 * Don't show them unless
                 * Q2 is currently selected.
                 */
                if (
                    activeChartId
                    !== "Q2_grn"
                ) {
                    q2Filters.hide();
                }
            })
            .catch(function (error) {

                console.error(
                    "Could not load "
                    + "Q2 location filters:",
                    error
                );

                q2Filters.hide();
            });


        /*
         * Normal SQDIP graph buttons.
         */
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
                function ({
                    chartId
                }) {

                    activeChartId =
                        chartId;

                    graphPanel.hidden =
                        false;

                        // only show filters for applicable graphs
                    if (
                        chartId ===
                        "Q2_grn"
                    ) {
                        q2Filters.show();
                    }
                    else {
                        q2Filters.hide();
                    }
                }
        });
    }
);