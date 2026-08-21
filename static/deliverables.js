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

/////////////////////////////////// EXPORT TO EXCEL ////////////////////////////////////
<script>
document.addEventListener("DOMContentLoaded", function () {
    const previewApiUrl =
        "{{ url_for('deliverables') }}";

    const exportApiUrl =
        "{{ url_for('deliverables_export') }}";

    const exportButton =
        document.getElementById("exportDeliverablesButton");



    function setStatus(message, type = "") {
        statusElement.textContent = message;

        statusElement.classList.remove(
            "is-error",
            "is-success"
        );

        if (type) {
            statusElement.classList.add(type);
        }
    }

    function addTableCell(tableRow, value) {
        const cell = document.createElement("td");

        cell.textContent = (
            value === null || value === undefined
                ? ""
                : String(value)
        );

        tableRow.appendChild(cell);
    }


    function renderDeliverablesRows(rows) {
        tableBody.replaceChildren();

        if (!rows.length) {
            const emptyRow = document.createElement("tr");
            const emptyCell = document.createElement("td");

            emptyCell.colSpan = 7;
            emptyCell.className = "Deliverables-empty-row";
            emptyCell.textContent =
                "No Deliverables entries were found for this date range.";

            emptyRow.appendChild(emptyCell);
            tableBody.appendChild(emptyRow);

            rowCount.textContent = "0 entries";
            exportButton.disabled = true;

            return;
        }

        rows.forEach(function (entry) {
            const tableRow = document.createElement("tr");

            // get column names from sql
            addTableCell(tableRow, qry.${});
            addTableCell(tableRow, qry.${});
            addTableCell(tableRow, qry.${});
            addTableCell(tableRow, qry.${});

            addTableCell(
                tableRow,
                formatDisplayDate(entry.date)
            );

            addTableCell(tableRow, entry.notes);

            addTableCell(
                tableRow,
                Number(entry.hours || 0).toFixed(2)
            );

            tableBody.appendChild(tableRow);
        });

        const description = (
            rows.length === 1
                ? "1 entry"
                : `${rows.length} entries`
        );

        rowCount.textContent = description;
        exportButton.disabled = false;
    }


    async function loadDeliverables() {
        try {

            loadButton.disabled = true;
            exportButton.disabled = true;

            setStatus("Loading Deliverables data...");

            const response = await fetch(
                `${previewApiUrl}?${query.toString()}`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error ||
                    "The Deliverables could not be loaded."
                );
            }

            renderDeliverablesRows(data.rows);

            setStatus(
                `${data.count} Deliverables entries loaded.`,
                "is-success"
            );

        } catch (error) {
            console.error(
                "Deliverables load error:",
                error
            );

            renderDeliverablesRows([]);

            setStatus(
                error.message,
                "is-error"
            );

        } finally {
            loadButton.disabled = false;
        }
    }


    async function exportDeliverables() {
        try {
            const dates = getSelectedDates();

            exportButton.disabled = true;

            setStatus("Creating Excel workbook...");

            const response = await fetch(
                `${exportApiUrl}?${query.toString()}`,
                {
                    method: "GET"
                }
            );

            if (!response.ok) {
                let errorMessage =
                    "The Excel workbook could not be generated.";

                try {
                    const errorData = await response.json();

                    if (errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (parseError) {
                    console.error(
                        "Export error response was not JSON:",
                        parseError
                    );
                }

                throw new Error(errorMessage);
            }

            const workbookBlob = await response.blob();

            const contentDisposition =
                response.headers.get(
                    "Content-Disposition"
                ) || "";

            const filenameMatch =
                contentDisposition.match(
                    /filename="?([^";]+)"?/i
                );

            const filename = filenameMatch
                ? filenameMatch[1]
                : (
                        `QRY_Exp_${data-sqdip-chart}_${Exp-title}.xls`
                );

            const downloadUrl =
                URL.createObjectURL(workbookBlob);

            const downloadLink =
                document.createElement("a");

            downloadLink.href = downloadUrl;
            downloadLink.download = filename;

            document.body.appendChild(downloadLink);
            downloadLink.click();
            downloadLink.remove();

            URL.revokeObjectURL(downloadUrl);

            setStatus(
                "Excel workbook created successfully.",
                "is-success"
            );

        } catch (error) {
            console.error(
                "Deliverables export error:",
                error
            );

            setStatus(
                error.message,
                "is-error"
            );

        } finally {
            exportButton.disabled = false;
        }
    }


    const today = new Date();

    const firstDayOfMonth = new Date(
        today.getFullYear(),
        today.getMonth(),
        1
    );

    startDateInput.value =
        formatInputDate(firstDayOfMonth);

    endDateInput.value =
        formatInputDate(today);

    loadButton.addEventListener(
        "click",
        loadDeliverables
    );

    exportButton.addEventListener(
        "click",
        exportDeliverables
    );

    startDateInput.addEventListener(
        "change",
        function () {
            exportButton.disabled = true;
        }
    );

    endDateInput.addEventListener(
        "change",
        function () {
            exportButton.disabled = true;
        }
    );

    loadDeliverables();
});