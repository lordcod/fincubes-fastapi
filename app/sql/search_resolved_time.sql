SELECT
    column_name,
    is_generated
FROM
    information_schema.columns
WHERE
    table_name = 'results'
    AND column_name = 'resolved_time';