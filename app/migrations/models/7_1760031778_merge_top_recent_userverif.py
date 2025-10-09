from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 1️⃣ Добавляем новое поле is_top к таблице athletes
    ALTER TABLE athletes ADD COLUMN is_top BOOL DEFAULT FALSE;

    -- Переносим данные из top_athletes
    UPDATE athletes
    SET is_top = TRUE
    WHERE id IN (SELECT athlete_id FROM top_athletes);

    -- 2️⃣ Добавляем новое поле last_processed_at к таблице competitions
    ALTER TABLE competitions ADD COLUMN last_processed_at TIMESTAMP NULL;

    -- Переносим дату из recent_events (если есть created_at)
    UPDATE competitions
    SET last_processed_at = re.created_at
    FROM recent_events re
    WHERE competitions.id = re.competition_id;

    -- 3️⃣ Добавляем поле state в таблицу user_verification
    ALTER TABLE userverification ADD COLUMN state TEXT NULL;

    -- 4️⃣ Удаляем больше не нужные таблицы
    DROP TABLE IF EXISTS top_athletes;
    DROP TABLE IF EXISTS recent_events;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 1️⃣ Восстанавливаем таблицу top_athletes
    CREATE TABLE top_athletes (
        id SERIAL PRIMARY KEY,
        athlete_id INT NOT NULL REFERENCES athletes (id) ON DELETE CASCADE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO top_athletes (athlete_id, created_at)
    SELECT id, CURRENT_TIMESTAMP FROM athletes WHERE is_top = TRUE;

    -- 2️⃣ Восстанавливаем таблицу recent_events
    CREATE TABLE recent_events (
        id SERIAL PRIMARY KEY,
        competition_id INT NOT NULL REFERENCES competitions (id) ON DELETE CASCADE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO recent_events (competition_id, created_at)
    SELECT id, last_processed_at FROM competitions
    WHERE last_processed_at IS NOT NULL;

    -- 3️⃣ Удаляем новые поля
    ALTER TABLE athletes DROP COLUMN is_top;
    ALTER TABLE competitions DROP COLUMN last_processed_at;
    ALTER TABLE user_verification DROP COLUMN state;
    """
