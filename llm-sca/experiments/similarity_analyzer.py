from similarity_cos import CosSimilarty
from similarity_diff import Difference

class SimilarityAnalyzer:
    def __init__(self, model_A_name, model_B_name, **kwargs):
        self.model_A_name = model_A_name
        self.model_B_name = model_B_name
        self.kwargs = kwargs


    def analyze(self, method = "cos"):
        if method == "cos":
            analyzer = CosSimilarty(self.model_A_name, self.model_B_name, **self.kwargs)
            cos_ne = analyzer.compare_models_cos()
            stats = analyzer.plot_cosine_similarity_stats(cos_ne)
            analyzer.save_stats_to_json(stats, update_existing=True)
            return cos_ne
        elif method == "diff":
            analyzer = Difference(self.model_A_name, self.model_B_name, **self.kwargs)
            stats_list, global_sample_array = analyzer.compute_elementwise_differences()
            stats = analyzer.plot_diff_stats(global_sample_array)
            analyzer.save_stats_to_json(stats, update_existing=True)
            return stats_list
        

if __name__ == '__main__':
    analyzer = SimilarityAnalyzer('amitom/gpt2-DiabloGPT-SLERP',
                            'amitom/gpt2-DiabloGPT-TA',
                            model_A_type = "",
                            model_A_base = "openai-community/gpt2",
                            model_B_type = "",
                            model_B_base = "openai-community/gpt2")
    analyzer.analyze(method="diff")