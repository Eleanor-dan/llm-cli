# pytest 会自动发现 tests/ 目录下 test_*.py 文件里的 test_* 函数。
# 不需要写 main()，直接运行 `pytest` 即可。
import pytest

from llm_cli.prompts import build_messages


def test_user_only() -> None:
    # assert 是 Python 的断言语句。
    # 失败时 pytest 会打印左右两边的值，比 C 的 assert 信息更多。
    assert build_messages("hello") == [{"role": "user", "content": "hello"}]


def test_with_system() -> None:
    messages = build_messages("hello", system="be brief")

    # 列表按顺序比较；字典不关心键的顺序。
    assert messages == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "hello"},
    ]


def test_blank_system_is_ignored() -> None:
    assert build_messages("hello", system="   ") == [{"role": "user", "content": "hello"}]


def test_empty_prompt_raises() -> None:
    # pytest.raises 是上下文管理器：
    # 它要求 with 块里必须抛出指定异常，否则测试失败。
    with pytest.raises(ValueError):
        build_messages("   ")
