"use strict";

/*
 * SQDIP Charts
 * Lightweight, dependency-free horizontal bar chart library.
 *
 * Public API:
 *   SQDIPCharts.create(target, options)
 *   SQDIPCharts.render(target, payload, options)
 *   SQDIPCharts.load(target, url, options)
 *   SQDIPCharts.mountButtons(options)
 *   SQDIPCharts.registerFormatter(name, formatter)
 *
 * Expected payload:
 * {
 *   "meta": {
 *     "title": "Hours by part number",
 *     "xLabel": "Hours",
 *     "axis": "left",           // left | both | centre
 *     "formatter": "hours",
 *     "min": 0,
 *     "max": null
 *   },
 *   "data": [
 *     { "y": "PART-001", "x": 12.5 },
 *     { "y": "PART-002", "x": 8.0 }
 *   ]
 * }
 */

(function initialiseSQDIPCharts(global) {
    const SVG_NS = "http://www.w3.org/2000/svg";
    const instances = new WeakMap();
    const formatters = new Map();

    const DEFAULTS = Object.freeze({
        axis: "left",
        title: "",
        subtitle: "",
        xLabel: "",
        targetKey: "target",
        targetStartKey: "targetStart",
        formatter: "number",
        min: null,
        max: null,
        symmetric: true,
        tickCount: 5,
        minHeight: 280,
        rowHeight: null,
        barHeightRatio: 0.62,
        leftLabelWidth: null,
        rightLabelWidth: null,
        centreLabelWidth: null,
        showValues: true,
        showGrid: true,
        showZeroLine: true,
        emptyMessage: "No data is available for this graph.",
        loadingMessage: "Loading graph…",
        errorMessage: "The graph could not be loaded.",
        ariaLabel: "Horizontal bar chart",
        valueKey: "x",
        labelKey: "y",
        tooltipKey: "tooltip",
        idKey: "id",
        classKey: "className",
        sort: "none",             // none | ascending | descending | label
        zeroValueText: "0",
        maxLabelCharacters: 80,
        resizeDebounceMs: 80,
        rightValueKey: "rightValue",
        rightValueFormatter: "number",
        rightValueWidth: null,
        rightValueLabel: "",
        showRowSeparators: false,
        orientation: "horizontal",
        yLabel: "",
        secondaryValueKey:
            "secondaryValue",
        secondaryValueFormatter:
            "number",
        secondaryValueLabel:
            "",
        targetBandStart:
            null,
        targetBandEnd:
            null,
    });

    formatters.set("number", value => new Intl.NumberFormat("en-GB", {
        maximumFractionDigits: 2
    }).format(value));

    formatters.set("integer", value => new Intl.NumberFormat("en-GB", {
        maximumFractionDigits: 0
    }).format(value));

    formatters.set("percent", value => `${new Intl.NumberFormat("en-GB", {
        maximumFractionDigits: 1
    }).format(value)}%`);

    formatters.set("hours", value => `${new Intl.NumberFormat("en-GB", {
        maximumFractionDigits: 2
    }).format(value)} h`);

    formatters.set("minutes", value => `${new Intl.NumberFormat("en-GB", {
        maximumFractionDigits: 0
    }).format(value)} min`);

    formatters.set(
    "currency",
    value => new Intl.NumberFormat(
        "en-GB",
        {
            style: "currency",
            currency: "GBP",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    ).format(value)
);

    function resolveElement(target) {
        if (target instanceof Element) {
            return target;
        }

        if (typeof target === "string") {
            const element = document.querySelector(target);
            if (element) {
                return element;
            }
        }

        throw new Error("SQDIPCharts: graph target was not found.");
    }

    function createSvgElement(name, attributes = {}, text = null) {
        const element = document.createElementNS(SVG_NS, name);

        Object.entries(attributes).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                element.setAttribute(key, String(value));
            }
        });

        if (text !== null && text !== undefined) {
            element.textContent = String(text);
        }

        return element;
    }

    function normaliseAxis(axis) {
        const value = String(axis || "left").toLowerCase();
        return ["left", "both", "centre"].includes(value) ? value : "left";
    }

    function safeNumber(value) {
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
    }

    function cssNumber(element, propertyName, fallback) {
        const raw = getComputedStyle(element).getPropertyValue(propertyName).trim();
        const value = Number.parseFloat(raw);
        return Number.isFinite(value) ? value : fallback;
    }

    function escapeClassNames(value) {
        return String(value || "")
            .split(/\s+/)
            .filter(Boolean)
            .map(item => item.replace(/[^a-zA-Z0-9_-]/g, "-"))
            .join(" ");
    }

    function truncate(text, maximumCharacters) {
        const value = String(text ?? "");
        if (value.length <= maximumCharacters) {
            return value;
        }
        return `${value.slice(0, Math.max(0, maximumCharacters - 1))}…`;
    }

    function debounce(callback, delayMs) {
        let timeoutId = null;
        return (...args) => {
            window.clearTimeout(timeoutId);
            timeoutId = window.setTimeout(() => callback(...args), delayMs);
        };
    }

    function mergeOptions(base, extra) {
        return {
            ...base,
            ...(extra || {}),
            axis: normaliseAxis(extra?.axis ?? base.axis)
        };
    }

    function normalisePayload(payload, options) {
        const source = payload && typeof payload === "object" ? payload : {};
        const metadata = source.meta && typeof source.meta === "object" ? source.meta : {};
        const mergedOptions = mergeOptions(options, metadata);
        const sourceRows = Array.isArray(source.data)
            ? source.data
            : (Array.isArray(source.rows) ? source.rows : []);

        const rows = sourceRows
            .map((row, index) => {
                const item = row && typeof row === "object" ? row : {};
                const value = safeNumber(item[mergedOptions.valueKey]);

                if (value === null) {
                    return null;
                }

                return {
                    index,
                    id: item[mergedOptions.idKey] ?? index,
                    label: truncate(
                        item[mergedOptions.labelKey] ?? "",
                        mergedOptions.maxLabelCharacters
                    ),
                    fullLabel: String(item[mergedOptions.labelKey] ?? ""),
                    value,
                    target: safeNumber(
                        item[mergedOptions.targetKey]
                    ),
                    targetStart: safeNumber(
                        item[mergedOptions.targetStartKey]
                    ),
                    tooltip: item[mergedOptions.tooltipKey] ?? null,
                    className: escapeClassNames(
                        item[mergedOptions.classKey]
                    ),

                    raw: item,

                    rightValue: safeNumber(
                        item[
                            mergedOptions.rightValueKey
                        ]
                    ),

                    secondaryValue: safeNumber(
                        item[
                            mergedOptions
                                .secondaryValueKey
                        ]
                    ),
                };
            })
            .filter(Boolean);

        switch (mergedOptions.sort) {
            case "ascending":
                rows.sort((a, b) => a.value - b.value);
                break;

            case "descending":
                rows.sort((a, b) => b.value - a.value);
                break;

            case "label":
                rows.sort((a, b) => a.label.localeCompare(
                    b.label,
                    "en-GB",
                    { numeric: true }
                ));
                break;

            default:
                break;
        }

        return {
            options: mergedOptions,
            rows
        };
    }

    function niceStep(rawStep) {
        if (!Number.isFinite(rawStep) || rawStep <= 0) {
            return 1;
        }

        const exponent = Math.floor(Math.log10(rawStep));
        const fraction = rawStep / (10 ** exponent);
        let niceFraction;

        if (fraction <= 1) {
            niceFraction = 1;
        } else if (fraction <= 2) {
            niceFraction = 2;
        } else if (fraction <= 5) {
            niceFraction = 5;
        } else {
            niceFraction = 10;
        }

        return niceFraction * (10 ** exponent);
    }

    function calculateScale(rows, options) {
        const values = rows.flatMap(row => {
        const rowValues = [
            row.value
        ];

        if (row.target !== null) {
            rowValues.push(
                row.target
            );
        }

        if (row.targetStart !== null) {
            rowValues.push(
                row.targetStart
            );
        }

        if (
            row.secondaryValue !== null
        ) {
            rowValues.push(
                row.secondaryValue
            );
        }

        const targetBandStart =
            safeNumber(
                options.targetBandStart
            );

        const targetBandEnd =
            safeNumber(
                options.targetBandEnd
            );

        if (
            targetBandStart !== null
        ) {
            values.push(
                targetBandStart
            );
        }

        if (
            targetBandEnd !== null
        ) {
            values.push(
                targetBandEnd
            );
        }
        return rowValues;
    });

        let minimum = options.min !== null
            ? safeNumber(options.min)
            : Math.min(0, ...values);

        let maximum = options.max !== null
            ? safeNumber(options.max)
            : Math.max(0, ...values);

        minimum = minimum ?? 0;
        maximum = maximum ?? 0;

        if (options.axis === "centre" && options.symmetric !== false) {
            const absoluteMaximum = Math.max(
                Math.abs(minimum),
                Math.abs(maximum),
                1
            );

            minimum = -absoluteMaximum;
            maximum = absoluteMaximum;
        }

        if (minimum === maximum) {
            if (minimum === 0) {
                maximum = 1;
            } else {
                const padding = Math.abs(minimum) * 0.1 || 1;
                minimum -= padding;
                maximum += padding;
            }
        }

        const tickTarget = Math.max(
            2,
            Number(options.tickCount) || 5
        );

        const rawStep = (maximum - minimum) / tickTarget;
        const step = niceStep(rawStep);

        let niceMinimum = Math.floor(minimum / step) * step;
        let niceMaximum = Math.ceil(maximum / step) * step;

        if (options.min !== null) {
            niceMinimum = minimum;
        }

        if (options.max !== null) {
            niceMaximum = maximum;
        }

        const ticks = [];
        const guardLimit = 100;
        let guard = 0;

        for (
            let value = niceMinimum;
            value <= niceMaximum + step / 2 && guard < guardLimit;
            value += step
        ) {
            const rounded = Math.abs(value) < step / 100000
                ? 0
                : Number(value.toPrecision(12));

            ticks.push(rounded);
            guard += 1;
        }

        return {
            minimum: niceMinimum,
            maximum: niceMaximum,
            ticks
        };
    }

    function getFormatter(formatterOption) {
        if (typeof formatterOption === "function") {
            return formatterOption;
        }

        return formatters.get(String(formatterOption))
            || formatters.get("number");
    }

    class HorizontalBarChart {
        constructor(target, options = {}) {
            this.target = resolveElement(target);
            this.options = mergeOptions(DEFAULTS, options);
            this.rows = [];
            this.payload = null;
            this.abortController = null;
            this.destroyed = false;

            this.target.classList.add("sqdip-chart");
            this.target.setAttribute("aria-live", "polite");

            this.handleResize = debounce(() => {
                if (!this.destroyed && this.rows.length > 0) {
                    this.draw();
                }
            }, this.options.resizeDebounceMs);

            if (typeof ResizeObserver === "function") {
                this.resizeObserver = new ResizeObserver(this.handleResize);
                this.resizeObserver.observe(this.target);
            } else {
                window.addEventListener("resize", this.handleResize);
            }
        }

        setOptions(options = {}) {
            this.options = mergeOptions(this.options, options);

            if (this.payload) {
                this.setData(this.payload);
            }

            return this;
        }

        setData(payload) {
            this.payload = payload;

            const normalised = normalisePayload(
                payload,
                this.options
            );

            this.options = normalised.options;
            this.rows = normalised.rows;
            this.draw();

            return this;
        }

        async load(url, fetchOptions = {}) {
            if (!url) {
                throw new Error(
                    "SQDIPCharts: no graph URL was supplied."
                );
            }

            if (this.abortController) {
                this.abortController.abort();
            }

            this.abortController = new AbortController();

            this.showStatus(
                "loading",
                this.options.loadingMessage
            );

            try {
                const {
                    headers = {},
                    ...requestOptions
                } = fetchOptions;

                const response = await fetch(url, {
                    credentials: "same-origin",
                    ...requestOptions,
                    headers: {
                        Accept: "application/json",
                        ...headers
                    },
                    signal: this.abortController.signal
                });

                if (!response.ok) {
                    const responseText = await response.text();

                    throw new Error(
                        `HTTP ${response.status}: ${
                            responseText || response.statusText
                        }`
                    );
                }

                const payload = await response.json();
                this.setData(payload);

                return payload;
            } catch (error) {
                if (error.name === "AbortError") {
                    return null;
                }

                console.error(
                    "SQDIPCharts load error:",
                    error
                );

                this.showStatus(
                    "error",
                    this.options.errorMessage,
                    error.message
                );

                throw error;
            }
        }

        showStatus(type, message, detail = "") {
            this.target.replaceChildren();
            this.target.dataset.state = type;

            const wrapper = document.createElement("div");

            wrapper.className =
                `sqdip-chart__status sqdip-chart__status--${type}`;

            const messageElement = document.createElement("p");

            messageElement.className =
                "sqdip-chart__status-message";

            messageElement.textContent = message;
            wrapper.appendChild(messageElement);

            if (detail) {
                const detailElement = document.createElement("p");

                detailElement.className =
                    "sqdip-chart__status-detail";

                detailElement.textContent = detail;
                wrapper.appendChild(detailElement);
            }

            this.target.appendChild(wrapper);
        }

        draw() {
            if (this.destroyed) {
                return;
            }

            if (this.rows.length === 0) {
                this.showStatus(
                    "empty",
                    this.options.emptyMessage
                );

                return;
            }

            if (
                this.options.orientation
                    === "vertical"
            ) {
                this.drawVertical();
                return;
            }

            this.target.dataset.state = "ready";
            this.target.dataset.axis = this.options.axis;
            this.target.replaceChildren();

            const width = Math.max(
                this.target.clientWidth,
                320
            );

            const hasRightValues =
                this.rows.some(
                    row =>
                        row.rightValue !== null
                );

            const rowHeight = this.options.rowHeight
                ?? cssNumber(
                    this.target,
                    "--sqdip-row-height",
                    38
                );

            const topPadding = cssNumber(
                this.target,
                "--sqdip-padding-top",
                this.options.title ? 74 : 44
            );

            const bottomPadding = cssNumber(
                this.target,
                "--sqdip-padding-bottom",
                58
            );

            const outerPadding = cssNumber(
                this.target,
                "--sqdip-padding-inline",
                18
            );

            const valueGap = cssNumber(
                this.target,
                "--sqdip-value-gap",
                8
            );

            const axisLabelGap = cssNumber(
                this.target,
                "--sqdip-axis-label-gap",
                10
            );

            const minimumPlotWidth = 120;

            const height = Math.max(
                this.options.minHeight,
                topPadding
                    + bottomPadding
                    + (this.rows.length * rowHeight)
            );

            this.target.style.setProperty(
                "--sqdip-computed-height",
                `${height}px`
            );

            
            const layout = this.calculateLayout({
                width,
                height,
                rowHeight,
                topPadding,
                bottomPadding,
                outerPadding,
                minimumPlotWidth,
                hasRightValues
            });

            const scale = calculateScale(
                this.rows,
                this.options
            );

            const formatValue = getFormatter(
                this.options.formatter
            );

            const formatRightValue =
                getFormatter(
                    this.options
                        .rightValueFormatter
                );

            const xPosition = value => {
                const ratio = (
                    value - scale.minimum
                ) / (
                    scale.maximum - scale.minimum
                );

                return layout.plotLeft
                    + (ratio * layout.plotWidth);
            };

            const zeroX = xPosition(0);

            const targetBandGroup =
                createSvgElement(
                    "g",
                    {
                        class:
                            "sqdip-chart__target-band-group"
                    }
                );

            const svg = createSvgElement("svg", {
                class: "sqdip-chart__svg",
                viewBox: `0 0 ${width} ${height}`,
                width: "100%",
                height,
                role: "img",
                "aria-label": this.options.ariaLabel,
                preserveAspectRatio: "xMidYMin meet"
            });

            const targetBandStart =
                safeNumber(
                    this.options
                        .targetBandStart
                );

            const targetBandEnd =
                safeNumber(
                    this.options
                        .targetBandEnd
                );

            if (
                targetBandStart !== null
                && targetBandEnd !== null
            ) {

                const targetStartX =
                    xPosition(
                        targetBandStart
                    );

                const targetEndX =
                    xPosition(
                        targetBandEnd
                    );

                targetBandGroup.appendChild(
                    createSvgElement(
                        "rect",
                        {
                            class:
                                "sqdip-chart__target-band",

                            x:
                                Math.min(
                                    targetStartX,
                                    targetEndX
                                ),

                            y:
                                layout.plotTop,

                            width:
                                Math.abs(
                                    targetEndX
                                    - targetStartX
                                ),

                            height:
                                layout.plotBottom
                                - layout.plotTop
                        }
                    )
                );
            }

            const title = createSvgElement(
                "title",
                {},
                this.options.title
                    || this.options.ariaLabel
            );
            
            const targetsGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__targets"
                }
            );
            svg.appendChild(title);

            if (this.options.title) {
                svg.appendChild(createSvgElement(
                    "text",
                    {
                        class: "sqdip-chart__title",
                        x: outerPadding,
                        y: 28
                    },
                    this.options.title
                ));
            }

            if (this.options.subtitle) {
                svg.appendChild(createSvgElement(
                    "text",
                    {
                        class: "sqdip-chart__subtitle",
                        x: outerPadding,
                        y: this.options.title ? 50 : 28
                    },
                    this.options.subtitle
                ));
            }

            const gridGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__grid"
                }
            );

            const rowSeparatorsGroup =
                createSvgElement(
                    "g",
                    {
                        class:
                            "sqdip-chart__row-separators"
                    }
                );

            const axisGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__axes"
                }
            );

            const barsGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__bars"
                }
            );

            const secondaryBarsGroup =
                createSvgElement(
                    "g",
                    {
                        class:
                            "sqdip-chart__secondary-bars"
                    }
                );

            const secondaryValuesGroup =
                createSvgElement(
                    "g",
                    {
                        class:
                            "sqdip-chart__secondary-values"
                    }
                );

            const labelsGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__labels"
                }
            );

            const valuesGroup = createSvgElement(
                "g",
                {
                    class: "sqdip-chart__values"
                }
            );

            const rightValuesGroup =
                createSvgElement(
                    "g",
                    {
                        class:
                            "sqdip-chart__right-values"
                    }
                );

            scale.ticks.forEach(tick => {
                const x = xPosition(tick);

                if (this.options.showGrid) {
                    gridGroup.appendChild(createSvgElement(
                        "line",
                        {
                            class:
                                `sqdip-chart__grid-line${
                                    tick === 0
                                        ? " sqdip-chart__grid-line--zero"
                                        : ""
                                }`,
                            x1: x,
                            y1: layout.plotTop,
                            x2: x,
                            y2: layout.plotBottom
                        }
                    ));
                }

                // Bottom X-axis numbers
                axisGroup.appendChild(createSvgElement(
                    "text",
                    {
                        class:
                            "sqdip-chart__tick-label "
                            + "sqdip-chart__tick-label--bottom",
                        x,
                        y: layout.plotBottom + 23,
                        "text-anchor": "middle"
                    },
                    formatValue(tick)
                ));

                // Top X-axis numbers
                axisGroup.appendChild(createSvgElement(
                    "text",
                    {
                        class:
                            "sqdip-chart__tick-label "
                            + "sqdip-chart__tick-label--top",
                        x,
                        y: layout.plotTop - 10,
                        "text-anchor": "middle"
                    },
                    formatValue(tick)
                ));
            });

            axisGroup.appendChild(createSvgElement(
                "line",
                {
                    class: "sqdip-chart__x-axis",
                    x1: layout.plotLeft,
                    y1: layout.plotBottom,
                    x2: layout.plotRight,
                    y2: layout.plotBottom
                }
            ));

            // Top X-axis
            axisGroup.appendChild(createSvgElement(
                "line",
                {
                    class:
                        "sqdip-chart__x-axis "
                        + "sqdip-chart__x-axis--top",
                    x1: layout.plotLeft,
                    y1: layout.plotTop,
                    x2: layout.plotRight,
                    y2: layout.plotTop
                }
            ));

            if (
                this.options.showZeroLine
                && scale.minimum <= 0
                && scale.maximum >= 0
            ) {
                axisGroup.appendChild(createSvgElement(
                    "line",
                    {
                        class: "sqdip-chart__zero-line",
                        x1: zeroX,
                        y1: layout.plotTop,
                        x2: zeroX,
                        y2: layout.plotBottom
                    }
                ));
            }

            if (this.options.xLabel) {

            const xLabelCentre =
                layout.plotLeft
                + (layout.plotWidth / 2);


            // Bottom X-axis label
            axisGroup.appendChild(createSvgElement(
                "text",
                {
                    class:
                        "sqdip-chart__x-label "
                        + "sqdip-chart__x-label--bottom",

                    x: xLabelCentre,

                    y: height - 12,

                    "text-anchor": "middle"
                },
                this.options.xLabel
            ));


            // Top X-axis label
            axisGroup.appendChild(createSvgElement(
                "text",
                {
                    class:
                        "sqdip-chart__x-label "
                        + "sqdip-chart__x-label--top",

                    x: xLabelCentre,

                    y: layout.plotTop - 32,

                    "text-anchor": "middle"
                },
                this.options.xLabel
            ));
        }
            this.rows.forEach((row, rowIndex) => {
                const rowTop = layout.plotTop
                    + (rowIndex * rowHeight);

                const centreY = rowTop
                    + (rowHeight / 2);

                /*
                * Optional horizontal line
                * separating each graph row.
                */
                if (
                    this.options.showRowSeparators
                    && rowIndex < this.rows.length - 1
                ) {
                    const separatorY =
                        rowTop + rowHeight;

                    rowSeparatorsGroup.appendChild(
                        createSvgElement(
                            "line",
                            {
                                class:
                                    "sqdip-chart__row-separator",

                                x1:
                                    outerPadding,

                                y1:
                                    separatorY,

                                x2:
                                    width - outerPadding,

                                y2:
                                    separatorY
                            }
                        )
                    );
                }

                if (row.rightValue !== null) {

                    rightValuesGroup.appendChild(
                        createSvgElement(
                            "text",
                            {
                                class:
                                    "sqdip-chart__right-value",

                                x:
                                    width
                                    - outerPadding,

                                y:
                                    centreY,

                                "dominant-baseline":
                                    "middle",

                                "text-anchor":
                                    "end"
                            },

                            formatRightValue(
                                row.rightValue
                            )
                        )
                    );
                }

                const barHeight = Math.max(
                    2,
                    rowHeight
                        * this.options.barHeightRatio
                );

                if (
                row.secondaryValue
                    !== null
            ) {

                const secondaryX =
                    xPosition(
                        row.secondaryValue
                    );

                const secondaryBarX =
                    Math.min(
                        zeroX,
                        secondaryX
                    );

                const secondaryBarWidth =
                    Math.max(
                        Math.abs(
                            secondaryX
                            - zeroX
                        ),
                        1
                    );

                secondaryBarsGroup
                    .appendChild(
                        createSvgElement(
                            "rect",
                            {
                                class:
                                    "sqdip-chart__secondary-bar",

                                x:
                                    secondaryBarX,

                                y:
                                    centreY
                                    - (
                                        barHeight
                                        / 2
                                    ),

                                width:
                                    secondaryBarWidth,

                                height:
                                    barHeight,

                                rx:
                                    2
                            }
                        )
                    );


                const formatSecondary =
                    getFormatter(
                        this.options
                            .secondaryValueFormatter
                    );


                /*
                * Display the due-days number
                * in the middle of the yellow bar.
                */
                secondaryValuesGroup
                    .appendChild(
                        createSvgElement(
                            "text",
                            {
                                class:
                                    "sqdip-chart__secondary-value",

                                x:
                                    (
                                        zeroX
                                        + secondaryX
                                    ) / 2,

                                y:
                                    centreY,

                                "dominant-baseline":
                                    "middle",

                                "text-anchor":
                                    "middle"
                            },

                            formatSecondary(
                                row.secondaryValue
                            )
                        )
                    );
            }

                const valueX = xPosition(row.value);
                const barX = Math.min(zeroX, valueX);

                if (row.target !== null) {
                    const targetX = xPosition(
                        row.target
                    );

                    const targetStartValue =
                        row.targetStart !== null
                            ? row.targetStart
                            : row.value;

                    const targetStartX = xPosition(
                        targetStartValue
                    );

                    const lineStartX = Math.min(
                        targetStartX,
                        targetX
                    );

                    const lineEndX = Math.max(
                        targetStartX,
                        targetX
                    );
                    targetsGroup.appendChild(
                        createSvgElement(
                            "line",
                            {
                                class:
                                    "sqdip-chart__target-line",
                                x1: lineStartX,
                                y1: centreY,
                                x2: lineEndX,
                                y2: centreY
                            }
                        )
                    );

                    targetsGroup.appendChild(
                        createSvgElement(
                            "line",
                            {
                                class:
                                    "sqdip-chart__target-marker",
                                x1: targetX,
                                y1: centreY - (barHeight / 2),
                                x2: targetX,
                                y2: centreY + (barHeight / 2)
                            }
                        )
                    );
                }

                const barWidth = Math.max(
                    Math.abs(valueX - zeroX),
                    row.value === 0 ? 1 : 0
                );

                const stateClass = row.value < 0
                    ? "sqdip-chart__bar--negative"
                    : (
                        row.value > 0
                            ? "sqdip-chart__bar--positive"
                            : "sqdip-chart__bar--zero"
                    );

                const customClass = row.className
                    ? ` ${row.className}`
                    : "";

                const bar = createSvgElement(
                    "rect",
                    {
                        class:
                            `sqdip-chart__bar ${stateClass}${customClass}`,
                        x: barX,
                        y: centreY - (barHeight / 2),
                        width: barWidth,
                        height: barHeight,
                        rx: cssNumber(
                            this.target,
                            "--sqdip-bar-radius",
                            3
                        ),
                        tabindex: 0,
                        "data-row-id": row.id,
                        "data-value": row.value
                    }
                );

                const tooltipText = row.tooltip
                    ? String(row.tooltip)
                    : `${row.fullLabel}: ${
                        formatValue(row.value)
                    }`;

                bar.appendChild(createSvgElement(
                    "title",
                    {},
                    tooltipText
                ));

                barsGroup.appendChild(bar);

                this.drawCategoryLabels(
                    labelsGroup,
                    {
                        row,
                        centreY,
                        layout,
                        zeroX,
                        axisLabelGap
                    }
                );

                if (this.options.showValues) {
                    const valueIsPositive =
                        row.value >= 0;

                    let textX = valueIsPositive
                        ? valueX + valueGap
                        : valueX - valueGap;

                    let anchor = valueIsPositive
                        ? "start"
                        : "end";

                    const estimatedTextWidth = Math.max(
                        28,
                        formatValue(row.value).length * 7
                    );

                    if (
                        valueIsPositive
                        && textX + estimatedTextWidth
                            > layout.plotRight
                    ) {
                        textX = valueX - valueGap;
                        anchor = "end";
                    } else if (
                        !valueIsPositive
                        && textX - estimatedTextWidth
                            < layout.plotLeft
                    ) {
                        textX = valueX + valueGap;
                        anchor = "start";
                    }

                    valuesGroup.appendChild(createSvgElement(
                        "text",
                        {
                            class:
                                `sqdip-chart__value ${
                                    row.value < 0
                                        ? "sqdip-chart__value--negative"
                                        : "sqdip-chart__value--positive"
                                }`,
                            x: textX,
                            y: centreY,
                            "dominant-baseline": "middle",
                            "text-anchor": anchor
                        },
                        row.value === 0
                            ? this.options.zeroValueText
                            : formatValue(row.value)
                    ));
                }
            });

           svg.append(
                gridGroup,
                rowSeparatorsGroup,
                barsGroup,
                targetsGroup,
                axisGroup,
                labelsGroup,
                valuesGroup,
                rightValuesGroup
            );

            this.target.appendChild(svg);
        }
        
        drawVertical() {
    this.target.dataset.state =
        "ready";

    this.target.replaceChildren();

    const width = Math.max(
        this.target.clientWidth,
        320
    );

    const height = Math.max(
        this.options.minHeight,
        380
    );

    const leftPadding = 60;
    const rightPadding = 20;
    const topPadding =
        this.options.title
            ? 75
            : 45;

    const bottomPadding = 75;

    const plotLeft =
        leftPadding;

    const plotRight =
        width - rightPadding;

    const plotTop =
        topPadding;

    const plotBottom =
        height - bottomPadding;

    const plotWidth =
        plotRight - plotLeft;

    const plotHeight =
        plotBottom - plotTop;

    const scale = calculateScale(
        this.rows,
        {
            ...this.options,
            min:
                this.options.min
                ?? 0
        }
    );

    const formatValue =
        getFormatter(
            this.options.formatter
        );

    const yPosition =
        value => {

            const ratio =
                (
                    value
                    - scale.minimum
                )
                /
                (
                    scale.maximum
                    - scale.minimum
                );

            return (
                plotBottom
                - (
                    ratio
                    * plotHeight
                )
            );
        };

    const zeroY =
        yPosition(0);

    const svg =
        createSvgElement(
            "svg",
            {
                class:
                    "sqdip-chart__svg "
                    + "sqdip-chart__svg--vertical",

                viewBox:
                    `0 0 ${width} ${height}`,

                width:
                    "100%",

                height,

                role:
                    "img",

                "aria-label":
                    this.options.ariaLabel,

                preserveAspectRatio:
                    "xMidYMin meet"
            }
        );


    /*
     * Graph title
     */
    if (this.options.title) {
        svg.appendChild(
            createSvgElement(
                "text",
                {
                    class:
                        "sqdip-chart__title",

                    x:
                        leftPadding,

                    y:
                        28
                },

                this.options.title
            )
        );
    }


    const gridGroup =
        createSvgElement(
            "g",
            {
                class:
                    "sqdip-chart__grid"
            }
        );

    const axisGroup =
        createSvgElement(
            "g",
            {
                class:
                    "sqdip-chart__axes"
            }
        );

    const barsGroup =
        createSvgElement(
            "g",
            {
                class:
                    "sqdip-chart__bars"
            }
        );

    const labelsGroup =
        createSvgElement(
            "g",
            {
                class:
                    "sqdip-chart__labels"
            }
        );

    const valuesGroup =
        createSvgElement(
            "g",
            {
                class:
                    "sqdip-chart__values"
            }
        );


    /*
     * Horizontal value grid lines
     * and Y-axis values.
     */
    scale.ticks.forEach(
        tick => {

            const y =
                yPosition(tick);

            if (
                this.options.showGrid
            ) {
                gridGroup.appendChild(
                    createSvgElement(
                        "line",
                        {
                            class:
                                "sqdip-chart__grid-line",

                            x1:
                                plotLeft,

                            y1:
                                y,

                            x2:
                                plotRight,

                            y2:
                                y
                        }
                    )
                );
            }

            axisGroup.appendChild(
                createSvgElement(
                    "text",
                    {
                        class:
                            "sqdip-chart__tick-label",

                        x:
                            plotLeft - 10,

                        y:
                            y,

                        "dominant-baseline":
                            "middle",

                        "text-anchor":
                            "end"
                    },

                    formatValue(
                        tick
                    )
                )
            );
        }
    );


    /*
     * X-axis
     */
    axisGroup.appendChild(
        createSvgElement(
            "line",
            {
                class:
                    "sqdip-chart__x-axis",

                x1:
                    plotLeft,

                y1:
                    zeroY,

                x2:
                    plotRight,

                y2:
                    zeroY
            }
        )
    );


    /*
     * Y-axis
     */
    axisGroup.appendChild(
        createSvgElement(
            "line",
            {
                class:
                    "sqdip-chart__zero-line",

                x1:
                    plotLeft,

                y1:
                    plotTop,

                x2:
                    plotLeft,

                y2:
                    plotBottom
            }
        )
    );


    const columnWidth =
        plotWidth
        / this.rows.length;

    const barWidth =
        Math.max(
            6,
            Math.min(
                columnWidth * 0.62,
                70
            )
        );


    this.rows.forEach(
        (row, index) => {

            const centreX =
                plotLeft
                + (
                    columnWidth
                    * index
                )
                + (
                    columnWidth
                    / 2
                );

            const valueY =
                yPosition(
                    row.value
                );

            const barTop =
                Math.min(
                    valueY,
                    zeroY
                );

            const barHeight =
                Math.max(
                    1,
                    Math.abs(
                        zeroY
                        - valueY
                    )
                );


            /*
             * Vertical bar.
             */
            const bar =
                createSvgElement(
                    "rect",
                    {
                        class:
                            "sqdip-chart__bar "
                            + (
                                row.value < 0
                                    ? "sqdip-chart__bar--negative"
                                    : "sqdip-chart__bar--positive"
                            ),

                        x:
                            centreX
                            - (
                                barWidth
                                / 2
                            ),

                        y:
                            barTop,

                        width:
                            barWidth,

                        height:
                            barHeight,

                        rx:
                            cssNumber(
                                this.target,
                                "--sqdip-bar-radius",
                                3
                            )
                    }
                );


            bar.appendChild(
                createSvgElement(
                    "title",
                    {},

                    `${row.fullLabel}: ${
                        formatValue(
                            row.value
                        )
                    }`
                )
            );

            barsGroup.appendChild(
                bar
            );


            /*
             * Month beneath bar.
             */
            labelsGroup.appendChild(
                createSvgElement(
                    "text",
                    {
                        class:
                            "sqdip-chart__category-label",

                        x:
                            centreX,

                        y:
                            plotBottom
                            + 24,

                        "text-anchor":
                            "middle"
                    },

                    row.label
                )
            );


                /*
                * Accident count above bar.
                */
                if (
                    this.options.showValues
                ) {
                    valuesGroup.appendChild(
                        createSvgElement(
                            "text",
                            {
                                class:
                                    "sqdip-chart__value",

                                x:
                                    centreX,

                                y:
                                    valueY
                                    - 8,

                                "text-anchor":
                                    "middle"
                            },

                            formatValue(
                                row.value
                            )
                        )
                    );
                }
            }
        );


            /*
            * X-axis title.
            */
            if (this.options.xLabel) {
                axisGroup.appendChild(
                    createSvgElement(
                        "text",
                        {
                            class:
                                "sqdip-chart__x-label",

                            x:
                                plotLeft
                                + (
                                    plotWidth
                                    / 2
                                ),

                            y:
                                height - 12,

                            "text-anchor":
                                "middle"
                        },

                        this.options.xLabel
                    )
                );
            }


            /*
            * Y-axis title.
            */
            if (this.options.yLabel) {
                axisGroup.appendChild(
                    createSvgElement(
                        "text",
                        {
                            class:
                                "sqdip-chart__x-label "
                                + "sqdip-chart__y-label",

                            x:
                                18,

                            y:
                                plotTop
                                + (
                                    plotHeight
                                    / 2
                                ),

                            transform:
                                `rotate(-90 18 ${
                                    plotTop
                                    + (
                                        plotHeight
                                        / 2
                                    )
                                })`,

                            "text-anchor":
                                "middle"
                        },

                        this.options.yLabel
                    )
                );
            }


            svg.append(
                gridGroup,

                targetBandGroup,

                barsGroup,

                secondaryBarsGroup,

                targetsGroup,

                axisGroup,

                labelsGroup,

                valuesGroup,

                secondaryValuesGroup,

                rightValuesGroup
            );

            this.target.appendChild(
                svg
            );
        }
        calculateLayout({
            width,
            height,
            rowHeight,
            topPadding,
            bottomPadding,
            outerPadding,
            minimumPlotWidth,
            hasRightValues
        }) {

            const configuredRightValueWidth =
                this.options.rightValueWidth
                ?? cssNumber(
                    this.target,
                    "--sqdip-right-value-width",
                    120
                );
            const configuredLeftWidth =
                this.options.leftLabelWidth
                ?? cssNumber(
                    this.target,
                    "--sqdip-left-label-width",
                    190
                );

            const configuredRightWidth =
                this.options.rightLabelWidth
                ?? cssNumber(
                    this.target,
                    "--sqdip-right-label-width",
                    190
                );

            const configuredCentreWidth =
                this.options.centreLabelWidth
                ?? cssNumber(
                    this.target,
                    "--sqdip-centre-label-width",
                    150
                );

            let plotLeft = outerPadding;
            let plotRight = width - outerPadding;
            if (hasRightValues) {
                plotRight -=
                    configuredRightValueWidth;
            }

            if (this.options.axis === "left") {
                plotLeft += configuredLeftWidth;
            } else if (this.options.axis === "both") {
                plotLeft += configuredLeftWidth;
                plotRight -= configuredRightWidth;
            } else if (this.options.axis === "centre") {
                /*
                 * Central labels are drawn over the zero axis.
                 * Keep the full plot width.
                 */
                this.computedCentreLabelWidth =
                    configuredCentreWidth;
            }

            if (
                plotRight - plotLeft
                < minimumPlotWidth
            ) {
                const availableWidth = Math.max(
                    minimumPlotWidth,
                    width - (outerPadding * 2)
                );

                plotLeft = outerPadding
                    + Math.max(
                        0,
                        (
                            availableWidth
                            - minimumPlotWidth
                        ) / 2
                    );

                plotRight = width - outerPadding;
            }

            const plotTop = topPadding;
            const plotBottom = height - bottomPadding;

            return {
                width,
                height,
                rowHeight,
                plotLeft,
                plotRight,
                plotWidth: Math.max(
                    1,
                    plotRight - plotLeft
                ),
                plotTop,
                plotBottom
            };
        }

        drawCategoryLabels(group, {
            row,
            centreY,
            layout,
            zeroX,
            axisLabelGap
        }) {
            const commonAttributes = {
                class: "sqdip-chart__category-label",
                y: centreY,
                "dominant-baseline": "middle"
            };

            if (
                this.options.axis === "left"
                || this.options.axis === "both"
            ) {
                const leftLabel = createSvgElement(
                    "text",
                    {
                        ...commonAttributes,
                        x: layout.plotLeft
                            - axisLabelGap,
                        "text-anchor": "end"
                    },
                    row.label
                );

                leftLabel.appendChild(createSvgElement(
                    "title",
                    {},
                    row.fullLabel
                ));

                group.appendChild(leftLabel);
            }

            if (this.options.axis === "both") {
                const rightLabel = createSvgElement(
                    "text",
                    {
                        ...commonAttributes,
                        x: layout.plotRight
                            + axisLabelGap,
                        "text-anchor": "start"
                    },
                    row.label
                );

                rightLabel.appendChild(createSvgElement(
                    "title",
                    {},
                    row.fullLabel
                ));

                group.appendChild(rightLabel);
            }

            if (this.options.axis === "centre") {
                const labelWidth =
                    this.computedCentreLabelWidth
                    ?? cssNumber(
                        this.target,
                        "--sqdip-centre-label-width",
                        150
                    );

                const labelHeight = Math.max(
                    18,
                    layout.rowHeight * 0.72
                );

                group.appendChild(createSvgElement(
                    "rect",
                    {
                        class:
                            "sqdip-chart__centre-label-background",
                        x: zeroX - (labelWidth / 2),
                        y: centreY - (labelHeight / 2),
                        width: labelWidth,
                        height: labelHeight,
                        rx: cssNumber(
                            this.target,
                            "--sqdip-centre-label-radius",
                            3
                        )
                    }
                ));

                const centreLabel = createSvgElement(
                    "text",
                    {
                        ...commonAttributes,
                        class:
                            "sqdip-chart__category-label "
                            + "sqdip-chart__category-label--centre",
                        x: zeroX,
                        "text-anchor": "middle"
                    },
                    row.label
                );

                centreLabel.appendChild(createSvgElement(
                    "title",
                    {},
                    row.fullLabel
                ));

                group.appendChild(centreLabel);
            }
        }

        destroy() {
            this.destroyed = true;

            if (this.abortController) {
                this.abortController.abort();
            }

            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            } else {
                window.removeEventListener(
                    "resize",
                    this.handleResize
                );
            }

            this.target.replaceChildren();
            instances.delete(this.target);
        }
    }

    function create(target, options = {}) {
        const element = resolveElement(target);
        const existing = instances.get(element);

        if (existing) {
            existing.setOptions(options);
            return existing;
        }

        const chart = new HorizontalBarChart(
            element,
            options
        );

        instances.set(element, chart);

        return chart;
    }

    function render(target, payload, options = {}) {
        return create(
            target,
            options
        ).setData(payload);
    }

    function load(
        target,
        url,
        options = {},
        fetchOptions = {}
    ) {
        return create(
            target,
            options
        ).load(
            url,
            fetchOptions
        );
    }

    function mountButtons({
        target,
        buttons = "[data-sqdip-chart]",
        endpointBase = "/api/sqdip/chart/",
        chartOptions = {},
        fetchOptions = {},
        autoLoad = true,
        activeClass = "is-active",
        onBeforeLoad = null,
        onLoaded = null,
        onError = null
    } = {}) {
        const targetElement = resolveElement(target);

        const buttonElements = Array.from(
            document.querySelectorAll(buttons)
        );

        const chart = create(
            targetElement,
            chartOptions
        );

        if (buttonElements.length === 0) {
            console.warn(
                "SQDIPCharts: no graph buttons were found."
            );
        }

        async function loadFromButton(button) {
            const chartId =
                button.dataset.sqdipChart;

            const explicitUrl =
                button.dataset.sqdipUrl;

            const url = explicitUrl
                || `${endpointBase}${
                    encodeURIComponent(chartId)
                }`;

            buttonElements.forEach(item => {
                const active = item === button;

                item.classList.toggle(
                    activeClass,
                    active
                );

                item.setAttribute(
                    "aria-pressed",
                    active ? "true" : "false"
                );
            });

            targetElement.dataset.chartId = chartId;

            if (typeof onBeforeLoad === "function") {
                onBeforeLoad({
                    chartId,
                    url,
                    button,
                    chart
                });
            }

            try {
                const payload = await chart.load(
                    url,
                    fetchOptions
                );

                if (
                    payload
                    && typeof onLoaded === "function"
                ) {
                    onLoaded({
                        chartId,
                        url,
                        button,
                        chart,
                        payload
                    });
                }
            } catch (error) {
                if (typeof onError === "function") {
                    onError({
                        chartId,
                        url,
                        button,
                        chart,
                        error
                    });
                }
            }
        }

        const buttonHandlers = new Map();

        buttonElements.forEach(button => {
            if (!button.hasAttribute("type")) {
                button.type = "button";
            }

            button.setAttribute(
                "aria-controls",
                targetElement.id || "sqdip-chart"
            );

            button.setAttribute(
                "aria-pressed",
                "false"
            );

            const handler = () =>
                loadFromButton(button);

            buttonHandlers.set(
                button,
                handler
            );

            button.addEventListener(
                "click",
                handler
            );
        });

        if (
            autoLoad
            && buttonElements.length > 0
        ) {
            const defaultButton =
                buttonElements.find(
                    button => button.hasAttribute(
                        "data-sqdip-default"
                    )
                ) || buttonElements[0];

            loadFromButton(defaultButton);
        }

        return {
            chart,

            load: chartId => {
                const matchingButton =
                    buttonElements.find(
                        button =>
                            button.dataset.sqdipChart
                            === chartId
                    );

                if (!matchingButton) {
                    throw new Error(
                        "SQDIPCharts: no button is "
                        + `configured for graph '${chartId}'.`
                    );
                }

                return loadFromButton(
                    matchingButton
                );
            },

            destroy: () => {
                buttonHandlers.forEach(
                    (handler, button) => {
                        button.removeEventListener(
                            "click",
                            handler
                        );
                    }
                );

                chart.destroy();
            }
        };
    }

    function mountFilterButtons({
    container,
    target,
    chartId,
    filterId,
    parameterName,

    endpointBase =
        "/api/sqdip/chart/",

    filterEndpointBase =
        "/api/sqdip/filter/",

    includeAll = true,
    allLabel = "ALL",

    buttonClass =
        "sqdip-chart-filter-button",

    activeClass =
        "is-active",

    fetchOptions = {}
} = {}) {

    if (
        !chartId
        || !filterId
        || !parameterName
    ) {
        throw new Error(
            "SQDIPCharts: filter "
            + "configuration is incomplete."
        );
    }


    const containerElement =
        resolveElement(
            container
        );

    const targetElement =
        resolveElement(
            target
        );

    const chart =
        create(
            targetElement
        );


    let selectedValue = "";


    function buildChartUrl(
        value
    ) {
        const parameters =
            new URLSearchParams();


        if (
            value !== null
            && value !== undefined
            && String(value).trim() !== ""
        ) {
            parameters.set(
                parameterName,
                String(value)
            );
        }


        const query =
            parameters.toString();


        return (
            `${endpointBase}`
            + `${encodeURIComponent(chartId)}`
            + (
                query
                    ? `?${query}`
                    : ""
            )
        );
    }


    function setActiveButton(
        selectedButton
    ) {
        const buttons =
            containerElement.querySelectorAll(
                "[data-sqdip-filter-value]"
            );


        buttons.forEach(
            button => {
                const active =
                    button ===
                    selectedButton;

                button.classList.toggle(
                    activeClass,
                    active
                );

                button.setAttribute(
                    "aria-pressed",
                    active
                        ? "true"
                        : "false"
                );
            }
        );
    }


    async function select(
        value,
        button = null
    ) {
        selectedValue =
            value ?? "";


        if (button) {
            setActiveButton(
                button
            );
        }


        const url =
            buildChartUrl(
                selectedValue
            );


        return chart.load(
            url,
            fetchOptions
        );
    }


   function createFilterButton(
    label,
    value
) {
    const button =
        document.createElement(
            "button"
        );

    button.type =
        "button";


    /*
     * Create unique CSS class
     * from filter value.
     *
     * MRB OTHER
     * -> filter-mrb-other
     *
     * MRD REWORK
     * -> filter-mrd-rework
     */
    const uniqueClass =
        value
            ? "filter-"
                + String(value)
                    .trim()
                    .toLowerCase()
                    .replace(
                        /[^a-z0-9]+/g,
                        "-"
                    )
                    .replace(
                        /^-+|-+$/g,
                        ""
                    )
            : "filter-all";


    button.className =
        `${buttonClass} ${uniqueClass}`;


    button.textContent =
        label;


    button.dataset
        .sqdipFilterValue =
            value;


    button.setAttribute(
        "aria-pressed",
        "false"
    );


    button.addEventListener(
        "click",
        () => {
            select(
                value,
                button
            );
        }
    );


    return button;
}


    async function refresh() {

        const {
            headers = {},
            ...requestOptions
        } = fetchOptions;


        const response =
            await fetch(
                (
                    `${filterEndpointBase}`
                    + encodeURIComponent(
                        filterId
                    )
                ),
                {
                    credentials:
                        "same-origin",

                    ...requestOptions,

                    headers: {
                        Accept:
                            "application/json",

                        ...headers
                    }
                }
            );


        if (!response.ok) {
            const text =
                await response.text();

            throw new Error(
                `Filter HTTP `
                + `${response.status}: `
                + `${text}`
            );
        }


        const payload =
            await response.json();


        const rows =
            Array.isArray(
                payload.data
            )
                ? payload.data
                : [];


        containerElement
            .replaceChildren();


        if (includeAll) {
            const allButton =
                createFilterButton(
                    allLabel,
                    ""
                );

            containerElement
                .appendChild(
                    allButton
                );


            if (
                selectedValue === ""
            ) {
                setActiveButton(
                    allButton
                );
            }
        }


        rows.forEach(
            row => {

                const value =
                    String(
                        row.value ?? ""
                    );

                const label =
                    String(
                        row.label
                        ?? value
                    );


                if (!value) {
                    return;
                }


                const button =
                    createFilterButton(
                        label,
                        value
                    );


                containerElement
                    .appendChild(
                        button
                    );


                if (
                    value ===
                    selectedValue
                ) {
                    setActiveButton(
                        button
                    );
                }
            }
        );


        containerElement.hidden =
            false;


        return rows;
    }


    return {
        chart,

        refresh,

        select,

        show: () => {
            containerElement.hidden =
                false;
        },

        hide: () => {
            containerElement.hidden =
                true;
        },

        getSelectedValue:
            () => selectedValue
    };
}

    function registerFormatter(name, formatter) {
        if (
            !name
            || typeof formatter !== "function"
        ) {
            throw new TypeError(
                "SQDIPCharts.registerFormatter "
                + "requires a name and function."
            );
        }

        formatters.set(
            String(name),
            formatter
        );
    }

    global.SQDIPCharts = Object.freeze({
        version: "1.1.0",

        create,
        render,
        load,

        mountButtons,
        mountFilterButtons,

        registerFormatter
    });
})
(window);