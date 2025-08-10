ALTER TABLE results
ADD COLUMN resolved_time timetz GENERATED ALWAYS AS (
    CASE
        WHEN result IS NULL AND final IS NULL THEN NULL
        WHEN result IS NULL THEN final
        WHEN final IS NULL THEN result
        ELSE LEAST(result, final)
    END
) STORED;
