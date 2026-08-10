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

@dataclass(frozen=True)
class FilterDefinition:
    sql: str


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

FILTERS: dict[str, FilterDefinition] = {

    "grn_location": FilterDefinition(
        sql="""
            SELECT DISTINCT
                CAST(
                    GRNLocation AS varchar(255)
                ) AS value,

                CAST(
                    GRNLocation AS varchar(255)
                ) AS label

            FROM [Pcubed].[dbo].[AllLiveGRN]

            WHERE
                GRNLocation IS NOT NULL

                AND LTRIM(
                    RTRIM(GRNLocation)
                ) <> ''

                AND GRNLocation LIKE 'MRB%'

            ORDER BY
                label;
        """
    ),

}

def q2_location_parameters(
    args: Mapping[str, str]
) -> tuple[str]:
    location = (
        args.get(
            "location",
            ""
        )
        or ""
    ).strip()


    if location:
        return (
            f"%{location}%",
        )


    # Default Q2 display:
    # show all MR locations.
    return (
        "MR%",
    )

CHARTS: dict[str, ChartDefinition] = {
    "p13_coshh": ChartDefinition(
    sql="""

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
    ),
    "I2b_wip": ChartDefinition(
        sql="""
        SELECT 
            WOPartNo as y, 
            DATEDIFF(DAY, GETDATE(), WOSchedStartDate) as x
        FROM [Pcubed].[dbo].[worksOrder]
        WHERE WOStatusDescription = 'On Hold'
        order by WOSchedStartDate ASC;
        """,
        title="WIP - Works Orders ON-HOLD",

        x_label="Days",

        formatter="integer",
    ),
    "I6_location": ChartDefinition(
        sql="""
        SELECT TOP (20)
            LEFT(
                CONCAT(wo.WONo,' | ',COALESCE(wo.WOJobType, ''),' | ',COALESCE(wo.WOPartNo, '')), 80) AS y,
                DATEDIFF(DAY,wo.WOSchedStartDate,GETDATE()) AS x
        FROM [Pcubed].[dbo].[worksOrder] AS wo
        WHERE wo.WOSchedStartDate IS NOT NULL
            AND DATEDIFF(DAY,wo.WOSchedStartDate,GETDATE()) > 0
            AND (wo.WOJobType IS NULL
            OR (wo.WOJobType NOT LIKE 'PR%'
            AND wo.WOJobType NOT IN (
                        'SMT',
                        'TEST',
                        'QA',
                        'CONCOAT',
                        'SUB CONTRACTOR',
                        'ENGINEERING WIP',
                        'KITTING ON HOLD',
                        'MATERIAL SALES',
                        'SUB CON - TO BE SENT',
                        'PENDING CUSTOMER'
                    )))

            AND wo.WOStatusDescription NOT IN (
                'Completed',
                'Total Qty Received',
                'On Hold'
            )

            AND wo.WOPartNo NOT LIKE '%FAI REPORT'
            AND wo.WOPartNo <> 'SMT ATTRITION'
            AND wo.WOPartNo <> 'ADDITIONAL CHARGE'
            AND wo.WOPartNo <> 'EXCESS MATERIAL'
            AND wo.WOPartNo NOT LIKE '%FAIR%'
            AND wo.WOPartNo <> 'CONSUMABLE ISSUES'
            AND wo.WOPartNo NOT LIKE '%WRITE-OFF'
            AND wo.WOPartNo NOT LIKE '%-RETURN'
            AND wo.WOPartNo NOT LIKE '%-REPAIR'

        ORDER BY
            X DESC;
        """,
        title="Works Orders not in Prod Location (Top 20)",

        x_label="Days Since WO Start Date (Scheduled)",

        formatter="integer",
    ),
    "Q3_customer": ChartDefinition(
        sql="""
        SELECT
            CONCAT([WONo], ' (', [WOPartNo], ')') AS y,
            DATEDIFF(DAY,WOSchedFinishDate,GETDATE()) AS x
        FROM
            [Pcubed].[dbo].[worksOrder]
        WHERE
            (
                (([Pcubed].[dbo].[worksOrder].WOQtyOS) > 0)
                AND (([Pcubed].[dbo].[worksOrder].WOJobType) = 'PENDING CUSTOMER')
            )
        ORDER BY
            x ASC;
        """,
        title="WO's Pending Customer Query",

        x_label="Days Untill Scheduled Finish",

        formatter="integer",
    ),
    "I10_material": ChartDefinition(
        sql="""
        SELECT
            CONCAT([WONo], '|', [WOPartNo]) AS y,
            DATEDIFF(DAY,GETDATE(),WOSchedStartDate) AS x
        FROM
            [Pcubed].[dbo].[worksOrder]
            LEFT JOIN AllItems ON [Pcubed].[dbo].[worksOrder].WOPartNo = AllItems.PartNo
        WHERE
            (
                (([Pcubed].[dbo].[worksOrder].WOPartNo) NOT LIKE 'PROCEDURES')
                AND (([Pcubed].[dbo].[worksOrder].WOEarliestStartDate) = '12 / 12 / 2012')
                AND (([Pcubed].[dbo].[worksOrder].WOStatusDescription) NOT LIKE 'Completed')
            )
        ORDER BY
            x DESC;
        """,
        title="Material Only WO (Start Date 12/12/12)",

        x_label="Days Untill Scheduled Start",

        formatter="integer",
    ),
    "D1a1": ChartDefinition(
        sql="""
        SELECT
            CONCAT([PONum], '/', [PODetItemNum], ' : ', [PODetPart] ,' : ' , [POSuppAddressName],50) AS y,
            DATEDIFF(DAY,PODetDatePromised,GETDATE()) AS x
        FROM [Pcubed].[dbo].[AllLivePO]
        WHERE
            (
                (DATEDIFF(DAY,PODetDatePromised,GETDATE())) > 0)
                AND (([Pcubed].[dbo].[AllLivePO].PODetDatePromised) > '1 / 1 / 2019 ')
                AND (
                    ([Pcubed].[dbo].[AllLivePO].PODetDateLatest) NOT LIKE '1 / 1 / 2001 '
                    AND ([Pcubed].[dbo].[AllLivePO].PODetDateLatest) NOT LIKE '8 / 8 / 2008 '
                    AND ([Pcubed].[dbo].[AllLivePO].PODetDateLatest) NOT LIKE '9 / 9 / 2009 '
                    AND ([Pcubed].[dbo].[AllLivePO].PODetDateLatest) NOT LIKE '10 / 10 / 2010 '
                )
        ORDER BY x DESC;
        """,
        title="Overdue Purchase Orders (Promised)",

        x_label="Days Late",

        formatter="integer",
    ),
    "D1b": ChartDefinition(
        sql="""
        SELECT
            LEFT(CONCAT([PONum],'/',[PODetItemNum],' : ',[PODetPart],' : ',[POSuppAddressName]),50) AS y,
            DATEDIFF(DAY,GETDATE(),[PODetDateReq]) AS x
        FROM [Pcubed].[dbo].[AllLivePO]
        WHERE
            CAST([PODetDatePromised] AS date) = '2081-12-25'
            OR
            CAST([PODetDateLatest] AS date) = '2081-12-25'
        ORDER BY x ASC;
        """,
        title="Unkown Delivery Date Purchase Orders",

        x_label="Days Untill PO Required Date",

        formatter="integer",
    ),
    "D1c": ChartDefinition(
        sql="""
        SELECT
            LEFT(CONCAT([PONum],'/',[PODetItemNum],' : ',[PODetPart],' : ',[POSuppAddressName]),50) AS y,
            DATEDIFF(DAY,[PODetDatePromised],GETDATE()) AS x
        FROM [Pcubed].[dbo].[AllLivePO]
        WHERE DATEDIFF(DAY,[PODetDatePromised],GETDATE()) > 1
            AND [PODetDatePromised] > '2019-01-01'
            AND [PODetDateLatest] = '2008-08-08'
        ORDER BY x DESC;
        """,
        title="Overdue Purchase Orders (Recieved not Booked In)",

        x_label="Days Untill PO Required Date",

        formatter="integer",
    ),
    "D1d": ChartDefinition(
        sql="""
        SELECT
            LEFT(CONCAT([PONum], '/',[PODetItemNum],' : ',[PODetPart],' : ',[POSuppAddressName]),50) AS y,
            DATEDIFF(DAY,[PODetDatePromised],GETDATE()) AS x,
            5 AS target
        FROM [Pcubed].[dbo].[AllLivePO]
        WHERE
            DATEDIFF(DAY,[PODetDatePromised],GETDATE()) > 0
            AND [PODetDatePromised] > '2019-01-01'
            AND [PODetDateLatest] IN ('2008-08-08','2009-09-09','2010-10-10')
        ORDER BY x DESC;
        """,
        title="Overdue Purchase Orders - Confirmed Shipped",

        x_label="Days Late",

        formatter="integer",
    ),
    "P6": ChartDefinition(
        sql="""
        SELECT DISTINCT TOP (20)
            CONCAT([PONum], ' / ',[Name],' / ',LEFT([POSuppAddressName], 15)) AS y,
            DATEDIFF(DAY,[POSentDate],GETDATE()) AS x,
            0 AS targetStart,
            7 AS target
        FROM [Pcubed].[dbo].[AllLivePO]
        INNER JOIN [Pcubed].[dbo].[employees]
            ON [Pcubed].[dbo].[AllLivePO].[POBuyer] = [Pcubed].[dbo].[employees].[BadgeNo]
        WHERE
            CAST([PODetDatePromised] AS date) NOT IN (
                '2081-01-04',
                '2081-12-25'
            )
            AND [POSubmitted] = 1
            AND [POConfirmation] = 0
            AND [POSentDate] IS NOT NULL
        ORDER BY x DESC;
        """,
        title="PO's waiting Confirmation (Top 20)",

        x_label="Days Since PO Submitted",

        formatter="integer",
    ),
    "Q2_grn": ChartDefinition(
        sql="""
            SELECT
                CONCAT(grn.[GRNNo],' <',grn.[GRNLocation],'> ',grn.[GRNPartNo]) AS y,
                DATEDIFF(DAY,MAX(tr.[TransferDate]),GETDATE()) AS x,
                0 AS targetStart,
                7 AS target
            FROM
                [Pcubed].[dbo].[AllLiveGRN] AS grn
            LEFT JOIN [Pcubed].[dbo].[AllGRN_Transfer] AS tr
                ON grn.[GRNNo]= tr.[TransferGRNNo]
                AND grn.[GRNLineNo] = tr.[TranferGRNLineNo]
            WHERE grn.[GRNLocation] LIKE ?
            GROUP BY
                grn.[GRNNo],
                grn.[GRNLocation],
                grn.[GRNPartNo]
            ORDER BY x DESC;
        """,

        title="Stock in MRB Locations",

        x_label="Days",

        formatter="integer",

        parameters=q2_location_parameters,
    ),
    "D4": ChartDefinition(
        sql="""
            WITH Qry_RiskOrderPendAppr AS
            (SELECT po.PONum, po.PODetItemNum, po.POSuppAddressName, MIN(po.PODetDateReq) AS FirstOfPODetDateReq,po.PODetDatePromised,
                SUM(po.PODetQtyReq  * po.PODetUnitPrice) AS PoValue,emp.Name
                FROM [Pcubed].[dbo].[AllLivePO] AS po
            INNER JOIN [Pcubed].[dbo].[employees] AS emp ON po.POBuyer = emp.BadgeNo
            WHERE CAST(po.PODetDatePromised AS date) = '2081-04-01'
            GROUP BY po.PONum, po.PODetItemNum, po.POSuppAddressName, po.PODetDatePromised, emp.Name )

            SELECT LEFT(CONCAT(PONum,'/',PODetItemNum,' # ',Name, ' # ',POSuppAddressName),50) AS y,
            DATEDIFF(DAY, GETDATE(), FirstOfPODetDateReq) AS x,
            PoValue AS rightValue
            FROM Qry_RiskOrderPendAppr

            ORDER BY x ASC;
        """,

        title=
            "Risk Orders Pending Approval",

        x_label=
            "Days Until PO Required Date",

        formatter=
            "integer",

        meta={
            "rightValueFormatter":
                "currency",

            "rightValueLabel":
                "PO Value",
            
            "showRowSeparators":
            True
        },
    ),
    "Q9": ChartDefinition(
        sql="""
        SELECT
            CONCAT(grn.GRNNo,'/',grn.GRNLineNo,' (X',grn.GRNQtyLeft, ') ',grn.GRNPartNo) AS y,
            DATEDIFF(DAY,MAX(tr.TransferDate),GETDATE()) AS x
        FROM [Pcubed].[dbo].[AllLiveGRN] AS grn
        LEFT JOIN [Pcubed].[dbo].[AllGRN_Transfer] AS tr
            ON grn.GRNLineNo = tr.TranferGRNLineNo
            AND grn.GRNNo = tr.TransferGRNNo
        WHERE grn.GRNLocation = 'QUARANTINE' AND tr.TransferLocation = 'QUARANTINE'
        GROUP BY
            grn.GRNNo,
            grn.GRNLineNo,
            grn.GRNQtyLeft,
            grn.GRNPartNo
        ORDER BY x DESC;
        """,
        title=
            "Stock in QUARANTINE",

        x_label=
            "Days in Quarantine",

        formatter=
            "integer",
    ),
    "D7": ChartDefinition(
        sql="""
        SELECT
            LEFT(CONCAT([PONum],' # ',[POSuppAddressName]),14) AS y,
            DATEDIFF(DAY,[POOrderDate],GETDATE()) AS x,
            7 AS target
        FROM [Pcubed].[dbo].[AllLivePO]
        WHERE CAST([PODetDatePromised] AS date) <> '2081-04-01'
            AND [POSubmitted] = 0
        GROUP BY
            [PONum],
            [POOrderDate],
            [POSuppAddressName],
            [POSubmitted]
        ORDER BY x DESC;
        """,
        title=
            "PO Not Submitted",

        x_label=
            "Days Since PO Entered",

        formatter=
            "integer",
    ),
    "I8": ChartDefinition(
        sql="""
        SELECT
            CONCAT([GRNNo],' (X',[GRNQtyLeft],') ',[GRNPartNo]) AS y,
            DATEDIFF(DAY,[GRNDateReceived],GETDATE()) AS x,
            5 AS target
        FROM [Pcubed].[dbo].[AllLiveGRN]
        WHERE [GRNLocation] = 'GREY MARKET INSPECTION'
        ORDER BY x DESC;
        """,
        title=
            "Grey Market Inspection",

        x_label=
            "Days",

        formatter=
            "integer",
    ),
    "D1a2": ChartDefinition(
        sql="""
        WITH Qry_Exp_D1a2_LatePOReq AS
            (SELECT po.PONum AS PO, po.PODetItemNum, po.PODetPart, po.PODetPartDescr, po.POSuppAddressName, emp.Name AS Buyer,
            DATEDIFF(DAY,CAST(po.PODetDateReq AS date),CAST(GETDATE() AS date)) AS DaysLate,po.PODetDateReq,
            MAX(po.PODetDatePromised) AS MaxOfPODetDatePromised,
            po.PODetDateLatest
            FROM [Pcubed].[dbo].[AllLivePO] AS po
            LEFT JOIN [Pcubed].[dbo].[employees] AS emp ON po.POBuyer = emp.BadgeNo
            WHERE po.PODetPart IS NOT NULL
            AND DATEDIFF(DAY,CAST(po.PODetDateReq AS date),CAST(GETDATE() AS date) ) > 7
            AND CAST(po.PODetDateLatest AS date) NOT IN
                    ('2001-01-01',
                    '2008-08-08',
                    '2009-09-09',
                    '2010-10-10',
                    '2002-02-02',
                    '2018-12-31')

                GROUP BY
                    po.PONum,
                    po.PODetItemNum,
                    po.PODetPart,
                    po.PODetPartDescr,
                    po.POSuppAddressName,
                    emp.Name,
                    po.PODetDateReq,
                    po.PODetDateLatest

                HAVING
                    CAST(MAX( po.PODetDatePromised) AS date) NOT IN
                    ('2081-12-31',
                    '2002-02-02'))
            SELECT LEFT( CONCAT(
                        PO,
                        '/',
                        PODetItemNum,
                        ' : ',
                        PODetPart,
                        ' : ',
                        POSuppAddressName), 50) AS y,
                DaysLate AS x
            FROM Qry_Exp_D1a2_LatePOReq
            ORDER BY x DESC;
        """,
        title=
            "Overdue Purchase Orders (Requested) > 7 Days",

        x_label=
            "Days Late",

        formatter=
            "integer",
    ),
        "S1": ChartDefinition(
        sql="""
            SELECT CONCAT(' ',FORMAT([Date], 'yy/MM'),' ') AS x,
                COUNT([Accident Description]) AS y
            FROM [Pcubed].[dbo].[Accident]
            WHERE [Date] > DATEADD(DAY,-365,GETDATE())
            GROUP BY FORMAT([Date], 'yy/MM')
            ORDER BY FORMAT([Date], 'yy/MM');
        """,

        title=
            "Accidents Per Month (Last 12 Months)",

        x_label=
            "Year / Month",

        formatter=
            "integer",

        meta={
            "orientation":
                "vertical",

            "valueKey":
                "y",

            "labelKey":
                "x",

            "yLabel":
                "Number of Accidents"
        },
    ),
    "Q1": ChartDefinition(
        sql="""
        WITH Qry_Exp_Q1_AllReturnRepair AS
        (
            SELECT
                RIGHT(
                    so.SOLinePartNo,
                    6
                ) AS Type,

                so.SOLinePartNo,

                wo.WONo,

                wo.WOJobType AS Location,

                so.SONo,

                so.SOLineNo,

                so.SOLineQty
                    - so.SOLineShipQty
                    AS SOOSQty,

                DATEDIFF(
                    DAY,
                    CAST(so.SODate AS date),
                    CAST(GETDATE() AS date)
                ) AS SOOpenDays,

                30 AS Target,

                DATEDIFF(
                    DAY,
                    CAST(GETDATE() AS date),
                    CAST(
                        so.SOLinePromisedDate
                        AS date
                    )
                ) AS SODueDays,

                wo.WONotes,

                so.SODescription

            FROM
                [Pcubed].[dbo].[AllSO] AS so

            LEFT JOIN
                [Pcubed].[dbo].[AllWO] AS wo

                ON so.SOLineNo
                    = wo.WOLineNo

                AND so.SOLinePartNo
                    = wo.WOPartNo

                AND so.SONo
                    = wo.WOSalesOrder

            WHERE
                (
                    so.SOLinePartNo
                        LIKE '%-RETURN'

                    OR so.SOLinePartNo
                        LIKE '%-REPAIR'
                )

                AND so.SOLineStatus <> 50

                AND so.SOLineShipQty
                    < so.SOLineQty

                AND
                (
                    so.SODescription
                        <> 'On Hold'

                    OR so.SODescription
                        IS NULL
                )
        )

        SELECT
            CONCAT(
                SONo,
                '/',
                SOLineNo,
                ' : (WO-',
                WONo,
                ') ',
                LEFT(
                    SOLinePartNo,
                    18
                ),
                ' : ',
                SOOSQty
            ) AS y,

            SOOpenDays AS x,

            30 AS target,

            SODueDays,

            Location

        FROM
            Qry_Exp_Q1_AllReturnRepair

        WHERE
            (
                Location
                    <> 'PENDING CUSTOMER'

                OR Location IS NULL
            )

            AND SOLinePartNo LIKE ?

        ORDER BY
            SOOpenDays DESC;
        """,
        title=
            "Return And Repair WO's (Excl. SO on Hold)",

        x_label=
            "So Open",

        formatter=
            "integer",
    ),    
}


def json_value(value: Any) -> Any:
    """Convert pyodbc and SQL Server values into JSON-safe values."""

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


@sqdip_charts_bp.get(
    "/api/sqdip/filter/<string:filter_id>"
)
def get_sqdip_filter(filter_id: str):
    definition = FILTERS.get(
        filter_id
    )

    if definition is None:
        return jsonify({
            "error": "Unknown SQDIP filter.",
            "filterId": filter_id
        }), 404

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.timeout = 20

        cursor = connection.cursor()

        cursor.execute(
            definition.sql
        )

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "value": str(row[0]),
                "label": str(row[1])
            })

        return jsonify({
            "filterId": filter_id,
            "data": data
        })

    except Exception as error:
        print(
            f"SQDIP filter failed: "
            f"{filter_id}: {error}",
            flush=True
        )

        return jsonify({
            "error": str(error),
            "filterId": filter_id
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


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
                "className",
                "target",
                "targetStart",
                "rightValue"
            ):
                if optional_key in record:
                    item[optional_key] = json_value(
                        record[optional_key]
                    )

            data.append(item)

        return jsonify({
            "meta": {
                "title": definition.title,
                "xLabel": definition.x_label,
                "axis": definition.axis,
                "formatter": definition.formatter,
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


    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.timeout = 20

        cursor = connection.cursor()

        cursor.execute(
            definition.sql
        )

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "value": str(row[0]),
                "label": str(row[1])
            })


        return jsonify({
            "filterId": filter_id,
            "data": data
        })


    except Exception as error:
        return jsonify({
            "error": str(error),
            "filterId": filter_id
        }), 500


    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

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
                "className",
                "target",
                "targetStart"
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