from __future__ import annotations

from typing import Any, Callable, ClassVar, Dict, Iterator, Self, Tuple, Optional, Type, TypeVar, overload


BF = TypeVar("BF", bound="BaseFlags")


class flag_value:
    def __init__(self, func: Callable[[Any], int]) -> None:
        self.flag = func(None)
        self.__doc__ = func.__doc__

    @overload
    def __get__(self, instance: None, owner: Type[BF]) -> Self: ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool: ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self) -> str:
        return f"<flag_value flag={self.flag!r}>"


def fill_with_flags(*, inverted: bool = False):
    def decorator(cls: Type[BF]):
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2**max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls

    return decorator


class alias_flag_value(flag_value):
    pass


class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ("value",)

    def __init__(self, **kwargs: bool) -> None:
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid flag name.")
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} value={self.value}>"

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(
                f"Value to set for {self.__class__.__name__} must be a bool.")


@fill_with_flags()
class StageStatus(BaseFlags):
    @flag_value
    def DSQ(self) -> int: return 1 << 0
    @flag_value
    def DNS(self) -> int: return 1 << 1
    @flag_value
    def WDR(self) -> int: return 1 << 2
    @flag_value
    def EXH(self) -> int: return 1 << 3
    @flag_value
    def COMPLETED(self) -> int: return 1 << 4


status = StageStatus._from_value(-1)
print(status.DSQ)
print(status.WDR)

status.DSQ = False
status.COMPLETED = True
print(list(status))
print([name for name, is_set in status if is_set])
print(status)
print(status.value)
