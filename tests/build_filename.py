import re
import asyncio
from datetime import datetime
from transliterate import translit

try:
    from tortoise import Tortoise
    from app.core.config import settings
    from app.models.competition.competition import Competition
    TORTOISE_AVAILABLE = True
except ImportError:
    TORTOISE_AVAILABLE = False


def transliterate_text(text: str) -> str:
    """Транслитерация и нормализация текста для имени файла."""
    text = text.lower().strip()
    text = translit(text, "ru", reversed=True)
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def build_filename(name: str, date_str: str, doc_type: str, ext: str) -> str:
    """Формирует итоговое имя файла в стандартизированном виде."""
    translit_name = transliterate_text(name)
    return f"{date_str}__{doc_type}_{translit_name}.{ext}"


# === Основная логика ===

async def generate_filename_from_db():
    """Режим: получение данных соревнования по ID из базы."""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
    )

    comp_id = input("ID соревнования: ").strip()
    comp = await Competition.get_or_none(id=int(comp_id))

    if not comp:
        print(f"❌ Соревнование с ID {comp_id} не найдено.")
        await Tortoise.close_connections()
        return

    print(f"\n📘 Найдено соревнование: {comp.name} ({comp.start_date})\n")

    doc_type = input(
        "Тип документа (polozhenie, reglament, protocol, startlist, zayavka, report, results): ").strip()
    ext = input("Расширение файла (pdf, docx, xlsx и т.д.): ").strip()
    date_str = comp.start_date.strftime("%Y-%m-%d")

    filename = build_filename(comp.name, date_str, doc_type, ext)
    print("✅ Сгенерированное имя файла:", filename)
    print("✅ Ссылка:",
          "https://cdn.fincubes.ru/docs/"+filename)

    await Tortoise.close_connections()


def generate_filename_manual():
    """Режим: ручной ввод данных."""
    name = input("Название соревнования: ").strip()
    doc_type = input(
        "Тип документа (polozhenie, reglament, protocol, startlist, zayavka, report, results): ").strip()
    ext = input("Расширение файла (pdf, docx, xlsx и т.д.): ").strip()
    date_str = input("Дата соревнования (YYYY-MM-DD) или Enter для сегодня: ").strip(
    ) or datetime.now().strftime("%Y-%m-%d")

    filename = build_filename(name, date_str, doc_type, ext)
    print("✅ Сгенерированное имя файла:", filename)


# === Точка входа ===

if __name__ == "__main__":
    print("=== Генератор имени файла соревнования ===\n")
    mode = input("Режим работы (1 - ручной, 2 - из БД): ").strip()

    if mode == "2":
        if not TORTOISE_AVAILABLE:
            print("❌ Режим работы с БД недоступен (Tortoise или настройки не найдены).")
        else:
            asyncio.run(generate_filename_from_db())
    else:
        generate_filename_manual()
