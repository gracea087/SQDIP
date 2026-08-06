"""Flask routes for SQDIP Charts.

Keep chart IDs and SQL on the server.

Do not accept SQL text, table names or column names from the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

from flask import Blueprint, jsonify, request

# Replace this import with the connection helper already used by the SQDIP app.
from database import get_db_connection


sqdip_charts_bp = Blueprint(
    "sqdip_charts",
    __name__
)


@dataclass(frozen=True)
class ChartDefinition:
    sql: str
    title: str
    x_label: str

    # left | both | centre
    axis: str = "left"

    # number | integer | percent | hours | minutes
    formatter: str = "number"

    parameters: Callable[
        [Mapping[str, str]],
        Sequence[Any]
    ] = lambda _args: ()

    meta: Mapping[str, Any] = field(
        default_factory=dict
    )


def month_parameters(
    args: Mapping[str, str]
) -> tuple[str, str]:
    """Return validated date parameters.

    For production, use the SQDIP application's existing
    date validation helper.
    """

    start_date = args.get(
        "start",
        date.today().replace(day=1).isoformat()
    )

    end_date = args.get(
        "end",
        date.today().isoformat()
    )

    return start_date, end_date


CHARTS: dict[str, ChartDefinition] = {
    "p13_coshh": ChartDefinition(
    sql="""
        SET LOCK_TIMEOUT 10000;

        SELECT
            CAST(
                ai.partNo AS varchar(255)
            ) AS y,

            DATEDIFF(
                day,
                converted.review_date,
                CAST(GETDATE() AS date)
            ) - 700 AS x

        FROM [Pcubed].[dbo].[allItems]
            AS ai WITH (READUNCOMMITTED)

        CROSS APPLY (
            VALUES (
                TRY_CONVERT(
                    date,
                    ai.coshh_DATE
                )
            )
        ) AS converted(review_date)

        WHERE
            converted.review_date
                < DATEADD(
                    day,
                    -700,
                    CAST(GETDATE() AS date)
                )

            AND ai.statusDescription
                <> 'OBSOLETE'

        ORDER BY
            x DESC,
            y ASC;
    """,

    title="CoSHH Reviews Over 700 Days Old",

    x_label="Days Over 700-Day Limit",

    formatter="integer",
),
    "I2a_wip": ChartDefinition(
        sql="""
        SELECT TOP(10) 
        CONCAT(
                CAST(WONo AS varchar(30)),
                ' | ',
                CAST(WOQtyOS AS varchar(20)),
                ' | ',
                COALESCE(
                    CAST(WOPartNo AS varchar(100)),
                    ''
                )
            ) AS y, 
                WOSchedStartDate,
                DATEDIFF(DAY,  WOSchedStartDate, GETDATE()) as x
        FROM [Pcubed].[dbo].[worksOrder] 
        WHERE WOQTYOS > 0 
        AND WOStatusDescription = 'WIP'
        AND WOpartno NOT LIKE '%-REPAIR' 
        AND WOPARTNO NOT LIKE '%-RETURN'
        order by WOSchedStartDate ASC;
        """
        ,

    title="WIP - Days since WO Start Date (Oldest 10)",

    x_label="Days Since WO Start Date (Scheduled)",

    formatter="integer",
    )
}


def json_value(value: Any) -> Any:
    """Convert pyodbc and SQL Server values into JSON-safe values."""

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


@sqdip_charts_bp.get(
    "/api/sqdip/chart/<string:chart_id>"
)
def get_sqdip_chart(chart_id: str):
    """Execute a registered chart query and return y/x graph data."""

    definition = CHARTS.get(chart_id)

    if definition is None:
        return jsonify({
            "error": "Unknown SQDIP chart.",
            "chartId": chart_id
        }), 404

    parameters = definition.parameters(
        request.args
    )

    connection = None
    cursor = None

    try:
        print(
            f"SQDIP chart starting: {chart_id}",
            flush=True
        )

        connection = get_db_connection()

        # Prevent any graph query from occupying a
        # Waitress worker indefinitely.
        connection.timeout = 20

        cursor = connection.cursor()

        cursor.execute(
            definition.sql,
            *parameters
        )

        if cursor.description is None:
            raise RuntimeError(
                f"Chart '{chart_id}' returned "
                "no SQL result set."
            )

        column_names = [
            column[0]
            for column in cursor.description
        ]

        records = [
            dict(zip(column_names, row))
            for row in cursor.fetchall()
        ]

        data = []

        for record in records:
            item = {
                "y": str(
                    record.get("y", "")
                ),

                "x": json_value(
                    record.get("x")
                ),
            }

            for optional_key in (
                "tooltip",
                "id",
                "className"
            ):
                if optional_key in record:
                    item[optional_key] = (
                        json_value(
                            record[optional_key]
                        )
                    )

            data.append(item)

        print(
            f"SQDIP chart completed: "
            f"{chart_id} ({len(data)} rows)",
            flush=True
        )

        return jsonify({
            "meta": {
                "title": definition.title,
                "xLabel": definition.x_label,
                "axis": definition.axis,
                "formatter":
                    definition.formatter,
                **dict(definition.meta),
            },

            "data": data,
        })

    except Exception as error:
        print(
            f"SQDIP chart failed: "
            f"{chart_id}: {error}",
            flush=True
        )

        return jsonify({
            "error": str(error),
            "chartId": chart_id
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()