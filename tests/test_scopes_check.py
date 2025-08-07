
from app.shared.clients.scopes.check import has_scope


def test_has_scope():
    # 1. Нет scope_to_check — всегда True
    assert has_scope(["*"], None) is True
    assert has_scope([], None) is True

    # 2. Глобальный wildcard даёт доступ ко всем правам
    assert has_scope(["*"], "user:read") is True
    assert has_scope(["*"], "billing:delete") is True

    # 3. Запрет в глобальной категории перекрывает wildcard
    assert has_scope(["*", "user:-read"], "user:read") is False
    assert has_scope(["*", "billing:-delete"], "billing:create") is True
    assert has_scope(["*", "user:-read"], "user:write") is True

    # 4. Проверка без wildcard, права включены явно
    assert has_scope(["user:read,write"], "user:read") is True
    assert has_scope(["user:read,write"], "user:write") is True
    assert has_scope(["user:read,write"], "user:delete") is False

    # 5. Проверка с явным запретом в категории
    assert has_scope(["user:read,-write"], "user:read") is True
    assert has_scope(["user:read,-write"], "user:write") is False
    assert has_scope(["user:read,-*"], "user:write") is False
    assert has_scope(["user:read"], "user:write") is False
    assert has_scope(["user:read,-*"], "user:read") is True

    # 6. Несколько категорий
    scopes = ["user:read,write", "billing:read,-delete",
              "posts:create", "admin:*"]
    assert has_scope(scopes, "user:read") is True
    assert has_scope(scopes, "billing:read") is True
    assert has_scope(scopes, "billing:delete") is False
    assert has_scope(scopes, "posts:create") is True
    assert has_scope(scopes, "posts:delete") is False
    assert has_scope(scopes, "admin:create") is True

    # 7. Запрет с wildcard в правах категории
    assert has_scope(["user:*,-write"], "user:read") is True
    assert has_scope(["user:*,-write"], "user:write") is False

    # 8. Категория отсутствует и нет глобального wildcard — доступ запрещён
    assert has_scope(["billing:read"], "user:read") is False

    # 9. Категория с wildcard и множественные запреты
    assert has_scope(["user:*,-write,-delete"], "user:read") is True
    assert has_scope(["user:*,-write,-delete"], "user:write") is False
    assert has_scope(["user:*,-write,-delete"], "user:delete") is False

    # 10. Категория с wildcard и запретом по wildcard (отключить все кроме включенных)
    assert has_scope(["user:-*,read"], "user:read") is True
    assert has_scope(["user:-*,read"], "user:write") is False

    # 11. Проверка запрета без включений в категории
    assert has_scope(["user:-read"], "user:read") is False
    assert has_scope(["user:-read"], "user:write") is False

    # 12. Проверка включения без запрета
    assert has_scope(["user:read"], "user:read") is True
    assert has_scope(["user:read"], "user:write") is False

    # 13. Смешанный случай — есть wildcard, но запрет в другом scope
    scopes = ["*", "billing:-delete"]
    assert has_scope(scopes, "user:read") is True
    assert has_scope(scopes, "billing:delete") is False
    assert has_scope(scopes, "billing:create") is True

    # 14. Запрет wildcard без явных включений — запрет для всех прав категории
    assert has_scope(["user:-*"], "user:read") is False
    assert has_scope(["user:-*"], "user:write") is False

    # 15. Глобальный wildcard с запретом конкретного права в другой категории
    scopes = ["*", "posts:-create"]
    assert has_scope(scopes, "posts:create") is False
    assert has_scope(scopes, "posts:delete") is True
    assert has_scope(scopes, "user:write") is True

    # 16. Перекрытие wildcard в категории и глобальном wildcard, приоритет запрета
    scopes = ["*", "user:*,-write"]
    assert has_scope(scopes, "user:read") is True
    assert has_scope(scopes, "user:write") is False

    # 17. Смешанный случай с отключением wildcard и включением отдельного права
    scopes = ["user:-*,read"]
    assert has_scope(scopes, "user:read") is True
    assert has_scope(scopes, "user:write") is False

    # 18. Несколько категорий с wildcard и конфликтами
    scopes = ["user:*,-write", "billing:read,-write", "posts:*,-delete"]
    assert has_scope(scopes, "user:read") is True
    assert has_scope(scopes, "user:write") is False
    assert has_scope(scopes, "billing:read") is True
    assert has_scope(scopes, "billing:write") is False
    assert has_scope(scopes, "posts:create") is True
    assert has_scope(scopes, "posts:delete") is False

    # 19. Отсутствующая категория, без глобального wildcard — всегда False
    scopes = ["user:read,write", "billing:read"]
    assert has_scope(scopes, "posts:create") is False
    assert has_scope(scopes, "admin:delete") is False

    # 20. Пустой scopes — доступ только без проверки
    assert has_scope([], None) is True
    assert has_scope([], "user:read") is False

    print("Все объединённые тесты пройдены!")
