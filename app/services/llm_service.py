from groq import Groq

from app.core.config import settings
from app.core.logger import logger 


class LLMService:
    """
    Responsible only for communicating with the LLM.
    """

    def __init__(self):
        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = settings.groq_model
        self.temperature = settings.groq_temperature
        self.max_tokens = settings.groq_max_tokens

    async def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Send prompt to Groq and return generated response.
        """

        try:
            logger.info(f"Sending request to LLM with prompt: {prompt}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            logger.info(f"LLM Response: {response.choices[0].message.content}")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM Generation Failed: {e}")
            raise RuntimeError(f"LLM Generation Failed: {e}")

    def generate_stream(
        self,
        prompt: str,
    ):
        """
        Send prompt to Groq and yield the response token by token.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            for chunk in response:
                token = chunk.choices[0].delta.content
                if token:
                    yield token

        except Exception as e:
            logger.error(f"LLM Streaming Failed: {e}")
            raise RuntimeError(f"LLM Streaming Failed: {e}")


llm_service = LLMService()