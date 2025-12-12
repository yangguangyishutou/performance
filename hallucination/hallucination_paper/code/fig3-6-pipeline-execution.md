
```python
class TranslationPipeline:
    def run_full_translation(self, ai_name, project_name):
        # Load and analyze source code
        data = load_translation_graph(ai_name, project_name)

        # Class-level translation
        self.header_scheme_step.generate_schemes(headers)
        self.header_translation_step.translate_headers(headers)

        # Method-level translation with dependency ordering
        self.method_scheme_step.generate_schemes(method_nodes)
        self.method_translation_step.translate_methods(method_nodes)

        # Generate final C++ files
        self.cpp_file_generation_step.generate_files(ai_name, project_name)
```