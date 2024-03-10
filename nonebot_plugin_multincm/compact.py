from typing import Literal, Optional

from nonebot.compat import PYDANTIC_V2

if PYDANTIC_V2:
    from pydantic import field_validator  # type: ignore

else:
    from pydantic import validator

    def field_validator(
        __field: str,
        *fields: str,
        mode: Literal["before", "after", "wrap", "plain"] = "after",
        check_fields: Optional[bool] = None,  # noqa: ARG001
    ):
        return validator(__field, *fields, pre=(mode == "before"), allow_reuse=True)
