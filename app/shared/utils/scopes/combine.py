from collections import defaultdict
import itertools
import time
from typing import Iterable, List, Dict, Set, Tuple
import math


def split_roles_and_permissions(
    scopes: Iterable[Dict]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Делит список dict на роли (node начинается с '@') и права.
    """
    roles = []
    permissions = []
    now = time.time()
    for entry in scopes:
        if entry.get("inherited") is not None and entry["inherited"] <= now:
            continue
        if entry["node"].startswith("@"):
            roles.append(entry)
        else:
            permissions.append(entry)
    return roles, permissions


def group_scopes(scopes: Iterable[Dict]) -> Dict[str, Set[str]]:
    """
    Разбивает список scopes на категории и права.

    Пример:
    `["user:*", "admin:read", "-admin:write", "-admin"]` →
    ```
    {
        "user": {"*"},
        "admin": {"read", "-write", "-*"}
    }
    ```

    - Отрицательные scopes начинаются с `-`.
    - Если право не указано (например, `admin`), считается как `admin:*`.
    """
    result: Dict[str, Set[str]] = defaultdict(set)

    for scope in scopes:
        category, right = (scope['node'].split(':', 1) + [None])[:2]
        if right is None:
            right = '*'
        right = f"-{right}" if not scope['value'] else right
        result[category].add(right)

    return dict(result)


def simplify_by_masks(rights: Iterable[str]) -> Set[str]:
    """
    Упрощает права в категории:
    - Если есть `*`, удаляет остальные положительные права.
    - Если есть `-*`, удаляет остальные отрицательные права.
    - Если есть и `*` и `-*`, возвращает только их.
    """
    rights = set(rights)
    has_all = '*' in rights
    has_deny_all = '-*' in rights

    if has_all and has_deny_all:
        return {}
    if has_all:
        return {'*'} | {r for r in rights if r.startswith('-')}
    if has_deny_all:
        return {r for r in rights if not r.startswith('-')}
    return rights


def resolve_conflicts(rights: Iterable[str]) -> Set[str]:
    """
    Разрешает конфликты прав:
    - Если есть и право, и его отрицание (например, `read` и `-read`),
      остаётся только отрицательное.
    """
    rights = set(rights)
    positives = {r for r in rights if not r.startswith('-')}
    negatives = {r[1:] for r in rights if r.startswith('-')}

    cleaned = {
        r for r in positives if r not in negatives
    }
    cleaned.update({f"-{r}" for r in negatives})

    return cleaned


def optimize_categories(categories: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Упрощает и нормализует права в каждой категории:
    - Применяет `simplify_by_masks` и `resolve_conflicts` по каждой категории.
    """
    return {
        name: resolve_conflicts(simplify_by_masks(rights))
        for name, rights in categories.items()
    }


def merge_rights_by_category(
    *extras: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """
    Объединяет несколько словарей прав по категориям:
    - Категории объединяются по ключам.
    - Права из всех словарей суммируются.

    Пример:
        `{"user": {"*"}}`, `{"user": {"read"}}` → `{"user": {"*", "read"}}`
    """
    result: Dict[str, Set[str]] = {}

    all_keys = set(itertools.chain.from_iterable(e.keys() for e in extras))
    for category in all_keys:
        rights = [e.get(category, set())
                  for e in extras]
        result[category] = set(itertools.chain.from_iterable(rights))

    return result


def combine_roles_scopes(roles: Dict[str, Dict]) -> Dict[str, Dict[str, Set[str]]]:
    """
    Объединяет scopes всех ролей с учётом наследования и приоритетов:
    - Наследуемые роли указываются через `@role` в scopes.
    - Проверяется, чтобы родитель не имел меньший ранг.
    - Роли комбинируются по возрастанию ранга.
    """
    result: Dict[str, Dict[str, Set[str]]] = {}

    roles_to_roles: Dict[str, Set[str]] = {}
    roles_to_scopes: Dict[str, Dict[str, Set[str]]] = {}

    for name, role in roles.items():
        scopes = role['scopes']
        role_roles, role_scopes = split_roles_and_permissions(scopes)
        roles_to_roles[name] = set(role['node'][1:] for role in role_roles)
        roles_to_scopes[name] = group_scopes(role_scopes)

    for parent, children in roles_to_roles.items():
        parent_rank = roles[parent]['rank']
        for child in children:
            if roles[child]['rank'] > parent_rank:
                raise ValueError(
                    f'Child role "{child}" has higher rank than parent "{parent}"')

    for name in sorted(roles, key=lambda x: roles[x]['rank']):
        combined_scopes = roles_to_scopes[name]
        for inherited in roles_to_roles[name]:
            if inherited not in result:
                raise ValueError(f'Role "{inherited}" not found')
            combined_scopes = merge_scopes_with_priority(result[inherited],
                                                         combined_scopes)
        result[name] = combined_scopes

    return result


def merge_scopes_with_priority(
    low: Dict[str, Set[str]],
    high: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """
    Объединяет два словаря прав с учётом приоритета:
    - Права из high имеют приоритет над low.
    - Отрицания и маски обрабатываются.
    - `*` в high полностью перекрывает low.
    """
    result: Dict[str, Set[str]] = {}
    all_categories = low.keys() | high.keys()

    if '*' in high:
        return high

    for category in all_categories:
        low_rights = low.get(category, set())
        high_rights = high.get(category, set())

        merged: Set[str] = set()
        all_rights = {r.lstrip('-') for r in low_rights | high_rights}

        if set(['*', '-*']) & set(high_rights):
            merged = high_rights
        else:
            for right in all_rights:
                if f"-{right}" in high_rights:
                    merged.add(f"-{right}")
                elif right in high_rights:
                    merged.add(right)
                elif f"-{right}" in low_rights:
                    merged.add(f"-{right}")
                elif right in low_rights:
                    merged.add(right)

        result[category] = merged

    return result


def combine_all_scopes(
    roles: Dict[str, Dict] | List[Dict],
    default_scopes: List[str],
    user_scopes: List[str]
) -> Dict[str, Set[str]]:
    """
    Комбинирует все источники прав:
    - roles: описание всех ролей
    - default_scopes: базовые права (низкий приоритет)
    - user_scopes: права, явно заданные пользователю (высший приоритет)

    Права объединяются по рангу, от меньшего к большему.
    """
    if isinstance(roles, list):
        roles = {
            role['name']: role
            for role in roles
        }

    user_roles, user_scopes = split_roles_and_permissions(user_scopes)
    default_roles, default_scopes = split_roles_and_permissions(default_scopes)

    final_all_roles_scopes = combine_roles_scopes(roles)
    final_default_scopes = merge_rights_by_category(
        group_scopes(default_scopes),
        *(final_all_roles_scopes[role['node'][1:]] for role in default_roles)
    )
    final_user_scopes = group_scopes(user_scopes)

    priority_map: Dict[float, Dict[str, Set[str]]] = {
        -math.inf: final_default_scopes,
        math.inf: final_user_scopes
    }

    for role in user_roles:
        role_name = role['node'][1:]
        if role_name not in roles:
            continue
        rank = roles[role_name]["rank"]
        priority_map[rank] = final_all_roles_scopes[role_name]

    result: Dict[str, Set[str]] = {}
    for _, scopes in sorted(priority_map.items(), key=lambda x: x[0]):
        result = merge_scopes_with_priority(result, scopes)

    return optimize_categories(result)


def flatten_scopes(scopes: Dict[str, Set[str]]) -> List[str]:
    """
    Преобразует словарь прав в плоский список строк:
    - Категория '*' обрабатывается отдельно.
    - Если category имеет права: ['read', '-write'] →
      результат: 'category:read,-write'
    """
    result = []

    for category, rights in scopes.items():
        if not rights:
            continue

        if category == '*':
            if '-*' in rights:
                continue
            elif rights == {'*'}:
                result.append('*')
            continue
        result.append(f"{category}:" + ','.join(sorted(rights)))

    return result
