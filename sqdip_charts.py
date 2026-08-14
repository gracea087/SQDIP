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
                AND LTRIM(RTRIM(GRNLocation)) <> ''
                AND GRNLocation LIKE 'MRB%'

            ORDER BY
                label;
        """
    ),


    "q1_type": FilterDefinition(
        sql="""
            SELECT
                value,
                label

            FROM (
                VALUES
                    ('RETURN', 'RETURN'),
                    ('REPAIR', 'REPAIR')
            ) AS filters(
                value,
                label
            );
        """
    ),


    "q7_type": FilterDefinition(
        sql="""
            SELECT
                value,
                label

            FROM (
                VALUES
                    ('Corrective', 'Corrective'),
                    ('prevent', 'preventative'),
                    ('Follow', 'Follow Up')
            ) AS filters(
                value,
                label
            );
        """
    ),

    "p12_training": FilterDefinition(
        sql="""
            SELECT DISTINCT
                LTRIM(
                    RTRIM(
                        CAST(
                            training.[Areas_of_Experience]
                            AS varchar(255)
                        )
                    )
                ) AS value,

                LTRIM(
                    RTRIM(
                        CAST(
                            training.[Areas_of_Experience]
                            AS varchar(255)
                        )
                    )
                ) AS label

            FROM [Pcubed].[dbo].[AllTraining]
                AS training

            INNER JOIN [Pcubed].[dbo].[employees]
                AS employee
                ON training.[BadgeNo_IDFK]
                    = employee.BadgeNo

            WHERE
                training.[Areas_of_Experience]
                    IS NOT NULL

                AND LTRIM(
                    RTRIM(
                        CAST(
                            training.[Areas_of_Experience]
                            AS varchar(255)
                        )
                    )
                ) <> ''

                -- Must actually qualify for P12
                AND training.Result = 1

                AND employee.EmployeeStatusID <> 15

                AND DATEDIFF(
                    DAY,
                    training.[Course_Date],
                    CAST(GETDATE() AS date)
                ) > 180

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

    def q2_location_parameters(
        args: Mapping[str, str]
    ) -> tuple[str]:
        location = (
            args.get(
                "Type",
                ""
            )
            or ""
        ).strip()


        if location:
            return (
                f"%{Type}%",
            )

        # Default Q2 display:
        # show all MR locations.
        return (
            "",
        )

def q1_type_parameters(
    args: Mapping[str, str]
) -> tuple[str]:

    type_ncr = (
        args.get(
            "type",
            ""
        )
        or ""
    ).strip().upper()

    if type_ncr == "RETURN":
        return (
            "%-RETURN%",
        )

    if type_ncr == "REPAIR":
        return (
            "%-REPAIR%",
        )

    return (
        "%",
    )

def q7_type_parameters(
    args: Mapping[str, str]
) -> tuple[str]:

    q7_type = (
        args.get(
            "type",
            ""
        )
        or ""
    ).strip()

    if q7_type:
        return (
            f"%{q7_type}%",
        )

    # ALL button
    return (
        "%",
    )

def p12_training_parameters(
    args: Mapping[str, str]
) -> tuple[str]:

    area = (
        args.get(
            "area",
            ""
        )
        or ""
    ).strip()


    if area:
        return (
            area,
        )


    # ALL AREAS
    return (
        "%",
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
        (SELECT RIGHT(so.SOLinePartNo,6) AS Type,
                so.SOLinePartNo,
                ai.PartDefCust AS Customer,
                wo.WONo,
                wo.WOJobType AS Location,
                so.SONo,
                so.SOLineNo,
                so.SOLineQty - so.SOLineShipQty AS SOOSQty,
                DATEDIFF(DAY,CAST(so.SODate AS date),CAST(GETDATE() AS date)) AS SOOpenDays,
                DATEDIFF(DAY,CAST(GETDATE() AS date),CAST(so.SOLinePromisedDate AS date)) AS SODueDays,
                wo.WONotes,
                so.SODescription

            FROM [Pcubed].[dbo].[AllSO] AS so

            LEFT JOIN [Pcubed].[dbo].[worksOrder] AS wo
                ON so.SOLineNo = wo.WOLineNo
                AND so.SOLinePartNo = wo.WOPartNo
                AND so.SONo  = wo.WOSalesOrder
            LEFT JOIN [Pcubed].[dbo].[allItems] AS ai
            ON ai.PartNo = so.SOLinePartNo

            WHERE
                (so.SOLinePartNo LIKE '%-RETURN' OR so.SOLinePartNo LIKE '%-REPAIR')
                AND so.SOLineStatus <> 50
                AND so.SOLineShipQty < so.SOLineQty
                AND (so.SODescription <> 'On Hold' OR so.SODescription IS NULL))

        SELECT CONCAT(SONo,'/',SOLineNo,' : (WO-',
                COALESCE(CAST(WONo AS varchar(30)),''),') ',
                LTRIM(RTRIM(SOLinePartNo)),
                CASE WHEN NULLIF(LTRIM(RTRIM(Customer)),'') IS NOT NULL
                    THEN CONCAT(' - ',LTRIM(RTRIM(Customer)))ELSE '' END,' : ',SOOSQty) AS y,
            SOOpenDays AS x,
            SODueDays AS secondaryValue

        FROM Qry_Exp_Q1_AllReturnRepair
        WHERE (Location <> 'PENDING CUSTOMER' OR Location IS NULL)
            AND SOLinePartNo LIKE ?

        ORDER BY SOOpenDays DESC;
        """,

        title=
            "Return And Repair WO's "
            "(Excl. SO On Hold)",

        x_label=
            "Days",

        formatter=
            "integer",

        parameters=
            q1_type_parameters,

        meta={
            "secondaryValueFormatter":
                "integer",

            "secondaryValueLabel":
                "SO Due (Days)",

            "targetBandStart":
                0,

            "targetBandEnd":
                30
        },
    ),
    "I11": ChartDefinition(
        sql = """
        SELECT
            CONCAT([WONo] , ' <' , [WOSalesOrder] , '/' , [WOLineNo] , '> ' , [WOPartNo]) AS y,
            DATEDIFF(DAY,[SOLinePromisedDate],[WOSchedFinishDate]) AS x
        FROM
            (
                [Pcubed].[dbo].[worksOrder]
                LEFT JOIN AllItems ON [Pcubed].[dbo].[worksOrder].WOPartNo = AllItems.PartNo
            )
            INNER JOIN AllSO ON ([Pcubed].[dbo].[worksOrder].WOLineNo = AllSO.SOLineNo)
            AND ([Pcubed].[dbo].[worksOrder].WOSalesOrder = AllSO.SONo)
        WHERE
            (
                (DATEDIFF(DAY,[SOLinePromisedDate],[WOSchedFinishDate]) > 0)
                AND (DATEDIFF(DAY,[SOLineShipQty],[SOLineQty]) > 0)
                AND (([Pcubed].[dbo].[worksOrder].WOStatusDescription) NOT LIKE 'Completed')
            )
        ORDER BY x DESC;
        """,
        title=
            "WO Schedule Finish > SO Promised",

        x_label=
            "Days Late",

        formatter=
            "integer",
    ),    
    "I12": ChartDefinition(
        sql="""
        WITH Qry_Exp_I12_MatExp AS
        (SELECT
            AllLiveGRN.GRNNo,
            AllLiveGRN.GRNPartNo,
            AllItems.PartDescription,
            AllLiveGRN.GRNQtyLeft,
            AllItems.PartLeadTime,
            DATEDIFF(DAY,GETDATE(),[GRNExpiryDate]) AS DaysTillExpiry,
            AllLiveGRN.GRNExpiryDate,
            AllItems.PartGroupCode,
            AllLiveGRN.GRNLocation,
            [DemandSO] + [DemandWO] AS Demand,
            AllItems.PartStockActive
        FROM
            AllLiveGRN
            INNER JOIN AllItems ON AllLiveGRN.GRNPartNo = AllItems.PartNo
        GROUP BY
            AllLiveGRN.GRNNo,
            AllLiveGRN.GRNPartNo,
            AllItems.PartDescription,
            AllLiveGRN.GRNQtyLeft,
            AllItems.PartLeadTime,
            DATEDIFF(DAY,GETDATE(),[GRNExpiryDate]),
            AllLiveGRN.GRNExpiryDate,
            AllItems.PartGroupCode,
            AllLiveGRN.GRNLocation,
            [DemandSO] + [DemandWO],
            AllItems.PartStockActive,
            [GRNExpiryDate] - [PartLeadTime] -7
        HAVING
            ((DATEDIFF(DAY,GETDATE(),[GRNExpiryDate])) < 60)
                AND ((AllLiveGRN.GRNLocation) NOT LIKE '%QUARANTINE%')
            )

            SELECT
            concat([GRNNo] , ' <' , [GRNPartNo] , '>') AS y,
            Qry_Exp_I12_MatExp.DaysTillExpiry AS x
        FROM
            Qry_Exp_I12_MatExp

        ORDER BY
            DATEDIFF(DAY,GETDATE(),[GRNExpiryDate]);
        """,
        title=
            "Material and PCB Shelf Life Expiry Within 60 Days",

        x_label=
            "Days Untill Expiry",

        formatter=
            "integer",
    ),
    "D8": ChartDefinition(
        sql="""
        WITH Qry_MaxPOUnitPrice AS
        (SELECT
            AllLivePO.PODetPart AS POPartNo,
            Max(AllLivePO.PODetUnitPrice) AS MaxOfPODetUnitPrice
        FROM
            AllLivePO
        GROUP BY
            AllLivePO.PODetPart)

        SELECT
            TOP 20 AllLivePO.PODetPart AS y,
            [MaxOfPODetUnitPrice] * (
                IIf(
                    [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                    [PartStockOnOrderPO],
                    [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
                ) / [PartUOMUOPConv]
            ) AS x
        FROM
            (
                (
                    AllLivePO
                    INNER JOIN AllItems ON AllLivePO.PODetPart = AllItems.PartNo
                )
                INNER JOIN employees ON AllLivePO.POBuyer = employees.BadgeNo
            )
            INNER JOIN Qry_MaxPOUnitPrice ON AllLivePO.PODetPart = Qry_MaxPOUnitPrice.POPartNo
        WHERE
            (((AllItems.PartMinStockLev) = 0))
        GROUP BY
            AllLivePO.PODetPart,
            [MaxOfPODetUnitPrice] * (
                IIf(
                    [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                    [PartStockOnOrderPO],
                    [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
                ) / [PartUOMUOPConv]
            ),
            IIf(
                [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                [PartStockOnOrderPO],
                [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
            )
        HAVING
            (
                (
                    (
                        [MaxOfPODetUnitPrice] * (
                            IIf(
                                [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                                [PartStockOnOrderPO],
                                [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
                            ) / [PartUOMUOPConv]
                        )
                    ) > 20
                )
                AND (
                    (
                        IIf(
                            [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                            [PartStockOnOrderPO],
                            [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
                        )
                    ) > 0
                )
                AND (
                    (Min(AllLivePO.PODetDatePromised)) NOT LIKE '1 / 1 / 2001'
                    AND (Min(AllLivePO.PODetDatePromised)) NOT LIKE '4 / 1 / 2081'
                    AND (Min(AllLivePO.PODetDatePromised)) NOT LIKE '1 / 1 / 2002'
                )
            )
        ORDER BY
            [MaxOfPODetUnitPrice] * (
                IIf(
                    [PartStockOnOrderPO] < [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO],
                    [PartStockOnOrderPO],
                    [PartStockActive] + [PartStockOnOrderPO] - [DemandSO] - [DemandWO]
                ) / [PartUOMUOPConv]
            ) DESC;
        """,
        title=
            "Excess PO Qty (Top 20 by Excess Value >£20)",

        x_label=
            "Excess PO Qty Value £",

        formatter=
            "integer",
    ),
    "I4": ChartDefinition(
        sql="""
        SELECT
            Left(CONCAT([GRNNo] , ' <' , [GRNPartNo] , '> ' , [PartDescription]),25) AS y,
            DATEDIFF(DAY,[GRNDateReceived],GETDATE()) AS x,
            5 AS Target
        FROM
            [Pcubed].[dbo].[AllLiveGRN] 
            LEFT JOIN AllItems ON AllLiveGRN.GRNPartNo = AllItems.PartNo
            LEFT JOIN AllWOPartDemand ON AllLiveGRN.GRNPartNo = AllWOPartDemand.PartNo
        WHERE
        AllLiveGRN.GRNRequiresRelease = 1
                AND AllLiveGRN.GRNLocation NOT LIKE 'MRB%'
                    AND AllLiveGRN.GRNLocation <> 'GREY MARKET INSPECTION'
        GROUP BY
            AllLiveGRN.GRNNo,
            AllLiveGRN.GRNPartNo,
            AllItems.PartDescription,
            AllLiveGRN.GRNDateReceived,
            AllWOPartDemand.PartNo

        ORDER BY x DESC;
        """,
        title=
            "Stock Awaiting Release (Days since parts Recieved)",

        x_label=
            "Days In WIP",

        formatter=
            "integer",
    ),
    "I7": ChartDefinition(
        sql="""
        SELECT
            CONCAT(
                als.GRNNo,
                '(X',
                grn.GRNQtyLeft,
                ' <> £',
                ROUND(
                    TRY_CONVERT(
                        decimal(18, 2),
                        grn.GRNQtyLeft
                    )
                    *
                    TRY_CONVERT(
                        decimal(18, 2),
                        grn.GRNUnitCost
                    ),
                    0
                ),
                ') ',
                grn.GRNPartNo
            ) AS y,

            CASE
                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - RED]
                ) <> 0
                THEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - RED]
                )

                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - AMBER]
                ) <> 0
                THEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - AMBER]
                )

                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - GREEN]
                ) <> 0
                THEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - GREEN]
                )

                ELSE 0
            END AS x,


            CASE
                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - RED]
                ) <> 0
                THEN 'lost-stock-red'

                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - AMBER]
                ) <> 0
                THEN 'lost-stock-amber'

                WHEN TRY_CONVERT(
                    decimal(18, 2),
                    als.[LOST STOCK - GREEN]
                ) <> 0
                THEN 'lost-stock-green'

                ELSE 'lost-stock-unknown'
            END AS className,

            30 AS target

        FROM [Pcubed].[dbo].[AllLostStock] AS als

        LEFT JOIN [Pcubed].[dbo].[AllLiveGRN] AS grn
            ON als.GRNNo = grn.GRNNo
            AND als.GRNLineNo = grn.GRNLineNo

        LEFT JOIN [Pcubed].[dbo].[AllGRN_Transfer] AS tr
            ON als.GRNNo = tr.TransferGRNNo
            AND als.GRNLineNo = tr.TranferGRNLineNo

        GROUP BY
            als.GRNNo,
            grn.GRNQtyLeft,
            grn.GRNUnitCost,
            grn.GRNPartNo,
            als.[LOST STOCK - AMBER],
            als.[LOST STOCK - GREEN],
            als.[LOST STOCK - RED],
            als.MaxOfTransferDate

        ORDER BY
            als.MaxOfTransferDate;
        """,
        title=
            "LOST STOCK Location (Days)",

        x_label=
            "Days Lost",

        formatter=
            "integer",
    ),
    "Q7": ChartDefinition(
        sql="""
        SELECT
            CONCAT([Type], ' ' , [NCR] , ' # ' , [Name]) AS y,
            DATEDIFF(DAY,GETDATE(),Target) AS x,
            Type,
            employees.Name

            FROM AllOpenNCRActions 
            INNER JOIN employees ON AllOpenNCRActions.Who = employees.BadgeNo

            WHERE ((DATEDIFF(DAY,GETDATE(),[Target]))<=7) 
            AND [Type] Like ?

            ORDER BY x DESC;
        """,
        title=
            "NCR Actions Due within 7 Days",

        x_label=
            "Days Untill Due",

        formatter=
            "integer",
        
        parameters=q7_type_parameters,
    ),
    "Q6": ChartDefinition(
        sql="""
        SELECT
            TOP 20 
            CONCAT([NonCNo] , ' # ' , [NonCPartNo] , ' ~ ' , [Name]) AS y,
            DATEDIFF(DAY,[NonCDate],GETDATE()) AS x,
            0 AS targetStart,
            30 AS target

        FROM
            (AllOpenNCR LEFT JOIN AllOpenNCRActions ON AllOpenNCR.NonCNo = AllOpenNCRActions.NCR)
            LEFT JOIN employees ON AllOpenNCRActions.Who = employees.BadgeNo

        WHERE
            (((AllOpenNCRActions.Type) LIKE 'C%'
            OR (AllOpenNCRActions.Type) LIKE 'P%'))

        ORDER BY x DESC;
        """,
        title=
            "Open NCR (Days) Top 20 With Open Actions (Pre/Cor)",

        x_label=
            "Days Open",

        formatter=
            "integer",
    ),
    "Q8": ChartDefinition(
        sql="""
        SELECT
            CONCAT([ToolCompanySerialNo] , ' (' , [ToolNo] , ') ' , ' # ' , [Name] , ' # ' , [ToolLocation]) AS y,
            DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) AS x
        FROM
            AllCalibration
            LEFT JOIN employees ON AllCalibration.ToolResponsible = employees.BadgeNo
        WHERE
            (
                (DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) <= 7)
                AND (
                    (AllCalibration.ToolLocation) NOT LIKE 'QUARANTINE'
                    AND (AllCalibration.ToolLocation) NOT LIKE 'AWAITING REPAIR / CALIBRATION'
                    AND (AllCalibration.ToolLocation) NOT LIKE 'SENT FOR CALIBRATION'
                    AND (AllCalibration.ToolLocation) NOT LIKE 'RETURNED TO SUPPLIER'
                    AND (AllCalibration.ToolLocation) NOT LIKE 'ARCHIVE'
                    AND (AllCalibration.ToolLocation) NOT LIKE 'RETURNED TO CUSTOMER'
                )
                AND (
                    (AllCalibration.CalibrationStatusDesc) <> 'closed'
                )
                AND ((AllCalibration.ToolRequiresCalibration) = 1)
                AND ((AllCalibration.GroupName) = 'CALIBRATED')
            )
            OR (
                (DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) <= 7)
                AND ((AllCalibration.ToolLocation) IS NULL)
                AND (
                    (AllCalibration.CalibrationStatusDesc) <> 'closed'
                )
                AND ((AllCalibration.ToolRequiresCalibration) = 1)
                AND ((AllCalibration.GroupName) = 'CALIBRATED')
            )
        ORDER BY x ASC;
        """,
         title=
            "Calibration Due in Next 7 Days",

        x_label=
            "Days Untill Due",

        formatter=
            "integer",
    ),
    "Q8b": ChartDefinition(
        sql="""
        SELECT
            CONCAT([ToolCompanySerialNo] , ' (' , [ToolNo] , ') ' , ' # ' , [Name] , ' # ' , [ToolLocation]) AS y,
            DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) AS x
        FROM
            AllCalibration
            LEFT JOIN employees ON AllCalibration.ToolResponsible = employees.BadgeNo
        WHERE
            ((DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) <= 7)
                AND ((AllCalibration.GroupName) IS NULL)
                AND ((AllCalibration.ToolLocation) NOT LIKE 'QUARANTINE'
                AND (AllCalibration.ToolLocation) NOT LIKE 'AWAITING REPAIR / CALIBRATION'
                AND (AllCalibration.ToolLocation) NOT LIKE 'SENT FOR CALIBRATION'
                AND (AllCalibration.ToolLocation) NOT LIKE 'RETURNED TO SUPPLIER'
                AND (AllCalibration.ToolLocation) NOT LIKE 'ARCHIVE'
                AND (AllCalibration.ToolLocation) NOT LIKE 'RETURNED TO CUSTOMER')
                AND ((AllCalibration.CalibrationStatusDesc) <> 'closed')
                AND ((AllCalibration.ToolRequiresCalibration) = 1))
            OR ((DATEDIFF(DAY,GETDATE(),[ToolNextCalibration]) <= 7)
                AND ((AllCalibration.GroupName) IS NULL)
                AND ((AllCalibration.ToolLocation) IS NULL)
                AND ((AllCalibration.CalibrationStatusDesc) <> 'closed')
                AND ((AllCalibration.ToolRequiresCalibration) = 1))
        ORDER BY x ASC;
        """,
        title=
            "Tooling Checks Due in Next 7 Days",

        x_label=
            "Days Untill Due",

        formatter=
            "integer",
    ),
    "P1": ChartDefinition(
        sql="""
        SELECT
            CONCAT([WONo] , ' (' , [WOSchedStartDate] , ') : ' , [WOPartNo],40) AS y,
            DATEDIFF(DAY,GETDATE(),[WOSchedStartDate]) AS x,
            7 AS target,
            0 AS targetStart

        FROM
            (worksOrder INNER JOIN AllItems ON worksOrder.WOPartNo = AllItems.PartNo)
            LEFT JOIN PV601 ON worksOrder.WONo = PV601.WorksOrder

        GROUP BY
            worksOrder.WOSchedStartDate,
            AllItems.StatusDescription,
            worksOrder.WOQtyOS,
            worksOrder.WOStatusDescription,
            PV601.PrintedBy,
            worksOrder.WOPartNo,
            worksOrder.WOEarliestStartDate,
            worksOrder.WONo

        HAVING
            (((worksOrder.WOSchedStartDate) >= GETDATE() -360 AND (worksOrder.WOSchedStartDate) <= GETDATE() + 28)
                AND ((AllItems.StatusDescription) LIKE 'TO BE REVIEWED'
                    OR (AllItems.StatusDescription) = 'IN DEV'
                    OR (AllItems.StatusDescription) = 'ENGINEERING HOLD'
                    OR (AllItems.StatusDescription) = 'NPI'
                    OR (AllItems.StatusDescription) = 'CAUTION'
                    OR (AllItems.StatusDescription) = 'DORMANT')
                AND ((worksOrder.WOQtyOS) > 0)
                AND ((worksOrder.WOStatusDescription) = 'WIP'
                    OR (worksOrder.WOStatusDescription) = 'Created')
                AND ((PV601.PrintedBy) IS NULL)
                AND ((worksOrder.WOPartNo) NOT LIKE 'SMT ATTRITION'
                    AND (worksOrder.WOPartNo) NOT LIKE '*REPAIR'
                    AND (worksOrder.WOPartNo) NOT LIKE '*RETURN')
                AND ((worksOrder.WOEarliestStartDate) NOT LIKE '12 / 12 / 2012'))

        ORDER BY x ASC;
        """,
        title=
            "TBR / IN-DEV / ENG-HOLD / NPI / CAUTION / DORMANT WO's",

        x_label=
            "Days Untill Start Date",

        formatter=
            "integer",
    ),
    "P2": ChartDefinition(
        sql="""
        SELECT
            CONCAT([WONo] , ' (' , [WOSchedStartDate] , ') : ' , [WOPartNo],40) AS y,
            DATEDIFF(DAY,GETDATE(),[WOSchedStartDate]) AS x,
            0 as targetStart,
            7 AS target
        FROM
            (worksOrder INNER JOIN AllItems ON worksOrder.WOPartNo = AllItems.PartNo)
            LEFT JOIN PV601 ON worksOrder.WONo = PV601.WorksOrder
        GROUP BY
            AllItems.StatusDescription,
            worksOrder.WOSchedStartDate,
            worksOrder.WOQtyOS,
            worksOrder.WOStatusDescription,
            PV601.PrintedBy,
            worksOrder.WOPartNo,
            worksOrder.WOEarliestStartDate,
            worksOrder.WONo
        HAVING
            (((AllItems.StatusDescription) <> 'TO BE REVIEWED'
                AND (AllItems.StatusDescription) <> 'IN DEV'
                AND (AllItems.StatusDescription) <> 'ENGINEERING HOLD'
                AND (AllItems.StatusDescription) <> 'NPI'
                AND (AllItems.StatusDescription) <> 'CAUTION'
                AND (AllItems.StatusDescription) <> 'DORMANT')
                AND ((worksOrder.WOSchedStartDate) >= GETDATE() -360
                AND (worksOrder.WOSchedStartDate) <= GETDATE() + 28)
                AND ((worksOrder.WOQtyOS) > 0)
                AND ((worksOrder.WOStatusDescription) = 'WIP'
                OR (worksOrder.WOStatusDescription) = 'Created')
                AND ((PV601.PrintedBy) IS NULL)
                AND ((worksOrder.WOPartNo) NOT LIKE '%FAI%'
                AND (worksOrder.WOPartNo) NOT LIKE 'CONSUMABLE ISSUES'
                AND (worksOrder.WOPartNo) NOT LIKE 'MONTHLY-LOST-STOCK-WRITE-OFF'
                AND (worksOrder.WOPartNo) NOT LIKE 'PHOENIX-DELTA-FAIR-SUB'
                AND (worksOrder.WOPartNo) NOT LIKE '%DELTA FAIR%'
                AND (worksOrder.WOPartNo) NOT LIKE '%PHOENIX FAIR%'
                AND (worksOrder.WOPartNo) NOT LIKE 'SMT ATTRITION'
                AND (worksOrder.WOPartNo) NOT LIKE '%RETURN'
                AND (worksOrder.WOPartNo) NOT LIKE '%REPAIR')
                AND ((worksOrder.WOEarliestStartDate) NOT LIKE '12 / 12 / 2012'))
        ORDER BY
            worksOrder.WOSchedStartDate;
        """,
         title=
            "WO's ready to Print - Due Within 28 Days",

        x_label=
            "Days Untill Start Date",

        formatter=
            "integer",
    ),
    "D12": ChartDefinition(
        sql="""
        WITH Qry_Exp_D12_SOHold AS
            (SELECT
                AllSO.SONo,
                AllSO.SOCustID,
                AllSO.SOLinePromisedDate,
                AllSO.SODescription,
                AllSO.SOLineQty,
                AllSO.SOLineShipQty,
                AllSO.SOLineNo
            FROM
                AllSO
            GROUP BY
                AllSO.SONo,
                AllSO.SOCustID,
                AllSO.SOLinePromisedDate,
                AllSO.SODescription,
                AllSO.SOLineQty,
                AllSO.SOLineShipQty,
                AllSO.SOLineNo
            HAVING
                (((AllSO.SOCustID) NOT LIKE 'MEG-VMI') AND ((AllSO.SODescription) = 'On Hold')))

            SELECT
                CONCAT([SONo] , ' (' , [SOCustID] , ') - ' , [SOLineNo]) AS y,
                DATEDIFF(DAY,GETDATE(),[SOLinePromisedDate]) AS x
            FROM
                Qry_Exp_D12_SOHold
            GROUP BY
                SONo,
                SOCustID,
                SOLineNo,
                SOLinePromisedDate,
                Qry_Exp_D12_SOHold.SOCustID
            HAVING
                (((Qry_Exp_D12_SOHold.SOCustID) NOT LIKE 'MEG-VMI'))
            ORDER BY x ASC;
        """,
        title=
            "SO On Hold (Exc. MAV-VMI)",

        x_label=
            "Days Untill Promised Delivery",

        formatter=
            "integer",
    ),
    "P3a": ChartDefinition(
        sql="""
        SELECT
            AllCR.AssignedName AS y,
            Count(CONCAT([ContractReviewNo] , ' ' , [ContRevDetailTaskNo])) AS x
        FROM
            AllCR
        WHERE
            (((AllCR.CRStatusDescription) = 'Open')
                AND ((AllCR.ContRevDetailTargetDate) < GETDATE()))
        GROUP BY
            AllCR.AssignedName
        ORDER BY
            X DESC;
        """,
        title=
            "Overdue CR Actions",

        x_label=
            "QTY Overdue Actions",

        formatter=
            "integer",
    ),
    "P3b": ChartDefinition(
        sql="""
        SELECT
            LEFT(CONCAT([ContractReviewNo] , '/' , [ContRevDetailTaskNo] , ' - ' , [AssignedName] , ' # ' , [ContRevDetailTask]),50) AS y,
            DATEDIFF(DAY,GETDATE(),[ContRevDetailTargetDate]) AS x,
            AllCR.ContRevDetailTask
        FROM
            AllCR
        GROUP BY
            ContractReviewNo,
            ContRevDetailTaskNo,
            AssignedName,
            ContRevDetailTask,
            ContRevDetailTargetDate,
            AllCR.ContRevDetailTask,
            AllCR.CRStatusDescription,
            AllCR.ContractReviewDate
        HAVING
            (((AllCR.ContRevDetailTask) LIKE '%LONG LEAD%'
            OR (AllCR.ContRevDetailTask) LIKE '%BOM%'
            OR (AllCR.ContRevDetailTask) LIKE '%WORK ORDER%')
            AND ((AllCR.CRStatusDescription) = 'open'))
        ORDER BY x DESC;
        """,
        title=
            "Open 'Long Lead', 'BOM' and 'WO' related CR Actions",

        x_label=
            "Days Untill Due",

        formatter=
            "integer",
    ),
    "P5": ChartDefinition(
        sql="""
        SELECT DISTINCT
            CONCAT(enq.EnquiryNo,' ',enq.EnqCustID,' (S-)',followup.[Name]) AS y,
            DATEDIFF(DAY,CAST(GETDATE() AS date), CAST(enq.EnqDecisionDate AS date)) AS x

        FROM [Pcubed].[dbo].[AllEnq] AS enq
        LEFT JOIN [Pcubed].[dbo].[employees] AS estimator
            ON enq.EnqEstimator = estimator.BadgeNo
        LEFT JOIN [Pcubed].[dbo].[employees] AS followup
            ON enq.EnqFollowUpBy = followup.BadgeNo
        LEFT JOIN [Pcubed].[dbo].[employees] AS salesrep
            ON enq.EnqSalesRep = salesrep.BadgeNo

        WHERE DATEDIFF(DAY,CAST(GETDATE() AS date),CAST(enq.EnqDecisionDate AS date)) <= 7
            AND enq.EnqDecisionDate >= '2020-01-01'
            AND enq.EnqStatus = '#Submitted'

        ORDER BY x ASC;
        """,
        title=
            "Enquiry Status - Submitted",

        x_label=
            "Days Untill Follow-Up Required",

        formatter=
            "integer",
    ),
    "P12": ChartDefinition(
        sql="""
            SELECT
                CONCAT(
                    training.[Training_Course],
                    ' (',
                    training.[Name],
                    ')'
                ) AS y,

                DATEDIFF(
                    DAY,
                    training.[Course_Date],
                    CAST(GETDATE() AS date)
                ) AS x

            FROM [Pcubed].[dbo].[AllTraining]
                AS training

            INNER JOIN [Pcubed].[dbo].[employees]
                AS employee

                ON training.[BadgeNo_IDFK]
                    = employee.BadgeNo

            WHERE
                training.[Areas_of_Experience]
                    LIKE ?

                AND training.Result = 1

                AND employee.EmployeeStatusID
                    <> 15

                AND DATEDIFF(
                    DAY,
                    training.[Course_Date],
                    CAST(GETDATE() AS date)
                ) > 180

            GROUP BY
                training.[Training_Course],
                training.[Name],
                training.[Course_Date],
                training.[Areas_of_Experience],
                training.Result,
                employee.EmployeeStatusID

            ORDER BY
                training.[Areas_of_Experience],
                x DESC;
        """,

        title=
            "Training Over 180 Days",

        x_label=
            "Days Since Training",

        formatter=
            "integer",

        parameters=
            p12_training_parameters,

        meta={
            "leftLabelWidth": "auto"
        }
    ),
    "I9": ChartDefinition(
        sql="""
        WITH Qry_WORecDate AS
            (SELECT
                AllWORec.GRNWO,
                worksOrder.WOQty,
                Sum(AllWORec.GRNQtyReceived) AS SumOfGRNQtyReceived,
                Max(AllWORec.GRNDateReceived) AS MaxOfGRNDateReceived
            FROM
                AllWORec
                LEFT JOIN worksOrder ON AllWORec.GRNWO = worksOrder.WONo
            GROUP BY
                AllWORec.GRNWO,
                worksOrder.WOQty)


        SELECT
            CONCAT([WONo] , ' # ' , [WOPartNo]) AS y,
            DATEDIFF(DAY,[MaxOfGRNDateReceived],GETDATE()) AS x
        FROM
            (worksOrder LEFT JOIN AllItems ON worksOrder.WOPartNo = AllItems.PartNo)
            INNER JOIN Qry_WORecDate ON worksOrder.WONo = Qry_WORecDate.GRNWO
        WHERE
            (((worksOrder.WOQtyOS) = 0)
            AND ((worksOrder.WOStatusDescription) NOT LIKE 'Completed')
            AND ((worksOrder.WOPartNo) NOT LIKE 'PROCEDURES'))
        ORDER BY x DESC;
        """,
        title=
            "WIP - Open Works Orders with Zero O/S Qty",

        x_label=
            "Days Since Last Receipt",

        formatter=
            "integer",
    ),
    "P11": ChartDefinition(
        sql="""
        WITH Qry_Exp_P11_DFM AS (
            SELECT
                CONCAT([DocNo],' ',[Type],' ',[PartNo],' (',[Who],')' ) AS y,
                DATEDIFF(DAY,[DateCreated],GETDATE()) AS x,
                PV760_DFM.PartNo,
                PV760_DFM.Customer

            FROM PV760_DFM

            WHERE [DateCreated] IS NOT NULL
                AND PV760_DFM.DateComplete IS NULL

            GROUP BY
                [DocNo],
                [Type],
                [PartNo],
                [Who],
                [DateCreated],
                PV760_DFM.PartNo,
                PV760_DFM.Customer,
                PV760_DFM.DateComplete)

        SELECT
            Qry_Exp_P11_DFM.y,
            Qry_Exp_P11_DFM.x

        FROM Qry_Exp_P11_DFM

        WHERE
            Qry_Exp_P11_DFM.x > 30

        ORDER BY
            Qry_Exp_P11_DFM.x DESC;
        """,
        title=
            "Open DFM (> 30 Days)",

        x_label=
            "Days Open",

        formatter=
            "integer",
    ),
    "P9": ChartDefinition(
        sql="""
        WITH Qry_Exp_P9_OpenObLog AS (
        SELECT
            PV718_ObLog.[Log],
            PV718_ObLog.[Date_Added],
            PV718_ObLog.Buyer,
            PV718_ObLog.[Progress_Part],
            PV718_ObLog.[Description_from_Progress],
            PV718_ObLog.[Link_To_Supplier_Email_hyperlink_on_column_A],
            PV718_ObLog.[Email_added_to_progress_AND_CHANGE_STATUS_TO_READ_MEMO],
            PV718_ObLog.[Note_Added_to_Progress],
            PV718_ObLog.[Email_to_Eng_And_Sales],
            PV718_ObLog.[Other_Action_Taken],
            PV718_ObLog.[PCN_or_EOL],
            PV718_ObLog.[LTB_DATE],
            PV718_ObLog.[Customer_s_Affected],
            PV718_ObLog.[Acc_Mgr_Date_sent_to_customer],
            PV718_ObLog.[Acc_Mgr_Action_requested_by_customer],
            PV718_ObLog.[Complete]
        FROM
            PV718_ObLog
        GROUP BY
            PV718_ObLog.[Log],
            PV718_ObLog.[Date_Added],
            PV718_ObLog.Buyer,
            PV718_ObLog.[Progress_Part],
            PV718_ObLog.[Description_from_Progress],
            PV718_ObLog.[Link_To_Supplier_Email_hyperlink_on_column_A],
            PV718_ObLog.[Email_added_to_progress_AND_CHANGE_STATUS_TO_READ_MEMO],
            PV718_ObLog.[Note_Added_to_Progress],
            PV718_ObLog.[Email_to_Eng_And_Sales],
            PV718_ObLog.[Other_Action_Taken],
            PV718_ObLog.[PCN_or_EOL],
            PV718_ObLog.[LTB_DATE],
            PV718_ObLog.[Customer_s_Affected],
            PV718_ObLog.[Acc_Mgr_Date_sent_to_customer],
            PV718_ObLog.[Acc_Mgr_Action_requested_by_customer],
            PV718_ObLog.[Complete]
        HAVING
            (((PV718_ObLog.[Complete]) IS NULL)))

        SELECT
            TOP 25 
            CONCAT([Log] , ' / ' , [Buyer] , ' / ' , Left([Progress_Part], 15)) AS y,
            DATEDIFF(DAY,[Date_Added],GETDATE()) AS x,
            0 as targetStart,
            DATEDIFF(DAY,GETDATE(),[LTB_DATE]) AS target
        FROM
            Qry_Exp_P9_OpenObLog
        GROUP BY
            [Log], 
            [Buyer],
            [Progress_Part],
            [Date_Added],
            [LTB_DATE]
        ORDER BY x DESC;
        """,
        title=
            "Obsolescence Log Open Items (PV718) Top 25 by Days Open",

        x_label=
            "Days Open",

        formatter=
            "integer",

        meta={
            "subtitle":
                "Red target = days until LTB date"
        },
    ),
    "P4": ChartDefinition(
        sql="""
        SELECT
            TOP 20 
            CONCAT([RFC] , ' (' , [Actionee] , ') - ' , [Document]) AS y,
            DATEDIFF(DAY,[DateRaised],GETDATE()) AS x,
            0 AS targetStart,
            90 AS target
        FROM
            [PV547-RFC]
        GROUP BY
            [RFC],
            [Actionee],
            [Document],
            [DateRaised],
            [PV547-RFC].Status,
            [PV547-RFC].Customer
        HAVING
            (
                ((DATEDIFF(DAY,[DateRaised],GETDATE())) >= 45)
                AND (
                    ([PV547-RFC].Status) = 'open'
                    OR ([PV547-RFC].Status) IS NULL
                )
                AND (([PV547-RFC].Customer) IS NOT NULL)
            )
        ORDER BY x DESC;
        """,
        title=
            "RFC's Open > 45 Days",

        x_label=
            "Days Open",

        formatter=
            "integer",
    ),
    "I14": ChartDefinition(
        sql="""
        ;WITH Qry_I14_StockGRNUnitCost AS
        (SELECT
            grn.GRNPartNo,
            grn.GRNNo,
            SUM(TRY_CONVERT(decimal(18, 4),grn.GRNQtyLeft)) AS GRNSumQtyLeft,
            MAX(TRY_CONVERT(decimal(18, 4),grn.GRNUnitCost)) AS GRNMaxUnitCost
            FROM [Pcubed].[dbo].[AllLiveGRN] AS grn
            WHERE grn.GRNPartNo IS NOT NULL
            GROUP BY grn.GRNPartNo,grn.GRNNo),


        Qry_Exp_I14_StockZeroWOBomQtyByPartGRN AS
        (SELECT
            wob.WOBOMChildPartNo,
            items.PartDescription,
            items.PartDefLocation,
            COUNT(wob.WONo) AS CountOfWONo,
            items.PartGroupCode,
            grn.GRNNo,
            grn.GRNSumQtyLeft,
            grn.GRNMaxUnitCost,
            ROUND(grn.GRNSumQtyLeft * grn.GRNMaxUnitCost,0 ) AS ApproxSurplusCost
            FROM [Pcubed].[dbo].[worksOrderBOM] AS wob
            INNER JOIN [Pcubed].[dbo].[AllItems] AS items
                ON wob.WOBOMChildPartNo= items.PartNo
            INNER JOIN [Pcubed].[dbo].[worksOrder] AS wo
                ON wob.WONo = wo.WONo
            INNER JOIN Qry_I14_StockGRNUnitCost AS grn
                ON wob.WOBOMChildPartNo= grn.GRNPartNo
            WHERE wo.WOStatusDescription <> 'Completed'
                AND items.PartMainlyPurchased = 1
                AND (wo.WOQty - wo.WOQtyOS) = 0
                AND items.PartGroupCode NOT LIKE 'CONSUMABLE%'
                AND grn.GRNSumQtyLeft > 0
                AND wob.WOBOMQty = 0
                AND wob.WOBOMChildPartNo <> 'DNF'
                AND ROUND( grn.GRNSumQtyLeft  * grn.GRNMaxUnitCost,0) > 20
            GROUP BY
                wob.WOBOMChildPartNo,
                items.PartDescription,
                items.PartDefLocation,
                items.PartGroupCode,
                grn.GRNNo,
                grn.GRNSumQtyLeft,
                grn.GRNMaxUnitCost,
                wob.WOBOMQty),

        Qry_Exp_I14 AS
        (SELECT
            stock.WOBOMChildPartNo,
            stock.PartDescription,
            stock.CountOfWONo,
            SUM(stock.GRNSumQtyLeft) AS SumOfGRNSumQtyLeft,
            SUM(stock.ApproxSurplusCost) AS SumOfApproxSurplusCost
            FROM Qry_Exp_I14_StockZeroWOBomQtyByPartGRN AS stock
            GROUP BY
                stock.WOBOMChildPartNo,
                stock.PartDescription,
                stock.CountOfWONo)


        SELECT TOP (20)
            result.WOBOMChildPartNo AS y,
            result.SumOfApproxSurplusCost AS x

        FROM Qry_Exp_I14 AS result

        ORDER BY
            result.SumOfApproxSurplusCost DESC;
        """,
         title=
            "Zero Qty WO Items with current stock > £20 (Top 20 by value)",

        x_label=
            "value (£)",

        formatter=
            "integer",
    ),
    "I13": ChartDefinition(
        sql="""
        ;WITH Qry_I13_2_SelectPartIssueWoBom AS
        (SELECT
            bom.WONo,
            bom.WOPartNo,
            COUNT(bom.WOBOMChildPartNo) AS QtyItemsPartialKit
            FROM [Pcubed].[dbo].[worksOrderBOM] AS bom
                INNER JOIN [Pcubed].[dbo].[AllItems] AS items
                    ON bom.WOBOMChildPartNo = items.PartNo
            WHERE bom.WOBOMTotalRequired > 0
                AND bom.WOQtyIssuedToDate
                    < bom.WOBOMTotalRequired
                AND bom.WOQtyIssuedToDate >= 0
                AND items.PartGroupCode
                    NOT LIKE 'CONSUMABLE%'
            GROUP BY
                bom.WONo,
                bom.WOPartNo),

        Qry_I13_3_ListWoWithPartialKitComp AS
        (SELECT
            partial.WONo,
            partial.WOPartNo,
            partial.QtyItemsPartialKit
            FROM Qry_I13_2_SelectPartIssueWoBom AS partial
                INNER JOIN [Pcubed].[dbo].[worksOrder] AS wo
                    ON partial.WONo = wo.WONo
            WHERE
                wo.WOStatusDescription = 'Completed'
                AND partial.QtyItemsPartialKit > 0)

        SELECT
            WONo AS y,
            QtyItemsPartialKit AS x

        FROM Qry_I13_3_ListWoWithPartialKitComp

        ORDER BY
            QtyItemsPartialKit DESC;
        """,
        title=
            "WO Completed with OS Material Issues",

        x_label=
            "QTY",

        formatter=
            "integer",
    ),
    "D3a": ChartDefinition(
        sql="""
        SELECT
            CONCAT(
                po.PONum,
                '/',
                po.PODetItemNum,
                ' # ',
                items.PartNo,
                ' # £',
                po.PODetUnitPrice * po.PODetQtyReq,
                ' (',
                emp.[Name],
                ')'
            ) AS y,

            DATEDIFF(
                DAY,
                CAST(GETDATE() AS date),
                required.RequiredDate
            ) AS [x],

            DATEDIFF(
                DAY,
                CAST(GETDATE() AS date),
                po.PODetDatePromised
            ) AS target,

            po.PODetUnitPrice
                * po.PODetQtyReq AS [Value],

            0 AS targetStart

        FROM [Pcubed].[dbo].[AllLivePO] AS po

        LEFT JOIN [Pcubed].[dbo].[allItems] AS items
            ON po.PODetPart = items.PartNo

        LEFT JOIN [Pcubed].[dbo].[employees] AS emp
            ON po.POBuyer = emp.BadgeNo

        LEFT JOIN [Pcubed].[dbo].[SQDIP_PONoDemandOK] AS demandOK
            ON po.PONum = demandOK.PO
            AND po.PODetItemNum = demandOK.Line


        CROSS APPLY
        (
            SELECT
                CASE

                    WHEN items.MinOfWOSchedStartDate IS NULL
                        THEN items.MinOfSOLinePromisedDate

                    WHEN items.MinOfSOLinePromisedDate
                            < items.MinOfWOSchedStartDate
                        THEN items.MinOfSOLinePromisedDate

                    ELSE items.MinOfWOSchedStartDate

                END AS RequiredDate
        ) AS required


        WHERE
            DATEDIFF(
                DAY,
                CAST(GETDATE() AS date),
                required.RequiredDate
            ) >= 28

            AND (
                po.PODetUnitPrice
                * po.PODetQtyReq
            ) > 100

            AND po.PODetDatePromised NOT IN
            (
                '2008-08-08',
                '2018-12-25',
                '2018-12-31',
                '2018-04-01',
                '2001-01-01'
            )

            AND (
                COALESCE(
                    items.DemandSO,
                    0
                )
                +
                COALESCE(
                    items.DemandWO,
                    0
                )
            ) > 0

            AND required.RequiredDate
                > DATEADD(
                    DAY,
                    28,
                    po.PODetDatePromised
                )

            AND demandOK.PO IS NULL


        ORDER BY x DESC;
        """,
        title=
            "PO's With Promised Date over 4 Weeks before Demand > £100",

        x_label=
            "Days",

        formatter=
            "integer",
    ),
    "D9": ChartDefinition(
        sql="""
        SELECT DISTINCT
            CONCAT(po.PONum,'/', po.PODetItemNum,' <',emp.[Name], '>') AS y,
            DATEDIFF(DAY,CAST(GETDATE() AS date),po.PODetDatePromised) AS x
        FROM [Pcubed].[dbo].[AllLivePO] AS po
        INNER JOIN [Pcubed].[dbo].[AllItems] AS items
            ON po.PODetPart = items.PartNo
        INNER JOIN [Pcubed].[dbo].[employees] AS emp
            ON po.POBuyer = emp.BadgeNo
        INNER JOIN [Pcubed].[dbo].[OOB-TRACKER-RECEIVED] AS oob
            ON po.POSuppAddressName = oob.SuppName
        WHERE DATEDIFF(DAY,CAST(GETDATE() AS date),po.PODetDatePromised) <= 14
            AND (po.PODetQtyReq- po.PODetQtyRec) > 0
            AND (po.PODetDateLatest IS NULL
                OR CAST(po.PODetDateLatest AS date
                ) NOT IN
                (
                    '2001-01-01',
                    '2018-12-31',
                    '2081-12-25',
                    '2111-01-01',
                    '2081-01-04',
                    '2010-10-10',
                    '2009-09-09',
                    '2008-08-08',
                    '2002-02-02'
                ))

            AND (po.PODetDatePromised IS NULL
                OR CAST( po.PODetDatePromised AS date) NOT IN
                (
                    '2001-01-01',
                    '2018-12-31',
                    '2081-12-25',
                    '2111-01-01',
                    '2081-01-04',
                    '2010-10-10',
                    '2009-09-09',
                    '2008-08-08',
                    '2002-02-02'
                ))

            AND oob.RECEIVED = 'N'
        ORDER BY x ASC;

        """,
        title=
            "PO's due in next 2 weeks inc overdue (Not confirmed)",

        x_label=
            "Days untill PO promised",

        formatter=
            "integer",
    ), 
    "P10": ChartDefinition(
        sql="""
            WITH Qry_Exp_P10_CPP AS
            (
                SELECT
                    CONCAT(
                        cpp.[CPP],
                        ' ',
                        cpp.[Customer],
                        ' (',
                        COALESCE(
                            cpp.[Status],
                            ''
                        ),
                        ')'
                    ) AS Info,

                    DATEDIFF(
                        DAY,
                        cpp.DateRaised,
                        GETDATE()
                    ) AS DaysOpen,

                    DATEDIFF(
                        DAY,
                        GETDATE(),
                        cpp.RequiredDate
                    ) AS DaysTillReq,

                    CASE
                        WHEN UPPER(
                            COALESCE(
                                cpp.[Status],
                                ''
                            )
                        ) LIKE '%PENDING%'
                            THEN 'p10-pending'

                        ELSE 'p10-days-open'
                    END AS className

                FROM [Pcubed].[dbo].[CPP_Log] AS cpp

                WHERE
                    cpp.DateRaised IS NOT NULL

                    AND
                    (
                        cpp.Status IS NULL

                        OR
                        (
                            cpp.Status NOT LIKE '%APPROVED%'
                            AND cpp.Status NOT LIKE '%REJECTED%'
                            AND cpp.Status NOT LIKE '%CANCELLED%'
                            AND cpp.Status NOT LIKE '%NOT REQ%'
                            AND cpp.Status NOT LIKE '%EXPIRED%'
                        )
                    )
            )

            SELECT
                Info AS y,

                DaysOpen AS x,

                DaysTillReq AS secondaryValue,

                className

            FROM Qry_Exp_P10_CPP

            ORDER BY
                DaysOpen DESC;
        """,

        title=
            "CPP Open Items",

        x_label=
            "Days",

        axis=
            "left",

        formatter=
            "integer",

        meta={
            "secondaryValueFormatter":
                "integer",

            "secondaryValueLabel":
                "Days Till Required",
            
            "subtitle":
             "🟩 DaysTillReq | 🟦 DaysOpen | 🟥 Pending"
        },
    ),
    "D5": ChartDefinition(
        sql="""
        SELECT
            CONCAT([EnquiryNo] , ' ' , [EnqCustID] , ' # ' , [EnqDepartment]) AS y,
            DATEDIFF(DAY,GETDATE(), [EnqRequiredDate]) AS x
        FROM
            AllEnq
        GROUP BY
            [EnquiryNo],
            [EnqCustID],
            [EnqDepartment],
            [EnqRequiredDate],
            AllEnq.EnqStatus
        HAVING
            (((AllEnq.EnqStatus) = '#Received'))
        ORDER BY x asc;
        """,
        title=
            "Enquiry Status -Recieved",

        x_label=
            "Days Untill Enq Response Required",

        axis=
            "left",

        formatter=
            "integer",
    ),
    "D3b": ChartDefinition(
        sql="""
            SELECT
                CONCAT(
                    po.PONum,
                    '/',
                    po.PODetItemNum,
                    ' # ',
                    items.PartNo,
                    ' # £',
                    po.PODetUnitPrice * po.PODetQtyReq,
                    ' (',
                    emp.[Name],
                    ')'
                ) AS y,

                DATEDIFF(
                    DAY,
                    CAST(GETDATE() AS date),
                    required.RequiredDate
                ) AS x,

                DATEDIFF(
                    DAY,
                    CAST(GETDATE() AS date),
                    po.PODetDatePromised
                ) AS secondaryValue

            FROM [Pcubed].[dbo].[AllLivePO] AS po

            LEFT JOIN [Pcubed].[dbo].[AllItems] AS items
                ON po.PODetPart = items.PartNo

            LEFT JOIN [Pcubed].[dbo].[employees] AS emp
                ON po.POBuyer = emp.BadgeNo

            LEFT JOIN [Pcubed].[dbo].[SQDIP_PONoDemandOK] AS demandOK
                ON po.PODetItemNum = demandOK.Line
                AND po.PONum = demandOK.PO

            CROSS APPLY
            (
                SELECT
                    CASE
                        WHEN items.MinOfWOSchedStartDate IS NULL
                            THEN items.MinOfSOLinePromisedDate

                        WHEN items.MinOfSOLinePromisedDate
                            < items.MinOfWOSchedStartDate
                            THEN items.MinOfSOLinePromisedDate

                        ELSE items.MinOfWOSchedStartDate
                    END AS RequiredDate
            ) AS required

            WHERE
                DATEDIFF(
                    DAY,
                    CAST(GETDATE() AS date),
                    required.RequiredDate
                ) >= 28

                AND (
                    po.PODetUnitPrice
                    * po.PODetQtyReq
                ) > 100

                AND CAST(
                    po.PODetDatePromised AS date
                ) NOT IN
                (
                    '2008-08-08',
                    '2018-12-25',
                    '2018-12-31',
                    '2018-04-01',
                    '2001-01-01'
                )

                AND required.RequiredDate
                    > po.PODetDatePromised

                AND
                (
                    YEAR(required.RequiredDate)
                        <> YEAR(po.PODetDatePromised)

                    OR

                    MONTH(required.RequiredDate)
                        <> MONTH(po.PODetDatePromised)
                )

                AND
                (
                    COALESCE(
                        items.DemandSO,
                        0
                    )
                    +
                    COALESCE(
                        items.DemandWO,
                        0
                    )
                ) > 0

                AND demandOK.PO IS NULL

            ORDER BY
                x DESC;
        """,

        title=
            "PO Demand Date Review",

        x_label=
            "Days",

        axis=
            "left",

        formatter=
            "integer",

        meta={
            "secondaryValueFormatter":
                "integer",

            "secondaryValueLabel":
                "Days Till Due",

            "subtitle":
                "🟦 Days Till Required | 🟪 Days Till Due"
        },
    ),
    "D2": ChartDefinition(
        sql="""
        ;WITH [PV658-ReFormat] AS (SELECT
            PV658.PO,
            pv658.PO_Line,
            PV658.DateRaised,
            PV658.DateReleased
        FROM
            PV658
        WHERE
            (PV658.PO) IS NOT NULL
            AND (PV658.PO_line) IS NOT NULL),

        Qry_Exp_D2_QueryPO AS (SELECT
            [PV658-ReFormat].PO AS PO,
            [PV658-ReFormat].PO_line,
            [PV658-BuyerEngineer].FirstOfBuyer AS Buyer,
            AllLivePO.POSuppAddressName,
            [PV658-ReFormat].DateRaised,
            DATEDIFF(DAY, Max([DateRaised]), GETDATE()) AS DaysInQuery,
            [PV658-ReFormat].DateReleased,
            AllLivePO.PODetDatePromised
        FROM
            (
                AllLivePO
                RIGHT JOIN [PV658-ReFormat] ON (AllLivePO.PODetItemNum = [PV658-ReFormat].PO_line)
                AND (AllLivePO.PONum = [PV658-ReFormat].PO)
            )
            LEFT JOIN [PV658-BuyerEngineer] ON AllLivePO.PONum = [PV658-BuyerEngineer].PO
        GROUP BY
            [PV658-ReFormat].PO,
            [PV658-ReFormat].PO_line,
            [PV658-BuyerEngineer].FirstOfBuyer,
            AllLivePO.POSuppAddressName,
            [PV658-ReFormat].DateRaised,
            [PV658-ReFormat].DateReleased,
            AllLivePO.PODetDatePromised
        HAVING
            (
                (([PV658-ReFormat].DateRaised) > '7 / 31 / 2023')
                AND (([PV658-ReFormat].DateReleased) IS NULL)
            ))
            
        SELECT
            CONCAT([PO] , '/' , [PO_line] , ' # ' , [Buyer] , ' # ' , [POSuppAddressName]) AS y,
            Qry_Exp_D2_QueryPO.DaysInQuery AS x,
            0 AS targetStart,
            5 AS target

        FROM
            Qry_Exp_D2_QueryPO

        GROUP BY
                [PO],
                [PO_line],
                [Buyer],
                [POSuppAddressName],
                Qry_Exp_D2_QueryPO.DaysInQuery

        ORDER BY x DESC;
        """,
        title=
            "Purchase Orders In Query",

        x_label=
            "Days in Query",

        axis=
            "left",

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
                "rightValue",
                "secondaryValue"
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
                "targetStart",
                "rightValue",
                "secondaryValue"
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