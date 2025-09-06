import os
from openai import OpenAI
from anthropic import Anthropic

class LLMAdapter:
    def complete(self, messages: list[dict]) -> str:
        raise NotImplementedError


# =====================
# 🚀 OpenAI Adapter
# =====================
class OpenAIAdapter(LLMAdapter):
    def __init__(self, model=None, api_key=None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, messages: list[dict]) -> str:
        # messages = [{"role":"system/user/assistant","content":"..."}]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6,
        )
        return resp.choices[0].message.content


# =====================
# 🤖 Claude Adapter
# =====================
class ClaudeAdapter(LLMAdapter):
    def __init__(self, model=None, api_key=None):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

    def complete(self, messages: list[dict]) -> str:
        """
        Claude usa otra estructura: `system`, `user`, `assistant`.
        Convierte messages estilo OpenAI a lo que espera Anthropic.
        """
        system_prompt = None
        new_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                new_messages.append({
                    "role": m["role"],
                    "content": m["content"],
                })

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            temperature=0.6,
            system=system_prompt,
            messages=new_messages
        )

        # Claude devuelve lista de bloques de contenido
        if resp.content and len(resp.content) > 0:
            return resp.content[0].text
        return ""

# =====================
# ⚡ Groq Adapter
# =====================
class GroqAdapter(LLMAdapter):
    def __init__(self, model=None, api_key=None):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key or os.getenv("GROQ_API_KEY")
        )
        # Por defecto usamos un modelo rápido de Groq
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    def complete(self, messages: list[dict]) -> str:
        """
        Funciona casi igual que OpenAI, porque Groq imita la API.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return resp.choices[0].message.content