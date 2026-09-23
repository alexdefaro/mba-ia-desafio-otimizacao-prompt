"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        assert prompt.get("system_prompt", "").strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        text = prompt["system_prompt"].lower()
        assert any(role in text for role in ("você é", "voce e", "product manager", "analista"))

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        text = prompt["system_prompt"].lower()
        assert "markdown" in text or "user story" in text

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        text = prompt["system_prompt"].lower()
        assert "exemplo" in text
        assert text.count("entrada") >= 2
        assert text.count("saída") >= 2 or text.count("saida") >= 2

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        assert "[TODO]" not in yaml.safe_dump(prompt, allow_unicode=True)

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = load_prompts(str(PROMPT_PATH))["bug_to_user_story_v2"]
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors
        assert len(prompt["techniques_applied"]) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])