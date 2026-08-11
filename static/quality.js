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
            typeof SQDIPCharts
                === "undefined"
        ) {
            console.error(
                "sqdip-charts.js "
                + "has not loaded."
            );

            return;
        }


        let activeChartId =
            null;


        /*
         * Q1 Return / Repair filters.
         */
        const q1Filters =
            SQDIPCharts.mountFilterButtons({

                container:
                    "#qualityGraphFilters",

                target:
                    "#qualityGraph",

                chartId:
                    "Q1",

                filterId:
                    "q1_type",

                parameterName:
                    "type",

                includeAll:
                    true,

                allLabel:
                    "ALL"
            });

        /*
         * Q7 Type filters.
         */
        const q7Filters =
            SQDIPCharts.mountFilterButtons({
                container:
                    "#qualityGraphFilters",

                target:
                    "#qualityGraph",

                chartId:
                    "Q7",

                filterId:
                    "q7_type",

                parameterName:
                    "type",

                includeAll:
                    true,

                allLabel:
                    "ALL"
            });


        /*
         * Q2 location filters.
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


        function hideFilters() {
            q1Filters.hide();
            q2Filters.hide();
            q7Filters.hide();
        }


        function loadQ1Filters() {

            q1Filters.refresh()
                .then(function () {

                    if (
                        activeChartId
                            === "Q1"
                    ) {
                        q1Filters.show();
                    }
                })
                .catch(function (error) {

                    console.error(
                        "Could not load "
                        + "Q1 filters:",
                        error
                    );

                    q1Filters.hide();
                });
        }


        function loadQ2Filters() {

            q2Filters.refresh()
                .then(function () {

                    if (
                        activeChartId
                            === "Q2_grn"
                    ) {
                        q2Filters.show();
                    }
                })
                .catch(function (error) {

                    console.error(
                        "Could not load "
                        + "Q2 filters:",
                        error
                    );

                    q2Filters.hide();
                });
        }

        function loadQ7Filters() {

            q7Filters.refresh()
                .then(function () {

                    if (
                        activeChartId
                            === "Q7"
                    ) {
                        q7Filters.show();
                    }
                })
                .catch(function (error) {

                    console.error(
                        "Could not load "
                        + "Q7 filters:",
                        error
                    );

                    q7Filters.hide();
                });
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
                function ({
                    chartId
                }) {

                    activeChartId =
                        chartId;

                    graphPanel.hidden =
                        false;

                    hideFilters();


                    if (
                        chartId === "Q1"
                    ) {
                        loadQ1Filters();
                    }

                    else if (
                        chartId === "Q2_grn"
                    ) {
                        loadQ2Filters();
                    }

                    else if (
                        chartId === "Q7"
                    ) {
                        loadQ7Filters();
                    }
                }
        });
    }
);