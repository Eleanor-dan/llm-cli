# 这个文件让你可以用 `python -m llm_cli` 的方式运行整个包。
# Python 在运行 `python -m 包名` 时，会自动执行包里的 __main__.py。

# 从同目录的 cli.py 导入 main 函数。
# 前面的点 `.` 表示“当前包”，是相对导入。
from .cli import main

# 只有“直接运行这个文件”时才执行下面的代码；
# 如果它只是被别的模块 import，就不会执行。
if __name__ == "__main__":
    # main() 返回整数退出码：0 成功，非 0 失败。
    # SystemExit 会把退出码传给 shell，等价于 C 里的 return 0/1。
    raise SystemExit(main())