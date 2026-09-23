"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """Pull the seed prompt and persist its messages as the local v1 YAML."""
    client = Client()
    prompt = client.pull_prompt(
        "leonanluppi/bug_to_user_story_v1",
        dangerously_pull_public_prompt=True,
    )

    messages = []
    for message in prompt.messages:
        message_prompt = getattr(message, "prompt", None)
        template = getattr(message_prompt, "template", None)
        if template is None:
            template = getattr(message, "template", None)
        if template is None:
            raise ValueError(f"Não foi possível extrair o template de {message!r}")

        class_name = type(message).__name__.lower()
        if "system" in class_name:
            role = "system"
        elif "human" in class_name:
            role = "user"
        elif "ai" in class_name:
            role = "assistant"
        else:
            role = getattr(message, "role", "user")
        messages.append({"role": role, "template": template})

    system_message = next(
        (message["template"] for message in messages if message["role"] == "system"),
        "",
    )
    user_message = next(
        (message["template"] for message in messages if message["role"] == "user"),
        "{bug_report}",
    )

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt pulled from the LangSmith Prompt Hub",
            "system_prompt": system_message,
            "user_prompt": user_message,
            "version": "v1",
            "created_at": "2025-01-15",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }
    output_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"
    if not save_yaml(prompt_data, str(output_path)):
        raise RuntimeError(f"Falha ao salvar {output_path}")
    return output_path


def main():
    """Função principal"""
    print_section_header("PULL DO PROMPT INICIAL")
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        output_path = pull_prompts_from_langsmith()
        print(f"✓ Prompt salvo em: {output_path}")
        return 0
    except Exception as error:
        print(f"❌ Falha ao fazer pull do prompt: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
