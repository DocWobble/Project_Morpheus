import sys
import pathlib
import types

# Add the package path so we can import orpheus_tts
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# Stub out the vllm module required by engine_class during import
vllm_stub = types.ModuleType("vllm")
vllm_stub.AsyncLLMEngine = object
vllm_stub.AsyncEngineArgs = object
vllm_stub.SamplingParams = object
sys.modules.setdefault("vllm", vllm_stub)

# Stub out transformers.AutoTokenizer
transformers_stub = types.ModuleType("transformers")
transformers_stub.AutoTokenizer = types.SimpleNamespace(from_pretrained=lambda *args, **kwargs: object())
sys.modules.setdefault("transformers", transformers_stub)

from orpheus_tts.engine_class import OrpheusModel


def test_map_model_params_medium_3b():
    model = OrpheusModel.__new__(OrpheusModel)
    assert OrpheusModel._map_model_params(model, 'medium-3b') == 'canopylabs/orpheus-tts-0.1-finetune-prod'
