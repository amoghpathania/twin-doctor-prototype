class FakeLLMClient:
    """Deterministic LLMClient double for hermetic tests - no network calls."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[str] = []
        self.system_instructions: list[str] = []

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        self.system_instructions.append(system_instruction)
        self.calls.append(prompt)
        return self.response


class MemoryExtractionLLMClient(FakeLLMClient):
    """Deterministic double with independent assessment and memory-extraction responses."""

    def __init__(self, assessment_response: str, memory_response: str | Exception) -> None:
        super().__init__(assessment_response)
        self.memory_response = memory_response
        self.memory_calls: list[str] = []
        self.memory_system_instructions: list[str] = []

    def generate_memories(self, system_instruction: str, prompt: str) -> str:
        self.memory_system_instructions.append(system_instruction)
        self.memory_calls.append(prompt)
        if isinstance(self.memory_response, Exception):
            raise self.memory_response
        return self.memory_response


class ScriptedLLMClient:
    """Returns one scripted response per call, in order - for multi-case eval tests."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[str] = []
        self.system_instructions: list[str] = []

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        index = len(self.calls)
        self.system_instructions.append(system_instruction)
        self.calls.append(prompt)
        return self.responses[index]


class FailingLLMClient:
    """Raises on every call - simulates provider errors (quota/network/auth) for fail-safe tests."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or RuntimeError("simulated LLM provider failure")

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        raise self.error
