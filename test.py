import re
from transliterate import translit
from datetime import datetime


def transliterate_text(text: str) -> str:
    text = text.lower().strip()
    text = translit(text, "ru", reversed=True)
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def generate_filename():
    name = input("Название соревнования: ").strip()
    doc_type = input(
        "Тип документа (, reglament, protocol, startlist, zayavka, report, results): ").strip()
    ext = input("Расширение файла (pdf, docx, xlsx и т.д.): ").strip()
    date_str = input(
        "Дата соревнования (YYYY-MM-DD) или Enter для сегодня: ").strip()

    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    translit_name = transliterate_text(name)

    filename = f"{date_str}__{doc_type}_{translit_name}.{ext}"
    return filename


if __name__ == "__main__":
    fname = generate_filename()
    print("Сгенерированное имя файла:", fname)
