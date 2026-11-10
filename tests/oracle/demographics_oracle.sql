-- Independent oracle for examples/pharma_tlf/recipe.yaml, written in SQL and run by DuckDB.
-- It derives the same demographics table with no pandas and no code from pharma_agents, so a
-- disagreement between this and `recompute` points at a formula, not a shared bug.
-- {adsl} is replaced with the CSV path by the test.

WITH pop AS (
    SELECT * FROM read_csv_auto('{adsl}') WHERE SAFFL = 'Y'
),
rows_g AS (                                      -- every subject once per column it belongs to
    SELECT p.*, p.TRT01A AS grp FROM pop p
    UNION ALL
    SELECT p.*, 'Total' AS grp FROM pop p
),
denom AS (SELECT grp, count(*) AS n FROM rows_g GROUP BY grp),

age AS (
    SELECT 'AGE' AS variable, '' AS category, s.statistic, r.grp AS "group",
           CASE s.statistic
               WHEN 'n'      THEN count(r.AGE)
               WHEN 'mean'   THEN avg(r.AGE)
               WHEN 'sd'     THEN stddev_samp(r.AGE)
               WHEN 'median' THEN median(r.AGE)
               WHEN 'min'    THEN min(r.AGE)
               WHEN 'max'    THEN max(r.AGE)
           END AS value
    FROM rows_g r
    CROSS JOIN (VALUES ('n'), ('mean'), ('sd'), ('median'), ('min'), ('max')) AS s(statistic)
    GROUP BY s.statistic, r.grp
),

-- SEX: fixed display order F, M (plus Missing if any null)
cats_sex AS (
    SELECT * FROM (VALUES ('F'), ('M')) AS c(category)
    UNION ALL SELECT 'Missing' WHERE EXISTS (SELECT 1 FROM pop WHERE SEX IS NULL)
),
cnt_sex AS (SELECT grp, coalesce(CAST(SEX AS VARCHAR), 'Missing') AS category, count(*) AS cnt FROM rows_g GROUP BY 1, 2),
sex AS (
    SELECT 'SEX' AS variable, c.category, s.statistic, d.grp AS "group",
           CASE s.statistic WHEN 'n' THEN coalesce(k.cnt, 0) WHEN 'pct' THEN 100.0 * coalesce(k.cnt, 0) / d.n END AS value
    FROM denom d CROSS JOIN cats_sex c CROSS JOIN (VALUES ('n'), ('pct')) AS s(statistic)
    LEFT JOIN cnt_sex k ON k.grp = d.grp AND k.category = c.category
),

-- RACE: observed values, sorted (plus Missing if any null)
cats_race AS (
    SELECT DISTINCT CAST(RACE AS VARCHAR) AS category FROM pop WHERE RACE IS NOT NULL
    UNION ALL SELECT 'Missing' WHERE EXISTS (SELECT 1 FROM pop WHERE RACE IS NULL)
),
cnt_race AS (SELECT grp, coalesce(CAST(RACE AS VARCHAR), 'Missing') AS category, count(*) AS cnt FROM rows_g GROUP BY 1, 2),
race AS (
    SELECT 'RACE' AS variable, c.category, s.statistic, d.grp AS "group",
           CASE s.statistic WHEN 'n' THEN coalesce(k.cnt, 0) WHEN 'pct' THEN 100.0 * coalesce(k.cnt, 0) / d.n END AS value
    FROM denom d CROSS JOIN cats_race c CROSS JOIN (VALUES ('n'), ('pct')) AS s(statistic)
    LEFT JOIN cnt_race k ON k.grp = d.grp AND k.category = c.category
),

-- AGEGR1: observed values, sorted (plus Missing if any null)
cats_agegr AS (
    SELECT DISTINCT CAST(AGEGR1 AS VARCHAR) AS category FROM pop WHERE AGEGR1 IS NOT NULL
    UNION ALL SELECT 'Missing' WHERE EXISTS (SELECT 1 FROM pop WHERE AGEGR1 IS NULL)
),
cnt_agegr AS (SELECT grp, coalesce(CAST(AGEGR1 AS VARCHAR), 'Missing') AS category, count(*) AS cnt FROM rows_g GROUP BY 1, 2),
agegr AS (
    SELECT 'AGEGR1' AS variable, c.category, s.statistic, d.grp AS "group",
           CASE s.statistic WHEN 'n' THEN coalesce(k.cnt, 0) WHEN 'pct' THEN 100.0 * coalesce(k.cnt, 0) / d.n END AS value
    FROM denom d CROSS JOIN cats_agegr c CROSS JOIN (VALUES ('n'), ('pct')) AS s(statistic)
    LEFT JOIN cnt_agegr k ON k.grp = d.grp AND k.category = c.category
)

SELECT variable, category, statistic, "group", CAST(value AS DOUBLE) AS value FROM age
UNION ALL SELECT variable, category, statistic, "group", CAST(value AS DOUBLE) FROM sex
UNION ALL SELECT variable, category, statistic, "group", CAST(value AS DOUBLE) FROM race
UNION ALL SELECT variable, category, statistic, "group", CAST(value AS DOUBLE) FROM agegr
ORDER BY variable, category, statistic, "group";
