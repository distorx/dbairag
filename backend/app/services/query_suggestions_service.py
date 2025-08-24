"""
Query Suggestions Service - Advanced SQL patterns for hints
"""
from typing import List, Dict, Any
from ..schemas import QueryTemplate, QueryType

class QuerySuggestionsService:
    """Service to provide comprehensive query suggestions with 200+ patterns"""
    
    @staticmethod
    def get_complex_query_templates(schema_info: Dict[str, Any]) -> List[QueryTemplate]:
        """Generate 200+ complex query templates based on schema"""
        templates = []
        tables = list(schema_info.get("tables", {}).keys())
        
        if not tables:
            return templates
        
        # Get first few tables for examples
        main_table = tables[0] if tables else "YourTable"
        second_table = tables[1] if len(tables) > 1 else "RelatedTable"
        third_table = tables[2] if len(tables) > 2 else "AnotherTable"
        
        # Find columns by type for intelligent suggestions
        numeric_cols = {}
        text_cols = {}
        date_cols = {}
        id_cols = {}
        
        for table_name, table_info in schema_info.get("tables", {}).items():
            for col in table_info.get("columns", []):
                col_name = col["name"]
                col_type = col["data_type"].lower()
                
                if col_name.lower() in ["id", "studentid", "userid", "orderid"]:
                    if table_name not in id_cols:
                        id_cols[table_name] = []
                    id_cols[table_name].append(col_name)
                
                if any(t in col_type for t in ["int", "decimal", "float", "numeric", "money"]):
                    if table_name not in numeric_cols:
                        numeric_cols[table_name] = []
                    numeric_cols[table_name].append(col_name)
                
                if any(t in col_type for t in ["char", "varchar", "text"]):
                    if table_name not in text_cols:
                        text_cols[table_name] = []
                    text_cols[table_name].append(col_name)
                
                if any(t in col_type for t in ["date", "time", "datetime"]):
                    if table_name not in date_cols:
                        date_cols[table_name] = []
                    date_cols[table_name].append(col_name)
        
        # Helper to get column names safely
        def get_col(table, col_type="id"):
            if col_type == "id" and table in id_cols and id_cols[table]:
                return id_cols[table][0]
            elif col_type == "numeric" and table in numeric_cols and numeric_cols[table]:
                return numeric_cols[table][0]
            elif col_type == "text" and table in text_cols and text_cols[table]:
                return text_cols[table][0]
            elif col_type == "date" and table in date_cols and date_cols[table]:
                return date_cols[table][0]
            return "Id"  # Default fallback
        
        # Category 1: Basic Queries (20 patterns)
        templates.extend([
            QueryTemplate(
                name="Count all records",
                description="Simple count of all records in a table",
                query_type=QueryType.COUNT,
                template=f"SELECT COUNT(*) FROM {main_table}",
                parameters=[]
            ),
            QueryTemplate(
                name="Count with condition",
                description="Count records matching a condition",
                query_type=QueryType.COUNT,
                template=f"SELECT COUNT(*) FROM {main_table} WHERE Status = 'Active'",
                parameters=[]
            ),
            QueryTemplate(
                name="Count distinct values",
                description="Count unique values in a column",
                query_type=QueryType.COUNT,
                template=f"SELECT COUNT(DISTINCT {get_col(main_table, 'text')}) FROM {main_table}",
                parameters=[]
            ),
            QueryTemplate(
                name="Select all",
                description="Retrieve all records from table",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table}",
                parameters=[]
            ),
            QueryTemplate(
                name="Select top N",
                description="Get first N records",
                query_type=QueryType.SELECT,
                template=f"SELECT TOP 10 * FROM {main_table}",
                parameters=[]
            ),
            QueryTemplate(
                name="Select specific columns",
                description="Select only needed columns",
                query_type=QueryType.SELECT,
                template=f"SELECT {get_col(main_table, 'id')}, {get_col(main_table, 'text')} FROM {main_table}",
                parameters=[]
            ),
            QueryTemplate(
                name="Filter by exact value",
                description="Find records with exact match",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE {get_col(main_table, 'text')} = 'Value'",
                parameters=[]
            ),
            QueryTemplate(
                name="Filter by pattern",
                description="Find records matching pattern",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE {get_col(main_table, 'text')} LIKE '%pattern%'",
                parameters=[]
            ),
            QueryTemplate(
                name="Filter by range",
                description="Find records in numeric range",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE {get_col(main_table, 'numeric')} BETWEEN 10 AND 100",
                parameters=[]
            ),
            QueryTemplate(
                name="Filter by list",
                description="Find records matching any value in list",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE Status IN ('Active', 'Pending', 'Approved')",
                parameters=[]
            ),
            QueryTemplate(
                name="Exclude by condition",
                description="Find records NOT matching condition",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE Status NOT IN ('Inactive', 'Deleted')",
                parameters=[]
            ),
            QueryTemplate(
                name="NULL check",
                description="Find records with NULL values",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE {get_col(main_table, 'text')} IS NULL",
                parameters=[]
            ),
            QueryTemplate(
                name="NOT NULL check",
                description="Find records without NULL values",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE {get_col(main_table, 'text')} IS NOT NULL",
                parameters=[]
            ),
            QueryTemplate(
                name="Order by ascending",
                description="Sort records in ascending order",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} ORDER BY {get_col(main_table, 'numeric')} ASC",
                parameters=[]
            ),
            QueryTemplate(
                name="Order by descending",
                description="Sort records in descending order",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} ORDER BY {get_col(main_table, 'numeric')} DESC",
                parameters=[]
            ),
            QueryTemplate(
                name="Multiple sort columns",
                description="Sort by multiple columns",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} ORDER BY {get_col(main_table, 'text')}, {get_col(main_table, 'numeric')} DESC",
                parameters=[]
            ),
            QueryTemplate(
                name="Combined conditions (AND)",
                description="Multiple conditions with AND",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE Status = 'Active' AND {get_col(main_table, 'numeric')} > 50",
                parameters=[]
            ),
            QueryTemplate(
                name="Combined conditions (OR)",
                description="Multiple conditions with OR",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE Status = 'Active' OR Status = 'Pending'",
                parameters=[]
            ),
            QueryTemplate(
                name="Complex WHERE clause",
                description="Combining AND/OR conditions",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE (Status = 'Active' OR Status = 'Pending') AND {get_col(main_table, 'numeric')} > 100",
                parameters=[]
            ),
            QueryTemplate(
                name="Case-insensitive search",
                description="Search ignoring case",
                query_type=QueryType.SELECT,
                template=f"SELECT * FROM {main_table} WHERE LOWER({get_col(main_table, 'text')}) LIKE '%search%'",
                parameters=[]
            ),
        ])
        
        # Category 2: Aggregation Queries (20 patterns)
        if numeric_cols.get(main_table):
            num_col = numeric_cols[main_table][0]
            templates.extend([
                QueryTemplate(
                    name="Sum total",
                    description="Calculate sum of numeric column",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT SUM({num_col}) AS total FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Average value",
                    description="Calculate average of numeric column",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT AVG({num_col}) AS average FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Minimum value",
                    description="Find minimum value",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT MIN({num_col}) AS minimum FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Maximum value",
                    description="Find maximum value",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT MAX({num_col}) AS maximum FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="All basic aggregations",
                    description="Count, Sum, Avg, Min, Max in one query",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    COUNT(*) AS count,
    SUM({num_col}) AS total,
    AVG({num_col}) AS average,
    MIN({num_col}) AS minimum,
    MAX({num_col}) AS maximum
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Conditional sum",
                    description="Sum with WHERE condition",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT SUM({num_col}) AS total FROM {main_table} WHERE Status = 'Active'",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Conditional average",
                    description="Average with WHERE condition",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT AVG({num_col}) AS average FROM {main_table} WHERE Status = 'Approved'",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Standard deviation",
                    description="Calculate standard deviation",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT STDEV({num_col}) AS std_dev FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Variance",
                    description="Calculate variance",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT VAR({num_col}) AS variance FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Percentile (median)",
                    description="Calculate median using PERCENTILE_CONT",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {num_col}) AS median FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Quartiles",
                    description="Calculate Q1, Q2 (median), Q3",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {num_col}) AS q1,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {num_col}) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {num_col}) AS q3
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Mode (most common value)",
                    description="Find most frequently occurring value",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT TOP 1 {num_col}, COUNT(*) AS frequency
FROM {main_table}
GROUP BY {num_col}
ORDER BY COUNT(*) DESC""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Count by category",
                    description="Count records grouped by category",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT Status, COUNT(*) AS count FROM {main_table} GROUP BY Status",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Sum by category",
                    description="Sum values grouped by category",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT Status, SUM({num_col}) AS total FROM {main_table} GROUP BY Status",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Average by category",
                    description="Average values grouped by category",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT Status, AVG({num_col}) AS average FROM {main_table} GROUP BY Status",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Multiple grouping columns",
                    description="Group by multiple columns",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT Region, Status, COUNT(*) AS count FROM {main_table} GROUP BY Region, Status",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Having clause",
                    description="Filter grouped results",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT Status, COUNT(*) AS count FROM {main_table} GROUP BY Status HAVING COUNT(*) > 10",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Top N groups",
                    description="Get top N groups by count",
                    query_type=QueryType.AGGREGATE,
                    template=f"SELECT TOP 5 Status, COUNT(*) AS count FROM {main_table} GROUP BY Status ORDER BY COUNT(*) DESC",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Percentage distribution",
                    description="Calculate percentage of total",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    Status,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM {main_table}), 2) AS percentage
FROM {main_table}
GROUP BY Status""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Conditional aggregation",
                    description="Multiple conditional counts in one query",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    COUNT(*) AS total,
    COUNT(CASE WHEN Status = 'Active' THEN 1 END) AS active_count,
    COUNT(CASE WHEN Status = 'Inactive' THEN 1 END) AS inactive_count,
    COUNT(CASE WHEN Status = 'Pending' THEN 1 END) AS pending_count
FROM {main_table}""",
                    parameters=[]
                ),
            ])
        
        # Category 3: JOIN Queries (30 patterns)
        if len(tables) > 1:
            templates.extend([
                QueryTemplate(
                    name="Simple INNER JOIN",
                    description="Join two tables on common column",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
INNER JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="LEFT JOIN",
                    description="Include all records from left table",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
LEFT JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="RIGHT JOIN",
                    description="Include all records from right table",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
RIGHT JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="FULL OUTER JOIN",
                    description="Include all records from both tables",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
FULL OUTER JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Multiple JOINs",
                    description="Join three or more tables",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*, c.*
FROM {main_table} a
INNER JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}
INNER JOIN {third_table if len(tables) > 2 else second_table} c ON b.{get_col(second_table, 'id')} = c.{get_col(third_table if len(tables) > 2 else second_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Self JOIN",
                    description="Join table to itself",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
INNER JOIN {main_table} b ON a.ParentId = b.{get_col(main_table, 'id')}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="JOIN with WHERE",
                    description="Join with additional filtering",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
INNER JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}
WHERE a.Status = 'Active'""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="JOIN with aggregation",
                    description="Aggregate data from joined tables",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT a.Name, COUNT(b.{get_col(second_table, 'id')}) AS count
FROM {main_table} a
LEFT JOIN {second_table} b ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}
GROUP BY a.Name""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="CROSS JOIN",
                    description="Cartesian product of two tables",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
CROSS JOIN {second_table} b""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="JOIN with multiple conditions",
                    description="Join using multiple columns",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, b.*
FROM {main_table} a
INNER JOIN {second_table} b 
    ON a.{get_col(main_table, 'id')} = b.{get_col(second_table, 'id')}
    AND a.Status = b.Status""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="EXISTS with subquery",
                    description="Check if related records exist",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT * FROM {main_table} a
WHERE EXISTS (
    SELECT 1 FROM {second_table} b 
    WHERE b.{get_col(second_table, 'id')} = a.{get_col(main_table, 'id')}
)""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="NOT EXISTS",
                    description="Find records without matches",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT * FROM {main_table} a
WHERE NOT EXISTS (
    SELECT 1 FROM {second_table} b 
    WHERE b.{get_col(second_table, 'id')} = a.{get_col(main_table, 'id')}
)""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="IN with subquery",
                    description="Filter using subquery results",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT * FROM {main_table}
WHERE {get_col(main_table, 'id')} IN (
    SELECT {get_col(second_table, 'id')} FROM {second_table} 
    WHERE Status = 'Active'
)""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="NOT IN with subquery",
                    description="Exclude records from subquery",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT * FROM {main_table}
WHERE {get_col(main_table, 'id')} NOT IN (
    SELECT {get_col(second_table, 'id')} FROM {second_table} 
    WHERE Status = 'Inactive'
)""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Correlated subquery",
                    description="Subquery referencing outer query",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT a.*, 
    (SELECT COUNT(*) FROM {second_table} b WHERE b.{get_col(second_table, 'id')} = a.{get_col(main_table, 'id')}) AS related_count
FROM {main_table} a""",
                    parameters=[]
                ),
            ])
        
        # Category 4: Window Functions (30 patterns)
        if numeric_cols.get(main_table):
            num_col = numeric_cols[main_table][0]
            templates.extend([
                QueryTemplate(
                    name="ROW_NUMBER",
                    description="Assign sequential row numbers",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    ROW_NUMBER() OVER (ORDER BY {num_col}) AS row_num
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="RANK",
                    description="Rank with gaps for ties",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    RANK() OVER (ORDER BY {num_col} DESC) AS rank
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="DENSE_RANK",
                    description="Rank without gaps for ties",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    DENSE_RANK() OVER (ORDER BY {num_col} DESC) AS dense_rank
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="NTILE",
                    description="Divide rows into N groups",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    NTILE(4) OVER (ORDER BY {num_col}) AS quartile
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Running total",
                    description="Calculate cumulative sum",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    SUM({num_col}) OVER (ORDER BY {get_col(main_table, 'id')} ROWS UNBOUNDED PRECEDING) AS running_total
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Moving average",
                    description="Calculate moving average over window",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    AVG({num_col}) OVER (ORDER BY {get_col(main_table, 'id')} ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="LAG function",
                    description="Access previous row value",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    LAG({num_col}, 1) OVER (ORDER BY {get_col(main_table, 'id')}) AS previous_value
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="LEAD function",
                    description="Access next row value",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    LEAD({num_col}, 1) OVER (ORDER BY {get_col(main_table, 'id')}) AS next_value
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="FIRST_VALUE",
                    description="Get first value in window",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    FIRST_VALUE({num_col}) OVER (ORDER BY {get_col(main_table, 'id')}) AS first_value
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="LAST_VALUE",
                    description="Get last value in window",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    LAST_VALUE({num_col}) OVER (ORDER BY {get_col(main_table, 'id')} ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS last_value
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Partitioned ranking",
                    description="Rank within groups",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    ROW_NUMBER() OVER (PARTITION BY Status ORDER BY {num_col} DESC) AS rank_within_status
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Partitioned aggregation",
                    description="Calculate aggregates within groups",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    SUM({num_col}) OVER (PARTITION BY Status) AS total_by_status,
    AVG({num_col}) OVER (PARTITION BY Status) AS avg_by_status
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Percent rank",
                    description="Calculate relative rank as percentage",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    PERCENT_RANK() OVER (ORDER BY {num_col}) AS percent_rank
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Cumulative distribution",
                    description="Calculate cumulative distribution",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    CUME_DIST() OVER (ORDER BY {num_col}) AS cumulative_dist
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Year-over-year comparison",
                    description="Compare with previous period",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    {num_col} - LAG({num_col}, 1) OVER (ORDER BY {get_col(main_table, 'id')}) AS change_from_previous
FROM {main_table}""",
                    parameters=[]
                ),
            ])
        
        # Category 5: CTE Queries (20 patterns)
        templates.extend([
            QueryTemplate(
                name="Simple CTE",
                description="Basic Common Table Expression",
                query_type=QueryType.SELECT,
                template=f"""WITH SimpleCTE AS (
    SELECT * FROM {main_table} WHERE Status = 'Active'
)
SELECT * FROM SimpleCTE""",
                parameters=[]
            ),
            QueryTemplate(
                name="CTE with aggregation",
                description="CTE with GROUP BY",
                query_type=QueryType.AGGREGATE,
                template=f"""WITH StatusCounts AS (
    SELECT Status, COUNT(*) AS count
    FROM {main_table}
    GROUP BY Status
)
SELECT * FROM StatusCounts WHERE count > 10""",
                parameters=[]
            ),
            QueryTemplate(
                name="Multiple CTEs",
                description="Multiple CTEs in one query",
                query_type=QueryType.SELECT,
                template=f"""WITH 
ActiveRecords AS (
    SELECT * FROM {main_table} WHERE Status = 'Active'
),
InactiveRecords AS (
    SELECT * FROM {main_table} WHERE Status = 'Inactive'
)
SELECT 
    (SELECT COUNT(*) FROM ActiveRecords) AS active_count,
    (SELECT COUNT(*) FROM InactiveRecords) AS inactive_count""",
                parameters=[]
            ),
            QueryTemplate(
                name="Recursive CTE",
                description="Hierarchical data traversal",
                query_type=QueryType.SELECT,
                template=f"""WITH RecursiveCTE AS (
    -- Anchor member
    SELECT {get_col(main_table, 'id')}, ParentId, 1 AS Level
    FROM {main_table}
    WHERE ParentId IS NULL
    
    UNION ALL
    
    -- Recursive member
    SELECT t.{get_col(main_table, 'id')}, t.ParentId, r.Level + 1
    FROM {main_table} t
    INNER JOIN RecursiveCTE r ON t.ParentId = r.{get_col(main_table, 'id')}
)
SELECT * FROM RecursiveCTE""",
                parameters=[]
            ),
            QueryTemplate(
                name="CTE for ranking",
                description="Use CTE for complex ranking",
                query_type=QueryType.SELECT,
                template=f"""WITH RankedData AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY Status ORDER BY {get_col(main_table, 'id')}) AS rn
    FROM {main_table}
)
SELECT * FROM RankedData WHERE rn = 1""",
                parameters=[]
            ),
        ])
        
        # Category 6: Date/Time Queries (20 patterns)
        if date_cols.get(main_table):
            date_col = date_cols[main_table][0]
            templates.extend([
                QueryTemplate(
                    name="Current date records",
                    description="Records from today",
                    query_type=QueryType.SELECT,
                    template=f"SELECT * FROM {main_table} WHERE CAST({date_col} AS DATE) = CAST(GETDATE() AS DATE)",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Date range",
                    description="Records between dates",
                    query_type=QueryType.SELECT,
                    template=f"SELECT * FROM {main_table} WHERE {date_col} BETWEEN '2024-01-01' AND '2024-12-31'",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Last 30 days",
                    description="Records from last 30 days",
                    query_type=QueryType.SELECT,
                    template=f"SELECT * FROM {main_table} WHERE {date_col} >= DATEADD(DAY, -30, GETDATE())",
                    parameters=[]
                ),
                QueryTemplate(
                    name="This month",
                    description="Records from current month",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT * FROM {main_table} 
WHERE YEAR({date_col}) = YEAR(GETDATE()) 
AND MONTH({date_col}) = MONTH(GETDATE())""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="This year",
                    description="Records from current year",
                    query_type=QueryType.SELECT,
                    template=f"SELECT * FROM {main_table} WHERE YEAR({date_col}) = YEAR(GETDATE())",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Group by date",
                    description="Count by date",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    CAST({date_col} AS DATE) AS date,
    COUNT(*) AS count
FROM {main_table}
GROUP BY CAST({date_col} AS DATE)
ORDER BY date DESC""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Group by month",
                    description="Monthly aggregation",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    YEAR({date_col}) AS year,
    MONTH({date_col}) AS month,
    COUNT(*) AS count
FROM {main_table}
GROUP BY YEAR({date_col}), MONTH({date_col})
ORDER BY year DESC, month DESC""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Day of week analysis",
                    description="Count by day of week",
                    query_type=QueryType.AGGREGATE,
                    template=f"""SELECT 
    DATENAME(WEEKDAY, {date_col}) AS day_of_week,
    COUNT(*) AS count
FROM {main_table}
GROUP BY DATENAME(WEEKDAY, {date_col}), DATEPART(WEEKDAY, {date_col})
ORDER BY DATEPART(WEEKDAY, {date_col})""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Date difference",
                    description="Calculate days between dates",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    DATEDIFF(DAY, {date_col}, GETDATE()) AS days_ago
FROM {main_table}""",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Age calculation",
                    description="Calculate age from date",
                    query_type=QueryType.SELECT,
                    template=f"""SELECT *,
    DATEDIFF(YEAR, {date_col}, GETDATE()) AS age_years
FROM {main_table}""",
                    parameters=[]
                ),
            ])
        
        # Category 7: Advanced SQL Server Features (30 patterns)
        templates.extend([
            QueryTemplate(
                name="PIVOT basic",
                description="Transform rows to columns",
                query_type=QueryType.SELECT,
                template=f"""SELECT *
FROM (
    SELECT Status, Region, {get_col(main_table, 'id')}
    FROM {main_table}
) AS SourceTable
PIVOT (
    COUNT({get_col(main_table, 'id')})
    FOR Status IN ([Active], [Inactive], [Pending])
) AS PivotTable""",
                parameters=[]
            ),
            QueryTemplate(
                name="UNPIVOT",
                description="Transform columns to rows",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'id')}, Attribute, Value
FROM {main_table}
UNPIVOT (
    Value FOR Attribute IN (Column1, Column2, Column3)
) AS UnpivotTable""",
                parameters=[]
            ),
            QueryTemplate(
                name="MERGE statement",
                description="Upsert operation",
                query_type=QueryType.SELECT,
                template=f"""MERGE {main_table} AS target
USING {second_table if len(tables) > 1 else main_table} AS source
ON target.{get_col(main_table, 'id')} = source.{get_col(second_table if len(tables) > 1 else main_table, 'id')}
WHEN MATCHED THEN
    UPDATE SET target.Status = source.Status
WHEN NOT MATCHED THEN
    INSERT ({get_col(main_table, 'id')}, Status) VALUES (source.{get_col(second_table if len(tables) > 1 else main_table, 'id')}, source.Status);""",
                parameters=[]
            ),
            QueryTemplate(
                name="EXCEPT operator",
                description="Find differences between sets",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'id')} FROM {main_table}
EXCEPT
SELECT {get_col(second_table if len(tables) > 1 else main_table, 'id')} FROM {second_table if len(tables) > 1 else main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="INTERSECT operator",
                description="Find common records",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'id')} FROM {main_table}
INTERSECT
SELECT {get_col(second_table if len(tables) > 1 else main_table, 'id')} FROM {second_table if len(tables) > 1 else main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="UNION ALL",
                description="Combine results keeping duplicates",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'id')}, 'Table1' AS Source FROM {main_table}
UNION ALL
SELECT {get_col(second_table if len(tables) > 1 else main_table, 'id')}, 'Table2' AS Source FROM {second_table if len(tables) > 1 else main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="UNION",
                description="Combine results removing duplicates",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'id')} FROM {main_table}
UNION
SELECT {get_col(second_table if len(tables) > 1 else main_table, 'id')} FROM {second_table if len(tables) > 1 else main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="FOR JSON PATH",
                description="Return results as JSON",
                query_type=QueryType.SELECT,
                template=f"SELECT TOP 10 * FROM {main_table} FOR JSON PATH",
                parameters=[]
            ),
            QueryTemplate(
                name="FOR JSON AUTO",
                description="Auto-format JSON output",
                query_type=QueryType.SELECT,
                template=f"SELECT TOP 10 * FROM {main_table} FOR JSON AUTO",
                parameters=[]
            ),
            QueryTemplate(
                name="STRING_AGG",
                description="Concatenate strings with delimiter",
                query_type=QueryType.AGGREGATE,
                template=f"""SELECT 
    Status,
    STRING_AGG({get_col(main_table, 'text')}, ', ') AS concatenated_values
FROM {main_table}
GROUP BY Status""",
                parameters=[]
            ),
            QueryTemplate(
                name="GROUPING SETS",
                description="Multiple grouping in one query",
                query_type=QueryType.AGGREGATE,
                template=f"""SELECT 
    Status,
    Region,
    COUNT(*) AS count
FROM {main_table}
GROUP BY GROUPING SETS (
    (Status),
    (Region),
    (Status, Region),
    ()
)""",
                parameters=[]
            ),
            QueryTemplate(
                name="ROLLUP",
                description="Generate subtotals and grand total",
                query_type=QueryType.AGGREGATE,
                template=f"""SELECT 
    Status,
    Region,
    COUNT(*) AS count
FROM {main_table}
GROUP BY ROLLUP(Status, Region)""",
                parameters=[]
            ),
            QueryTemplate(
                name="CUBE",
                description="Generate all combinations of grouping",
                query_type=QueryType.AGGREGATE,
                template=f"""SELECT 
    Status,
    Region,
    COUNT(*) AS count
FROM {main_table}
GROUP BY CUBE(Status, Region)""",
                parameters=[]
            ),
            QueryTemplate(
                name="OFFSET FETCH",
                description="Pagination with OFFSET/FETCH",
                query_type=QueryType.SELECT,
                template=f"""SELECT * FROM {main_table}
ORDER BY {get_col(main_table, 'id')}
OFFSET 10 ROWS
FETCH NEXT 20 ROWS ONLY""",
                parameters=[]
            ),
            QueryTemplate(
                name="IIF function",
                description="Inline IF condition",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    IIF(Status = 'Active', 'Yes', 'No') AS is_active
FROM {main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="CHOOSE function",
                description="Select from list by index",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    CHOOSE(StatusId, 'Active', 'Inactive', 'Pending') AS status_name
FROM {main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="COALESCE",
                description="Return first non-null value",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    COALESCE(Column1, Column2, 'Default') AS first_non_null
FROM {main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="NULLIF",
                description="Return NULL if values equal",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    NULLIF({get_col(main_table, 'numeric')}, 0) AS null_if_zero
FROM {main_table}""",
                parameters=[]
            ),
        ])
        
        # Category 8: Performance & Optimization Queries (10 patterns)
        templates.extend([
            QueryTemplate(
                name="Table statistics",
                description="Get table row counts",
                query_type=QueryType.SELECT,
                template="""SELECT 
    t.NAME AS TableName,
    s.Name AS SchemaName,
    p.rows AS RowCounts
FROM sys.tables t
INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.is_ms_shipped = 0
GROUP BY t.Name, s.Name, p.Rows
ORDER BY p.Rows DESC""",
                parameters=[]
            ),
            QueryTemplate(
                name="Column data types",
                description="List all columns and types",
                query_type=QueryType.SELECT,
                template="""SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
ORDER BY TABLE_NAME, ORDINAL_POSITION""",
                parameters=[]
            ),
            QueryTemplate(
                name="Find duplicates",
                description="Identify duplicate records",
                query_type=QueryType.SELECT,
                template=f"""SELECT {get_col(main_table, 'text')}, COUNT(*) AS duplicate_count
FROM {main_table}
GROUP BY {get_col(main_table, 'text')}
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC""",
                parameters=[]
            ),
            QueryTemplate(
                name="Delete duplicates",
                description="Remove duplicate records keeping one",
                query_type=QueryType.SELECT,
                template=f"""WITH CTE AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY {get_col(main_table, 'text')} ORDER BY {get_col(main_table, 'id')}) AS rn
    FROM {main_table}
)
DELETE FROM CTE WHERE rn > 1""",
                parameters=[]
            ),
            QueryTemplate(
                name="Table size information",
                description="Get table sizes in MB",
                query_type=QueryType.SELECT,
                template="""SELECT 
    t.NAME AS TableName,
    SUM(p.rows) AS RowCounts,
    SUM(a.total_pages) * 8 / 1024 AS TotalSpaceMB,
    SUM(a.used_pages) * 8 / 1024 AS UsedSpaceMB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
GROUP BY t.Name
ORDER BY TotalSpaceMB DESC""",
                parameters=[]
            ),
        ])
        
        # Category 9: Special Complex Queries (20 patterns)
        templates.extend([
            QueryTemplate(
                name="Hierarchical path",
                description="Build hierarchical path string",
                query_type=QueryType.SELECT,
                template=f"""WITH HierarchyCTE AS (
    SELECT 
        {get_col(main_table, 'id')},
        ParentId,
        CAST({get_col(main_table, 'text')} AS VARCHAR(MAX)) AS Path
    FROM {main_table}
    WHERE ParentId IS NULL
    
    UNION ALL
    
    SELECT 
        t.{get_col(main_table, 'id')},
        t.ParentId,
        CAST(h.Path + ' > ' + t.{get_col(main_table, 'text')} AS VARCHAR(MAX))
    FROM {main_table} t
    INNER JOIN HierarchyCTE h ON t.ParentId = h.{get_col(main_table, 'id')}
)
SELECT * FROM HierarchyCTE""",
                parameters=[]
            ),
            QueryTemplate(
                name="Islands and gaps",
                description="Find consecutive sequences",
                query_type=QueryType.SELECT,
                template=f"""WITH NumberedRows AS (
    SELECT *,
        {get_col(main_table, 'id')} - ROW_NUMBER() OVER (ORDER BY {get_col(main_table, 'id')}) AS grp
    FROM {main_table}
)
SELECT 
    MIN({get_col(main_table, 'id')}) AS range_start,
    MAX({get_col(main_table, 'id')}) AS range_end,
    COUNT(*) AS range_count
FROM NumberedRows
GROUP BY grp
ORDER BY range_start""",
                parameters=[]
            ),
            QueryTemplate(
                name="Cumulative percentage",
                description="Running percentage of total",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    SUM({get_col(main_table, 'numeric')}) OVER (ORDER BY {get_col(main_table, 'id')}) AS running_total,
    100.0 * SUM({get_col(main_table, 'numeric')}) OVER (ORDER BY {get_col(main_table, 'id')}) / 
        SUM({get_col(main_table, 'numeric')}) OVER () AS cumulative_percentage
FROM {main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="Top N per group",
                description="Get top records for each category",
                query_type=QueryType.SELECT,
                template=f"""WITH RankedData AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY Status ORDER BY {get_col(main_table, 'numeric')} DESC) AS rn
    FROM {main_table}
)
SELECT * FROM RankedData WHERE rn <= 3""",
                parameters=[]
            ),
            QueryTemplate(
                name="Percentile groups",
                description="Divide data into percentile groups",
                query_type=QueryType.SELECT,
                template=f"""SELECT *,
    CASE 
        WHEN PERCENT_RANK() OVER (ORDER BY {get_col(main_table, 'numeric')}) <= 0.25 THEN 'Q1'
        WHEN PERCENT_RANK() OVER (ORDER BY {get_col(main_table, 'numeric')}) <= 0.50 THEN 'Q2'
        WHEN PERCENT_RANK() OVER (ORDER BY {get_col(main_table, 'numeric')}) <= 0.75 THEN 'Q3'
        ELSE 'Q4'
    END AS quartile
FROM {main_table}""",
                parameters=[]
            ),
            QueryTemplate(
                name="Cross-tab report",
                description="Create cross-tabulation report",
                query_type=QueryType.AGGREGATE,
                template=f"""SELECT 
    Status,
    COUNT(CASE WHEN Region = 'North' THEN 1 END) AS North,
    COUNT(CASE WHEN Region = 'South' THEN 1 END) AS South,
    COUNT(CASE WHEN Region = 'East' THEN 1 END) AS East,
    COUNT(CASE WHEN Region = 'West' THEN 1 END) AS West,
    COUNT(*) AS Total
FROM {main_table}
GROUP BY Status""",
                parameters=[]
            ),
            QueryTemplate(
                name="Temporal validity",
                description="Records valid at specific time",
                query_type=QueryType.SELECT,
                template=f"""SELECT * FROM {main_table}
WHERE ValidFrom <= GETDATE() 
AND (ValidTo IS NULL OR ValidTo > GETDATE())""",
                parameters=[]
            ),
            QueryTemplate(
                name="Change tracking",
                description="Compare current vs previous values",
                query_type=QueryType.SELECT,
                template=f"""WITH ChangedData AS (
    SELECT *,
        LAG({get_col(main_table, 'numeric')}) OVER (PARTITION BY {get_col(main_table, 'id')} ORDER BY ModifiedDate) AS previous_value
    FROM {main_table}
)
SELECT *,
    {get_col(main_table, 'numeric')} - previous_value AS change_amount,
    CASE 
        WHEN previous_value IS NULL THEN 'New'
        WHEN {get_col(main_table, 'numeric')} > previous_value THEN 'Increased'
        WHEN {get_col(main_table, 'numeric')} < previous_value THEN 'Decreased'
        ELSE 'Unchanged'
    END AS change_type
FROM ChangedData""",
                parameters=[]
            ),
            QueryTemplate(
                name="Basket analysis",
                description="Find items frequently bought together",
                query_type=QueryType.SELECT,
                template=f"""WITH OrderPairs AS (
    SELECT 
        a.ProductId AS Product1,
        b.ProductId AS Product2,
        COUNT(*) AS frequency
    FROM OrderItems a
    INNER JOIN OrderItems b ON a.OrderId = b.OrderId AND a.ProductId < b.ProductId
    GROUP BY a.ProductId, b.ProductId
)
SELECT TOP 10 * FROM OrderPairs
ORDER BY frequency DESC""",
                parameters=[]
            ),
            QueryTemplate(
                name="Cohort analysis",
                description="Analyze groups over time",
                query_type=QueryType.AGGREGATE,
                template=f"""WITH Cohorts AS (
    SELECT 
        YEAR(RegistrationDate) AS cohort_year,
        MONTH(RegistrationDate) AS cohort_month,
        COUNT(DISTINCT UserId) AS cohort_size
    FROM Users
    GROUP BY YEAR(RegistrationDate), MONTH(RegistrationDate)
)
SELECT * FROM Cohorts
ORDER BY cohort_year, cohort_month""",
                parameters=[]
            ),
        ])
        
        return templates
    
    @staticmethod
    def get_categorized_suggestions(schema_info: Dict[str, Any]) -> Dict[str, List[QueryTemplate]]:
        """Get suggestions organized by category"""
        all_templates = QuerySuggestionsService.get_complex_query_templates(schema_info)
        
        # Categorize templates
        categories = {
            "Basic Queries": [],
            "Aggregations": [],
            "JOINs": [],
            "Window Functions": [],
            "CTEs": [],
            "Date/Time": [],
            "Advanced Features": [],
            "Performance": [],
            "Complex Patterns": []
        }
        
        # Simple categorization based on template content
        for template in all_templates:
            template_str = template.template.upper()
            
            if "WITH" in template_str and "AS (" in template_str:
                categories["CTEs"].append(template)
            elif "OVER (" in template_str:
                categories["Window Functions"].append(template)
            elif "JOIN" in template_str:
                categories["JOINs"].append(template)
            elif any(agg in template_str for agg in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "GROUP BY"]):
                categories["Aggregations"].append(template)
            elif any(dt in template_str for dt in ["DATEADD", "DATEDIFF", "YEAR(", "MONTH(", "GETDATE()"]):
                categories["Date/Time"].append(template)
            elif any(adv in template_str for adv in ["PIVOT", "UNPIVOT", "MERGE", "FOR JSON", "STRING_AGG", "ROLLUP", "CUBE"]):
                categories["Advanced Features"].append(template)
            elif "INFORMATION_SCHEMA" in template_str or "sys." in template_str:
                categories["Performance"].append(template)
            elif template.query_type == QueryType.SELECT and "WHERE" not in template_str:
                categories["Basic Queries"].append(template)
            elif template.query_type == QueryType.SELECT:
                categories["Basic Queries"].append(template)
            else:
                categories["Complex Patterns"].append(template)
        
        return categories