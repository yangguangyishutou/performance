import os
from pathlib import Path

from utils.Generator import Generator
from path_config import cfg_translated_project_dir_path, source_project_dir_path

from steps.translation_pipeline import TranslationPipeline

def main(ai_name:str, project_name:str, 
        test_mode:bool=False, 
        force_rebuild_graph:bool=False,
        header_scheme_step:bool=True,
        header_translation_step:bool=True,
        method_scheme_step:bool=True,
        method_translation_step:bool=True,
        cpp_file_generation_step:bool=True,
        agent_review_step:bool=True,
    ):
    """主函数"""
    output_dir = str(cfg_translated_project_dir_path(ai_name, project_name))

    print(f"Starting translation for project: {project_name}")
    print(f"Output directory: {output_dir}")
    print(f"Using model: {ai_name}")
    print("-" * 50)

    # 初始化
    generator = Generator(ai_name, test_mode=test_mode)
    pipeline = TranslationPipeline(generator)

    pipeline.run_full_translation(ai_name, project_name, 
        force_rebuild_graph=force_rebuild_graph,
        header_scheme_step=header_scheme_step,
        header_translation_step=header_translation_step,
        method_scheme_step=method_scheme_step,
        method_translation_step=method_translation_step,
        cpp_file_generation_step=cpp_file_generation_step,
        agent_review_step=agent_review_step,
    )

    print("Translation completed successfully!")
    print(f"Generated files are available at: {output_dir}")

    return 0


if __name__ == '__main__':
    # exit(main("deepseek", "Cookie", False, False))
    project_names = []
    for project_dir in source_project_dir_path.iterdir():
        if project_dir.is_dir():
            project_names.append(project_dir.name)
    print(f"project names: {project_names}")
    for project_name in project_names:
        # if project_name in ['NoopIndexDAO', 'IntMath', 'HoverMenuService', 'EnableJUnit4MigrationSupport']:
            main("qwen", project_name, 
                test_mode=False,
                force_rebuild_graph=True, # 强制重新构建图（会清除翻译进度）
                header_scheme_step=False,
                header_translation_step=False,
                method_scheme_step=False,
                method_translation_step=False,
                cpp_file_generation_step=False,
                agent_review_step=False,
            )
            # break
        # break








        




