ALTER TABLE results
ADD COLUMN resolved_time timetz GENERATED ALWAYS AS (
    CASE
        WHEN result IS NULL
        AND final IS NULL THEN NULL
        WHEN final IS NOT NULL
        OR final < result THEN final
        ELSE result
    END
) STORED;