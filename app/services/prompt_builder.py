from typing import List


class PromptBuilder:
    """
    Responsible for building prompts for the LLM.
    """

    SYSTEM_PROMPT = """
You are an AI Knowledge Assistant.

Your job is to answer ONLY using the provided context.
If the answer is not present, say you don't know.
Never hallucinate

Rules:
1. Use only the provided context.
2. If the answer is not available, reply:
   "I couldn't find enough information in the provided documents."
3. Never hallucinate.
4. Keep answers clear and professional.
5. Format answers using Markdown.
"""

    @staticmethod
    def build(
        question: str,
        chunks: List[str],
        history: List[str] | None = None,
    ) -> str:

        context = "\n\n".join(chunks)

        chat_history = ""
        if history:
            chat_history = "\n".join(history)

        prompt = f"""
{PromptBuilder.SYSTEM_PROMPT}

=========================
CONTEXT
=========================

{context}

=========================
CHAT HISTORY
=========================

{chat_history}

=========================
USER QUESTION
=========================

{question}

=========================
ANSWER
=========================
"""

        return prompt