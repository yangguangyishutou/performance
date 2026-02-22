from pathlib import Path
import sys
def make_dir(func):
    def wrapper(*args, **kwargs):
        dir_path = func(*args, **kwargs)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        return dir_path
    return wrapper

version = "v2"

# 本项目根目录
project_root_dir_path = Path(__file__).parent.parent.parent
transation_dir_path = project_root_dir_path / "translation_java-cpp"

@make_dir
def cfg_eval_dir_path(ai_name, project_name, strategy) -> Path:
    return transation_dir_path / project_name / ai_name / f"eval_{strategy}"

def cfg_result_dir_path(ai_name, project_name, strategy) -> Path:
    return transation_dir_path / project_name / ai_name / strategy


cfg_all_project_names = [
    "Cookie",
    "CircuitBreakerExecutor",
    "EnableJUnit4MigrationSupport",
    # "IntMath",
    "RateLimiterExecutor"
]

