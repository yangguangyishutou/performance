import os
from pathlib import Path

from utils.Generator import Generator
from utils.api_key import api_keys
from path_config import cfg_translated_project_dir_path

from steps.translation_pipeline import TranslationPipeline
        

def main(ai_name:str, project_name:str, test_mode:bool=False, auto_update:bool=False):
    """主函数"""
    output_dir = str(cfg_translated_project_dir_path(ai_name, project_name))

    print(f"Starting translation for project: {project_name}")
    print(f"Output directory: {output_dir}")
    print(f"Using model: {ai_name}")
    print("-" * 50)

    # 初始化
    generator = Generator(ai_name, api_keys['deepseek'], test_mode=test_mode)
    pipeline = TranslationPipeline(generator)

    pipeline.run_full_translation(ai_name, project_name, auto_update=auto_update)

    print("=" * 50)
    print("Translation completed successfully!")
    print(f"Generated files are available at: {output_dir}")

    return 0


if __name__ == '__main__':
    exit(main("deepseek", "Cookie", False, False))







        




