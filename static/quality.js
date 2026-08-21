"use strict";

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const graphPanel =
            document.getElementById(
                "QualityGraphPanel"
            );

        const graphTarget =
            document.getElementById(
                "QualityGraph"
            );

        const exportButton =
            document.getElementById(
                "exportQualityButton"
            );


        if (
            !graphPanel
            || !graphTarget
            || !exportButton
        ) {
            console.error(
                "The Quality page "
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
                "#QualityGraph",

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
                             * Not a JSON response.
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