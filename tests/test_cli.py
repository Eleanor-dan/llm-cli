import json

from llm_cli.cli import main
from llm_cli.errors import LLMError
from llm_cli.llm import Completion


class FakeClient:
    """假客户端：不联网，直接返回固定结果。

    main() 的 client_factory 参数让我们可以把它注入进去。
    """

    def __init__(self, settings) -> None:
        self.settings = settings

    def complete(self, messages, **kwargs) -> Completion:
        return Completion(
            content="hello",
            model="fake-model",
            prompt_tokens=3,
            completion_tokens=4,
        )

    def stream(self, messages, **kwargs):
        # 含 yield 的函数是生成器；这里模拟两个 token。
        yield "he"
        yield "llo"


def test_plain_output(monkeypatch, capsys) -> None:
    # monkeypatch 是 pytest 的 fixture：
    # setenv 会在测试结束后自动恢复环境变量，不会污染其他测试。
    monkeypatch.setenv("LLM_API_KEY", "test")

    code = main(["hi"], client_factory=FakeClient)

    # capsys 捕获 stdout/stderr；readouterr() 返回一个带 out/err 属性的对象。
    captured = capsys.readouterr()
    assert code == 0
    assert "hello" in captured.out


def test_stream_output(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")

    code = main(["--stream", "hi"], client_factory=FakeClient)

    captured = capsys.readouterr()
    assert code == 0
    assert "hello" in captured.out


def test_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")

    code = main(["--json", "hi"], client_factory=FakeClient)

    # json.loads 把字符串解析成 dict。
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["content"] == "hello"
    assert payload["usage"]["total_tokens"] == 7
    assert payload["model"] == "fake-model"


def test_file_input_and_system_prompt(monkeypatch, capsys, tmp_path) -> None:
    # tmp_path 是 pytest 提供的临时目录（pathlib.Path 对象），测试结束自动清理。
    monkeypatch.setenv("LLM_API_KEY", "test")
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("from file", encoding="utf-8")

    # 用闭包变量 seen 记录传给客户端的 messages。
    seen: dict = {}

    class CapturingClient(FakeClient):
        # 子类重写父类方法；super() 调用父类实现。
        def complete(self, messages, **kwargs) -> Completion:
            seen["messages"] = messages
            return super().complete(messages, **kwargs)

    code = main(
        ["--file", str(prompt_file), "--system", "be brief"],
        client_factory=CapturingClient,
    )

    assert code == 0
    assert seen["messages"][0] == {"role": "system", "content": "be brief"}
    assert seen["messages"][1] == {"role": "user", "content": "from file"}


def test_missing_api_key(monkeypatch, capsys, tmp_path) -> None:
    # 切到临时目录，避免读到项目里的 .env。
    monkeypatch.chdir(tmp_path)
    # 删除环境变量；raising=False 表示变量不存在也不报错。
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    code = main(["hi"], client_factory=FakeClient)

    captured = capsys.readouterr()
    assert code == 2
    assert "LLM_API_KEY" in captured.err


def test_empty_prompt(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")

    # 传一个空字符串，模拟用户没输入内容。
    code = main([""], client_factory=FakeClient)

    assert code == 2
    assert "No prompt" in capsys.readouterr().err


def test_llm_error_returns_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test")

    class BrokenClient(FakeClient):
        def complete(self, messages, **kwargs) -> Completion:
            raise LLMError("upstream is down")

    code = main(["hi"], client_factory=BrokenClient)

    captured = capsys.readouterr()
    assert code == 1
    assert "upstream is down" in captured.err


