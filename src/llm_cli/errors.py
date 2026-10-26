# 自定义异常：继承 Python 内置的 RuntimeError。
#
# 为什么需要它？
# OpenAI SDK 可能抛出很多种异常（网络、鉴权、限流、超时……）。
# 如果 CLI 里逐个捕获会很乱，所以在“边界”统一包成 LLMError，
# 上层只需要处理这一种异常。
class LLMError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        # super() 表示父类 RuntimeError；调用它的初始化方法，
        # 这样 str(exc) 才能拿到我们传入的 message。
        super().__init__(message)

        # 参数前面的 `*` 表示 retryable 只能用关键字传：
        #     LLMError("xxx", retryable=True)
        # 不能写成 LLMError("xxx", True)。
        self.retryable = retryable