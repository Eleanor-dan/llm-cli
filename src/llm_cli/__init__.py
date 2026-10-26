# """llm-cli: 命令行工具入口。"""

# import argparse
from importlib.metadata import PackageNotFoundError, version as _dist_version

try:
    __version__ = _dist_version("llm-cli")
except PackageNotFoundError:  # 未安装（例如直接跑源码）时的兜底
    __version__ = "0.1.0"


# def main(argv: list[str] | None = None) -> None:
#     parser = argparse.ArgumentParser(prog="llm_cli", description="llm-cli 命令行工具")
#     parser.add_argument(
#         "-V",
#         "--version",
#         action="version",
#         version=f"%(prog)s {__version__}",
#     )
#     parser.parse_args(argv)

#     print("Hello from llm-cli!")


