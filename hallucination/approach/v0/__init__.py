# sitp_script/__init__.py
# 统一对外导出，外部可 `import sitp_script as sitp` 直接调用。

from .dataset.data_set import create_data_set
from .strategy_class.translator import translate
from .strategy_method.translator_method import translate_method

# bottomup 可能因相对导入未改好而抛错；做一次优雅降级，避免整个包导入失败
try:
    from .strategy_bottomup.translator_bottomup import translate_bottomup, make_files
except Exception as _e:
    def translate_bottomup(*args, **kwargs):  # type: ignore
        raise ImportError(f"strategy_bottomup not available: {_e}")
    def make_files(*args, **kwargs):          # type: ignore
        raise ImportError(f"strategy_bottomup not available: {_e}")

from .file_operation import clone_files, init_logger
from .api_key import api_keys
from .Generator import Generator

__all__ = [
    # dataset
    "create_data_set",
    # strategies
    "translate",
    "translate_method",
    "translate_bottomup",
    "make_files",
    # utils
    "clone_files",
    "init_logger",
    "api_keys",
    "Generator",
]
import asyncio