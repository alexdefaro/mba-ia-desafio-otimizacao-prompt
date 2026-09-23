"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        system_prompt = prompt_data["system_prompt"]
        user_prompt = prompt_data.get("user_prompt", "{bug_report}")
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])
        techniques = prompt_data.get("techniques_applied", [])
        description = prompt_data.get(
            "description",
            "Optimized bug-to-user-story prompt.",
        )
        description = f"{description} Techniques: {', '.join(techniques)}"
        tags = list(prompt_data.get("tags", []))
        tags.extend(technique.lower().replace(" ", "-") for technique in techniques)
        tags = list(dict.fromkeys(tags))

        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
        print(f"✓ Prompt publicado: {prompt_name}")
        print(f"  URL: {url}")
        return True
    except Exception as error:
        print(f"❌ Erro ao publicar o prompt: {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []
    required_fields = ["description", "system_prompt", "version", "techniques_applied"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    if not str(prompt_data.get("system_prompt", "")).strip():
        errors.append("system_prompt está vazio")
    if "{bug_report}" not in str(prompt_data.get("system_prompt", "")) + str(
        prompt_data.get("user_prompt", "")
    ):
        errors.append("O prompt precisa usar a variável {bug_report}")
    if len(prompt_data.get("techniques_applied", [])) < 2:
        errors.append("Mínimo de 2 técnicas requeridas")
    if "[TODO]" in str(prompt_data):
        errors.append("O prompt ainda contém [TODO]")
    return len(errors) == 0, errors


def main():
    """Função principal"""
    print_section_header("PUSH DO PROMPT OTIMIZADO")
    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"
    prompt_document = load_yaml(str(prompt_path))
    if not prompt_document or "bug_to_user_story_v2" not in prompt_document:
        print(f"❌ Prompt inválido ou não encontrado: {prompt_path}")
        return 1

    prompt_data = prompt_document["bug_to_user_story_v2"]
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Validação do prompt falhou:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/bug_to_user_story_v2"
    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
