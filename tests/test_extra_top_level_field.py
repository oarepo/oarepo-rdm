from .models import model_with_top_level_field
import json

def test_extra_top_level_field() -> None:
    mapping_key = "mappings/os-v2/model_with_top_level_field/metadata-v1.0.0.json"
    mapping_content = json.loads(model_with_top_level_field.__files__[mapping_key])
    content = mapping_content["mappings"]["properties"]
    assert "original_record" in content
    assert "metadata" in content
    assert "created" in content
    assert "pids" in content
    assert "parent" in content
