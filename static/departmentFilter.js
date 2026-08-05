"use strict";

/*
 * Button visibility by department.
 *
 * Button names must match the HTML element IDs exactly.
 */
const departmentButtons = {
    all: [
        "S1",
        "Q1",
        "Q2",
        "Q3",
        "Q6",
        "Q7",
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
    ]

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

/*
 * Produces one complete list of every controlled button.
 *
 * Set removes duplicates such as S1, Q7 and P8.
 */
const allDepartmentButtonIds = new Set(
    Object.values(departmentButtons).flat()
);

function applyDepartmentFilter(department) {
    const normalisedDepartment = String(department)
        .trim()
        .toLowerCase();

    const selectedButtonIds =
        normalisedDepartment === "all"
            ? allDepartmentButtonIds
            : new Set(
                departmentButtons[normalisedDepartment] || []
            );

    allDepartmentButtonIds.forEach(function (buttonId) {
        const element = document.getElementById(buttonId);

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

    const validDepartments = [
        "all",
        "com",
        "eng",
        "man",
        "pur",
        "qa"
    ];

    let savedDepartment =
        localStorage.getItem("selectedDepartment") || "all";

    savedDepartment = String(savedDepartment)
        .trim()
        .toLowerCase();

    /*
     * Convert old saved values from the previous dropdown.
     */
    const oldValueMappings = {
        All: "all",
        Com: "com",
        Eng: "eng",
        Man: "man",
        Pur: "pur",
        QA: "qa"
    };

    savedDepartment =
        oldValueMappings[savedDepartment]
        || savedDepartment;

    if (!validDepartments.includes(savedDepartment)) {
        savedDepartment = "all";
    }

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
                departmentSelect.value;

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