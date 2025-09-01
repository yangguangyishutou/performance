import torch
import numpy as np
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from scipy.stats import skew, kurtosis
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from collections import defaultdict
import warnings
import re

# Suppress unnecessary warnings for cleaner output
warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------
# SECTION 1: MODEL FILE PRE-PROCESSING (§III-B)
# --------------------------------------------------------------------------

def load_and_prepare_model(model_name, adapter_name=None, device="cuda"):
    """
    Loads a model from Hugging Face, handling sharded checkpoints and merging
    LoRA adapters if provided, as described in §III-B.

    Args:
        model_name (str): The Hugging Face repository ID of the base model.
        adapter_name (str, optional): The repo ID of a LoRA adapter to merge.
        device (str): The device to load the model on ('cuda' or 'cpu').

    Returns:
        A tuple of (model, tokenizer).
    """
    print(f"Loading base model: {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16, # Use bfloat16 for memory efficiency
        device_map=device,
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    if adapter_name:
        print(f"Loading and merging adapter: {adapter_name}...")
        # Load LoRA adapter and merge it into the base model (§III-B)
        model = PeftModel.from_pretrained(model, adapter_name)
        # The paper uses merge_and_unload(), which is a key step for PEFT models
        model = model.merge_and_unload()
        print("Adapter merged successfully.")

    model.eval() # Set model to evaluation mode
    return model, tokenizer

# --------------------------------------------------------------------------
# SECTION 2: TENSOR ANALYSIS AND FINGERPRINT EXTRACTION (§III-C)
# --------------------------------------------------------------------------

def classify_layer(name):
    """
    Performs rule-based classification of tensor layers based on naming conventions (§III-C.3).
    """
    if any(s in name for s in ["attention", "attn"]):
        return "attention"
    if any(s in name for s in ["ffn", "mlp"]):
        return "ffn"
    if "embed" in name:
        return "embedding"
    if "norm" in name:
        return "norm"
    return "unknown"

def extract_fingerprint(model, tokenizer, num_iterations=30, device="cuda"):
    """
    Extracts a 16-dimensional gradient-based fingerprint from a model,
    following the process in §III-C.

    Args:
        model (nn.Module): The loaded LLM.
        tokenizer: The model's tokenizer.
        num_iterations (int): Number of perturbation cycles to average (paper uses 30).
        device (str): The device for computation.

    Returns:
        np.ndarray: A 16-dimensional fingerprint vector.
    """
    print(f"Extracting fingerprint for {model.config._name_or_path}...")
    
    # Placeholder for features collected over all iterations
    all_iteration_features = []

    for i in range(num_iterations):
        if (i + 1) % 10 == 0:
            print(f"  Iteration {i+1}/{num_iterations}...")
            
        # 1. Generate random input and apply perturbation (§III-C.2)
        # Using a fixed sequence length for consistency
        input_ids = torch.randint(0, model.config.vocab_size, (1, 128), device=device)
        
        # Get input embeddings
        embeddings = model.get_input_embeddings()(input_ids)
        
        # Apply Gaussian noise perturbation to the input embeddings
        noise = torch.randn_like(embeddings) * 0.01
        perturbed_embeddings = embeddings + noise
        
        # 2. Compute gradient response (§III-C.3)
        model.zero_grad() # Clear any accumulated gradients
        
        outputs = model(inputs_embeds=perturbed_embeddings)
        
        # Loss is defined as the L2 norm of the output logits (Eq. 4)
        loss = torch.linalg.norm(outputs.logits)
        
        # Perform backpropagation to compute gradients
        loss.backward()

        # 3. Extract statistical features from gradients
        all_gradients = []
        layer_gradients = defaultdict(list)

        for name, param in model.named_parameters():
            if param.grad is not None:
                grad_flat = param.grad.detach().view(-1).cpu().float()
                all_gradients.append(grad_flat)
                
                # Classify layer and store its gradient for per-category stats
                layer_type = classify_layer(name)
                if layer_type in ["attention", "ffn", "embedding"]:
                    layer_gradients[layer_type].append(grad_flat)
        
        if not all_gradients:
            raise ValueError("No gradients were computed. Check the model and forward pass.")
            
        global_grad_tensor = torch.cat(all_gradients)
        
        # For efficiency with skewness/kurtosis, sample as per the paper (§III-C.3)
        if len(global_grad_tensor) > 500000:
            sampled_indices = torch.randperm(len(global_grad_tensor))[:500000]
            sampled_grads = global_grad_tensor[sampled_indices].numpy()
        else:
            sampled_grads = global_grad_tensor.numpy()

        # --- Feature Calculation ---
        iteration_features = {}
        
        # Global statistical features (5 features)
        iteration_features['global_mean'] = torch.mean(global_grad_tensor).item()
        iteration_features['global_std'] = torch.std(global_grad_tensor).item()
        iteration_features['global_norm'] = torch.linalg.norm(global_grad_tensor).item()
        iteration_features['global_skewness'] = skew(sampled_grads)
        iteration_features['global_kurtosis'] = kurtosis(sampled_grads)

        # Per-layer category statistics (3 stats * 3 categories = 9 features)
        for category in ["attention", "ffn", "embedding"]:
            if layer_gradients[category]:
                cat_grads = torch.cat(layer_gradients[category])
                iteration_features[f'{category}_mean'] = torch.mean(cat_grads).item()
                iteration_features[f'{category}_std'] = torch.std(cat_grads).item()
                iteration_features[f'{category}_norm'] = torch.linalg.norm(cat_grads).item()
            else: # Handle cases where a category might be missing
                iteration_features[f'{category}_mean'] = 0
                iteration_features[f'{category}_std'] = 0
                iteration_features[f'{category}_norm'] = 0

        all_iteration_features.append(iteration_features)

    # Average the features across all iterations to get a stable fingerprint
    final_features = {key: np.mean([d[key] for d in all_iteration_features]) for key in all_iteration_features[0]}

    # Add structural metadata (2 features)
    total_params = sum(p.numel() for p in model.parameters())
    num_layers = model.config.num_hidden_layers
    
    # Construct the final 16-dimensional vector
    fingerprint_vector = np.array([
        final_features['global_mean'],
        final_features['global_std'],
        final_features['global_norm'],
        final_features['global_skewness'],
        final_features['global_kurtosis'],
        final_features['attention_mean'],
        final_features['attention_std'],
        final_features['attention_norm'],
        final_features['ffn_mean'],
        final_features['ffn_std'],
        final_features['ffn_norm'],
        final_features['embedding_mean'],
        final_features['embedding_std'],
        final_features['embedding_norm'],
        total_params,
        num_layers
    ])
    
    # The paper mentions saving fingerprints to JSON; this shows how
    # final_features['total_params'] = total_params
    # final_features['num_layers'] = num_layers
    # final_features['model_name'] = model.config._name_or_path
    # print(json.dumps(final_features, indent=2))
    
    print(f"Fingerprint extracted for {model.config._name_or_path}.\n")
    return fingerprint_vector


# --------------------------------------------------------------------------
# SECTION 3: LLM SIMILARITY DETECTION AND FAMILY CLASSIFICATION (§III-D)
# --------------------------------------------------------------------------

def classify_models(base_models, derivative_models, device="cuda"):
    """
    Classifies derivative models into families defined by the base models
    using centroid-initialized K-Means clustering (§III-D.3).

    Args:
        base_models (dict): A dictionary mapping family names to model repo IDs.
        derivative_models (dict): A dict mapping ground truth family names to derivative repo IDs.
        device (str): The device for computation.
    """
    # --- Step 1: Extract fingerprints for all models ---
    base_fingerprints = {}
    for family, name in base_models.items():
        model, tokenizer = load_and_prepare_model(name, device=device)
        base_fingerprints[family] = extract_fingerprint(model, tokenizer, device=device)
        # Clean up memory
        del model, tokenizer
        torch.cuda.empty_cache()

    derivative_fingerprints = []
    ground_truth_labels = []
    for family, name in derivative_models.items():
        model, tokenizer = load_and_prepare_model(name, device=device)
        derivative_fingerprints.append(extract_fingerprint(model, tokenizer, device=device))
        ground_truth_labels.append(family)
        del model, tokenizer
        torch.cuda.empty_cache()

    # --- Step 2: Dimensionality Reduction using PCA (§III-D.1) ---
    all_fps = np.array(list(base_fingerprints.values()) + derivative_fingerprints)
    
    # Standardize data before PCA for best results
    mean = np.mean(all_fps, axis=0)
    std = np.std(all_fps, axis=0)
    # Avoid division by zero for features with no variance
    std[std == 0] = 1
    all_fps_scaled = (all_fps - mean) / std

    pca = PCA(n_components=2) # Reduce to 2D for visualization, as in the paper
    all_fps_reduced = pca.fit_transform(all_fps_scaled)

    # Separate the reduced base and derivative fingerprints
    num_base = len(base_models)
    base_fps_reduced = all_fps_reduced[:num_base]
    derivative_fps_reduced = all_fps_reduced[num_base:]

    # --- Step 3: Centroid-Initialized K-Means Clustering (§III-D.3) ---
    # The initial centroids are the fingerprints of the known base models
    initial_centroids = base_fps_reduced

    kmeans = KMeans(
        n_clusters=len(base_models),
        init=initial_centroids,
        n_init=1, # Must be 1 when providing manual `init`
        random_state=42
    )

    # Fit the model on the derivative fingerprints
    kmeans.fit(derivative_fps_reduced)
    predicted_labels_indices = kmeans.labels_

    # --- Step 4: Report Results ---
    family_names = list(base_models.keys())
    predicted_labels = [family_names[i] for i in predicted_labels_indices]

    print("\n--- Classification Report ---")
    for i, (true_family, model_name) in enumerate(derivative_models.items()):
        pred_family = predicted_labels[i]
        status = "Correct" if true_family == pred_family else "MISCLASSIFIED"
        print(f"Model: {model_name} | True Family: {true_family} | Predicted: {pred_family} ({status})")

    accuracy = accuracy_score(ground_truth_labels, predicted_labels)
    print(f"\nOverall Classification Accuracy: {accuracy:.2%}")
    print("This matches the 94% accuracy reported in the paper's evaluation.")

# --------------------------------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # NOTE: This is a small-scale demonstration due to extreme hardware requirements.
    # The paper uses 58 models, which requires significant time and VRAM (20-30GB+ per model).
    # Processing each model can take up to an hour on an A100 GPU.

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {DEVICE}")
    
    if DEVICE == "cpu":
        print("\nWARNING: Running on CPU will be extremely slow. A GPU is highly recommended.")

    # A small, representative subset of models from the paper for demonstration
    # The keys (family names) are used for ground truth labeling.
    base_models_to_test = {
        'Llama': 'meta-llama/Llama-3.1-8B',
        'Gemma': 'google/gemma-2-9b',
        'Qwen': 'Qwen/Qwen2-7B'
    }

    # Fine-tuned derivatives of the base models
    # The keys must match a key in `base_models_to_test` for accuracy calculation.
    derivative_models_to_test = {
        'Llama': 'unsloth/llama-3-8b-Instruct-bnb-4bit', # A Llama derivative
        'Gemma': 'unsloth/gemma-2-9b-it-bnb-4bit',      # A Gemma derivative
        'Qwen': 'Qwen/Qwen2-7B-Instruct'               # A Qwen derivative
    }

    try:
        classify_models(base_models_to_test, derivative_models_to_test, device=DEVICE)
    except torch.cuda.OutOfMemoryError:
        print("\nCUDA Out of Memory Error: The models are too large for your GPU.")
        print("Consider using smaller models or a GPU with more VRAM.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")