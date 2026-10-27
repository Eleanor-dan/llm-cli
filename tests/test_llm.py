# SimpleNamespace 是标准库里的“空对象”，可以随手挂属性。
# 这里用它来伪造 OpenAI SDK 的返回对象，避免真的发请求。
from types import SimpleNamespace

import pytest

from llm_cli.config import Settings
from llm_cli.errors import LLMError
from llm_cli.llm import LLMClient


def _chunk(text: str) -> SimpleNamespace:
    """伪造一个流式 chunk，结构模仿 SDK：
    chunk.choices[0].delta.content
    """
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def _response(text: str) -> SimpleNamespace:
    """伪造一个非流式 response。"""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        model="fake-model",
        usage=SimpleNamespace(prompt_tokens=3, completion_tokens=4),
    )


class FakeCompletions:
    """假的 chat.completions 对象，只实现 create()。"""

    def __init__(self, *, response=None, chunks=None, error: Exception | None = None) -> None:
        self.response = response
        self.chunks = chunks or []
        self.error = error
        # 记录最后一次调用的参数，方便断言“参数有没有透传”。
        self.last_kwargs: dict = {}

    def create(self, **kwargs):
        # **kwargs 表示接收任意关键字参数，打包成字典。
        self.last_kwargs = kwargs

        if self.error:
            raise self.error

        if kwargs.get("stream"):
            # iter(list) 把列表变成迭代器，模拟 SDK 的流式返回。
            return iter(self.chunks)

        return self.response


class FakeOpenAI:
    """假的 OpenAI 客户端，只有 chat.completions 这一条路径。"""

    def __init__(self, completions: FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


def _client(completions: FakeCompletions) -> LLMClient:
    # 关键：把假 client 注入进去，LLMClient 就不会创建真实 OpenAI。
    settings = Settings(api_key="test", model="fake-model")
    return LLMClient(settings, client=FakeOpenAI(completions))


def test_complete_returns_content_and_usage() -> None:
    client = _client(FakeCompletions(response=_response("hello")))

    result = client.complete([{"role": "user", "content": "hi"}])

    assert result.content == "hello"
    assert result.model == "fake-model"
    assert result.prompt_tokens == 3
    assert result.completion_tokens == 4
    # total_tokens 是 @property，访问时不用加括号。
    assert result.total_tokens == 7


def test_complete_wraps_sdk_error() -> None:
    client = _client(FakeCompletions(error=RuntimeError("boom")))

    # match 是正则匹配异常信息。
    with pytest.raises(LLMError, match="boom"):
        client.complete([{"role": "user", "content": "hi"}])


def test_stream_yields_non_empty_deltas() -> None:
    client = _client(FakeCompletions(chunks=[_chunk("he"), _chunk(""), _chunk("llo")]))

    # 生成器是“惰性”的，list(...) 才会真正把它跑完并收集结果。
    assert list(client.stream([{"role": "user", "content": "hi"}])) == ["he", "llo"]


def test_stream_passes_overrides() -> None:
    completions = FakeCompletions(chunks=[_chunk("x")])
    client = _client(completions)

    # 只关心副作用（参数透传），所以把生成器消费掉但不保存结果。
    list(
        client.stream(
            [{"role": "user", "content": "hi"}],
            model="other",
            temperature=0.1,
            max_tokens=10,
        )
    )

    assert completions.last_kwargs["model"] == "other"
    assert completions.last_kwargs["temperature"] == 0.1
    assert completions.last_kwargs["max_tokens"] == 10
    assert completions.last_kwargs["stream"] is True
