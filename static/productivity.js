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

        const filterContainer =
            document.getElementById(
                "productivityGraphFilters"
            );


        if (
            !graphPanel
            || !graphTarget
            || !filterContainer
        ) {
            console.error(
                "The Productivity graph "
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
         * p12 location filters.
         */
        const p12Filters =
            SQDIPCharts.mountFilterButtons({

                container:
                    "#productivityGraphFilters",

                target:
                    "#productivityGraph",

                chartId:
                    "P12",

                filterId:
                    "p12_training",

                parameterName:
                    "area",

                includeAll:
                    true,

                allLabel:
                    "ALL AREAS"
            });


        function hideFilters() {
            p12Filters.hide();
        }


        function loadP12Filters() {

            p12Filters.refresh()
                .then(function () {

                    if (
                        activeChartId
                            === "P12"
                    ) {
                        p12Filters.show();
                    }
                })
                .catch(function (error) {

                    console.error(
                        "Could not load "
                        + "P12 filters:",
                        error
                    );

                    p12Filters.hide();
                });
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
                function ({
                    chartId
                }) {

                    activeChartId =
                        chartId;

                    graphPanel.hidden =
                        false;

                    hideFilters();

                    if (
                        chartId === "P12"
                    ) {
                        loadP12Filters();
                    }
                }
        });
    }
);