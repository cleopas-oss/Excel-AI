import asyncio
import os
from typing import Tuple


class LLMClient:

    def __init__(self):
        self.token = os.getenv("HF_TOKEN")

        if not self.token:
            raise ValueError("HF_TOKEN environment variable not set.")

        self.model = os.getenv(
            "HF_MODEL",
            "meta-llama/Llama-3.1-8B-Instruct:novita"
        )

        self.client = None

    async def initialize(self) -> bool:
        try:
            from huggingface_hub import InferenceClient

            self.client = await asyncio.to_thread(
                lambda: InferenceClient(api_key=self.token)
            )

            print(f"✓ Initialized HF client: {self.model}")
            return True

        except Exception as e:
            print(f"✗ LLM init failed: {e}")
            return False

    async def call_llm(self, prompt: str) -> Tuple[bool, str]:

        if not self.client:
            return False, "LLM not initialized"

        messages = [{"role": "user", "content": prompt}]

        for attempt in range(3):

            try:

                def hf_call():
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=512,
                        temperature=0.2,
                    )
                    return completion.choices[0].message.content

                result = await asyncio.to_thread(hf_call)

                return True, result

            except Exception as e:

                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue

                return False, str(e)

        return False, "Max retries exceeded"

    async def close(self):
        self.client = None
