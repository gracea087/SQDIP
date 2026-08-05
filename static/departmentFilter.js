"use strict";

/*
 * Every code must exactly match the HTML element ID.
 */
const departmentButtons = {
    all: [
        "S1",
        "Q1",
        "Q2",
        "Q3",
        "Q6",
        "Q7",
        "Q8",
        "Q8b",
        "Q9",
        "D1a1",
        "D1a2",
        "D1b",
        "D1c",
        "D1d",
        "D2",
        "D3a",
        "D3b",
        "D4",
        "D5",
        "D7",
        "D8",
        "D9",
        "D10",
        "D11",
        "D12",
        "I2a",
        "I2b",
        "I3",
        "I4",
        "I6",
        "I7",
        "I8",
        "I9",
        "I10",
        "I11",
        "I12",
        "I13",
        "I14",
        "I15",
        "P1",
        "P2",
        "P3a",
        "P3b",
        "P4",
        "P5",
        "P6",
        "P8",
        "P9",
        "P10",
        "P11",
        "P12",
        "P13"
    ],

    com: [
        "S1",
        "Q7",
        "P3a",
        "P5",
        "P8"
    ],

    eng: [
        "S1",
        "Q1",
        "Q3",
        "Q7",
        "Q8b",
        "I8",
        "I15",
        "P1",
        "P2",
        "P3a",
        "P3b",
        "P4",
        "P8",
        "P9",
        "P10",
        "P11",
        "P12",
        "P13"
    ],

    man: [
        "S1",
        "Q2",
        "Q7",
        "D1c",
        "D10",
        "I2a",
        "I3",
        "I4",
        "I6",
        "I7",
        "I9",
        "I12",
        "I13",
        "P3a",
        "P3b",
        "P8"
    ],

    pur: [
        "S1",
        "Q2",
        "Q7",
        "D1a1",
        "D1a2",
        "D1b",
        "D1d",
        "D2",
        "D3b",
        "D4",
        "D7",
        "D8",
        "D9",
        "D10",
        "D11",
        "I12",
        "I14",
        "I15",
        "P3a",
        "P3b",
        "P6",
        "P8"
    ],

    qa: [
        "S1",
        "Q2",
        "Q7",
        "Q8",
        "Q9",
        "I2b",
        "P3a",
        "P8"
    ]
};

const departmentDisplayNames = {
    all: "ALL DEPARTMENTS",
    com: "COMMERCIAL",
    eng: "ENGINEERING",
    man: "MANUFACTURING",
    pur: "PURCHASING",
    qa: "QUALITY"
};

/*
 * Every item that can be controlled by the filter.
 */
const allDepartmentButtonIds = new Set(
    departmentButtons.all
);

/*
 * Accept both abbreviated and full department names.
 */
function normaliseDepartment(value) {
    const department = String(value || "")
        .trim()
        .toLowerCase();

    const mappings = {
        all: "all",

        com: "com",
        commercial: "com",

        eng: "eng",
        engineering: "eng",

        man: "man",
        manufacturing: "man",

        pur: "pur",
        purchasing: "pur",

        qa: "qa",
        quality: "qa"
    };

    return mappings[department] || "all";
}

function updateDepartmentDisplay(department) {
    const departmentDisplay =
        document.getElementById("current-department");

    if (!departmentDisplay) {
        return;
    }

    const normalisedDepartment =
        normaliseDepartment(department);

    departmentDisplay.textContent =
        departmentDisplayNames[normalisedDepartment]
        || "ALL DEPARTMENTS";
}

function applyDepartmentFilter(department) {
    const normalisedDepartment =
        normaliseDepartment(department);

    updateDepartmentDisplay(normalisedDepartment);

    const selectedButtonIds =
        normalisedDepartment === "all"
            ? allDepartmentButtonIds
            : new Set(
                departmentButtons[normalisedDepartment] || []
            );

    allDepartmentButtonIds.forEach(function (buttonId) {
        const element = document.getElementById(buttonId);

        /*
         * Items on other pages will not exist in the current DOM.
         */
        if (!element) {
            return;
        }

        const shouldShow =
            selectedButtonIds.has(buttonId);

        element.classList.toggle(
            "department-hidden",
            !shouldShow
        );
    });

    console.log(
        "Department selected:",
        normalisedDepartment
    );

    console.log(
        "Buttons allowed:",
        [...selectedButtonIds]
    );
}

function initialiseDepartmentFilter() {
    const departmentSelect =
        document.getElementById("department-select");

    if (!departmentSelect) {
        console.error(
            "Department dropdown #department-select was not found."
        );
        return;
    }

    const savedDepartment =
        normaliseDepartment(
            localStorage.getItem("selectedDepartment") || "all"
        );

    departmentSelect.value = savedDepartment;

    localStorage.setItem(
        "selectedDepartment",
        savedDepartment
    );

    applyDepartmentFilter(savedDepartment);

    departmentSelect.addEventListener(
        "change",
        function () {
            const department =
                normaliseDepartment(departmentSelect.value);

            localStorage.setItem(
                "selectedDepartment",
                department
            );

            applyDepartmentFilter(department);
        }
    );
}

document.addEventListener(
    "DOMContentLoaded",
    initialiseDepartmentFilter
);