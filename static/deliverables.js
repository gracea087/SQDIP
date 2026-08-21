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

        const exportButton =
            document.getElementById(
                "exportDeliverablesButton"
            );


        if (
            !graphPanel
            || !graphTarget
            || !tablePanel
            || !exportButton
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


        let activeExportId =
            null;


        function hideExportButton() {

            activeExportId =
                null;

            exportButton.hidden =
                true;

            exportButton.disabled =
                true;
        }


        function setExportButton(
            button,
            itemId
        ) {

            const exportable =
                button.dataset
                    .sqdipExport
                === "true";


            if (!exportable) {
                hideExportButton();

                return;
            }


            activeExportId =
                itemId;

            exportButton.hidden =
                false;

            exportButton.disabled =
                false;
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

                    graphPanel.hidden =
                        false;

                    tablePanel.hidden =
                        true;

                    hideExportButton();
                },

            onLoaded:
                function ({
                    chartId,
                    button
                }) {

                    setExportButton(
                        button,
                        chartId
                    );
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

                    graphPanel.hidden =
                        true;

                    tablePanel.hidden =
                        false;

                    hideExportButton();
                },

            onLoaded:
                function ({
                    tableId,
                    button
                }) {

                    setExportButton(
                        button,
                        tableId
                    );
                }
        });


        /*
         * EXCEL EXPORT
         */
        exportButton.addEventListener(
            "click",
            async function () {

                if (!activeExportId) {
                    return;
                }


                exportButton.disabled =
                    true;


                try {

                    const response =
                        await fetch(
                            "/api/sqdip/export/"
                            + encodeURIComponent(
                                activeExportId
                            )
                        );


                    if (!response.ok) {

                        let message =
                            "Excel export failed.";


                        try {

                            const data =
                                await response.json();

                            if (data.error) {
                                message =
                                    data.error;
                            }

                        }
                        catch {
                            /*
                             * Response was not JSON.
                             */
                        }


                        throw new Error(
                            message
                        );
                    }


                    const blob =
                        await response.blob();


                    const disposition =
                        response.headers.get(
                            "Content-Disposition"
                        )
                        || "";


                    const match =
                        disposition.match(
                            /filename="?([^";]+)"?/i
                        );


                    const filename =
                        match
                            ? match[1]
                            : (
                                activeExportId
                                + ".xlsx"
                            );


                    const url =
                        URL.createObjectURL(
                            blob
                        );


                    const link =
                        document.createElement(
                            "a"
                        );


                    link.href =
                        url;

                    link.download =
                        filename;


                    document.body.appendChild(
                        link
                    );

                    link.click();

                    link.remove();


                    URL.revokeObjectURL(
                        url
                    );

                }
                catch (error) {

                    console.error(
                        "SQDIP export error:",
                        error
                    );

                    alert(
                        error.message
                    );

                }
                finally {

                    exportButton.disabled =
                        false;
                }
            }
        );
    }
);