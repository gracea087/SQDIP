# SQDIP Charts

A small, dependency-free SVG library for horizontal bar graphs in the SQDIP Flask application.

## Why SVG

SVG is a better fit than canvas for this requirement because bars, labels, grid lines and values are real DOM elements.

They can be styled with normal CSS classes and CSS variables.

No CDN, npm package or external JavaScript import is required.

## Files

Copy these files into the SQDIP application:

```text
static/
├── css/
│   ├── sqdip-charts.css
│   └── sqdip-page.css
└── js/
    ├── sqdip-charts.js
    └── sqdip-page.js

templates/
└── sqdip-page.html
```

The Flask routes can be incorporated into `app.py`, although a separate Blueprint is recommended:

```text
routes/
└── sqdip_charts.py
```

## Data contract

Every SQL query must return these aliases:

```sql
SELECT
    SomeCategory AS y,
    SomeNumericValue AS x
FROM ...;
```

The route returns:

```json
{
    "meta": {
        "title": "Hours by part number",
        "xLabel": "Hours",
        "axis": "left",
        "formatter": "hours"
    },
    "data": [
        {
            "y": "PART-001",
            "x": 12.5
        },
        {
            "y": "PART-002",
            "x": 8.0
        }
    ]
}
```

Optional row properties:

- `tooltip`: custom hover or focus text.
- `id`: row identifier placed in `data-row-id`.
- `className`: CSS class added to the bar, for example `warning`.

## Axis modes

### Normal left axis

```json
"axis": "left"
```

Category names are shown on the left and bars extend from zero.

### Labels on both sides

```json
"axis": "both"
```

The same category name is shown on the left and right of the plotting area.

### Central axis

```json
"axis": "centre"
```

Negative values extend left, positive values extend right and the category name is displayed over the zero line.

By default, the scale is symmetrical around zero.

## Minimal page JavaScript

When buttons use `data-sqdip-chart`, the complete page JavaScript is:

```javascript
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    SQDIPCharts.mountButtons({
        target: "#sqdipGraph",
        buttons: "[data-sqdip-chart]",
        endpointBase: "/api/sqdip/chart/"
    });
});
```

A button's graph ID is the route key:

```html
<button
    type="button"
    data-sqdip-chart="hours_by_part"
>
    Hours by part
</button>
```

It automatically requests:

```text
/api/sqdip/chart/hours_by_part
```

Use `data-sqdip-default` on the graph button that should load when the page opens.

A button can also use a completely different URL:

```html
<button
    type="button"
    data-sqdip-chart="custom_graph"
    data-sqdip-url="/another/api/route"
>
    Custom graph
</button>
```

## Adding a new graph

1. Add a server-side definition to `CHARTS`.
2. Make the SQL return `y` and `x`.
3. Add one HTML button with the same chart ID.
4. No graph-specific JavaScript is required.

Example:

```python
"rework_hours": ChartDefinition(
    sql="""
        SELECT
            CAST(EmployeeName AS varchar(100)) AS y,
            SUM(Hours) AS x

        FROM dbo.TimeMain

        WHERE Activity = 'Rework'

        GROUP BY EmployeeName

        ORDER BY x DESC;
    """,
    title="Rework hours by employee",
    x_label="Hours",
    axis="left",
    formatter="hours",
),
```

```html
<button
    type="button"
    data-sqdip-chart="rework_hours"
>
    Rework hours
</button>
```

## CSS styling

Prefer page-level variable overrides:

```css
#sqdipGraph {
    --sqdip-positive-bar: #1d72b8;
    --sqdip-negative-bar: #d4351c;
    --sqdip-grid: #d8dde2;
    --sqdip-row-height: 42px;
    --sqdip-left-label-width: 230px;
    --sqdip-label-size: 13px;
}
```

Style selected records by returning `className` from SQL or the API:

```sql
SELECT
    Department AS y,
    YieldPercent AS x,

    CASE
        WHEN YieldPercent < 95
            THEN 'warning'
        ELSE 'target-met'
    END AS className

FROM ...;
```

```css
#sqdipGraph .warning {
    fill: #d9822b;
}

#sqdipGraph .target-met {
    fill: #2f9e44;
}
```

## Built-in formatters

- `number`
- `integer`
- `percent`
- `hours`
- `minutes`

Register an application-specific formatter once:

```javascript
SQDIPCharts.registerFormatter(
    "pounds",
    value => new Intl.NumberFormat(
        "en-GB",
        {
            style: "currency",
            currency: "GBP"
        }
    ).format(value)
);
```

Then return:

```json
"formatter": "pounds"
```

## Date filters

Existing date fields can reload the selected graph by adding their values as query parameters.

Example page setup:

```javascript
const controller = SQDIPCharts.mountButtons({
    target: "#sqdipGraph",
    buttons: "[data-sqdip-chart]",
    endpointBase: "/api/sqdip/chart/",
    fetchOptions: {
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    }
});
```

For a page with date fields, the route can read the same query parameters used elsewhere in the SQDIP application.

## No internal scrolling

The chart height is calculated as:

```text
header space
+ footer space
+ number of rows × row height
```

The SVG and graph element grow to that height.

Every bar is rendered.

The graph itself does not use `overflow-y: auto` or an internal scrollbar.

With a very large result set, the normal web page may become long. This is intentional and keeps all bars visible and printable.

## Isolation from the test database application

The library is isolated by design:

- It creates only `window.SQDIPCharts`.
- It does not create or overwrite `window.Chart`.
- All CSS classes start with `sqdip-chart`.
- It only modifies the graph target supplied to it.
- It does not change global canvas, SVG or button styles.
- It can coexist with Chart.js on another page.
- It can also coexist with Chart.js on the same page.
- The API prefix `/api/sqdip/chart/` avoids collisions with existing report endpoints.

For additional separation:

- Keep the SQDIP routes in a Blueprint.
- Only load `sqdip-charts.js` on SQDIP templates.
- Only load `sqdip-charts.css` on SQDIP templates.
- Do not include these files globally in `base.html` unless every page needs them.

## Production recommendations

- Keep the `CHARTS` dictionary server-side.
- Whitelist graph IDs.
- Do not send table names, column names or SQL from the browser.
- Parameterise all SQL values.
- Apply authentication and role decorators where required.
- Add indexes for date and filter columns used by frequently refreshed graphs.
- Return aggregated data rather than thousands of raw database records.
- Use SQL `ORDER BY` when the order has business meaning.
- Version `sqdip-charts.js` separately.
- Test chart library changes in the sandbox before deployment.