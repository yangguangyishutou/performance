from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.shared_params.response_format_json_schema import JSONSchema
from dataclasses import dataclass, field
from typing import List, Dict, Iterable, Any, Sequence, Union
import os
import random
import sys
import asyncio
import logging
from itertools import islice

current_path = str(os.path.dirname(os.path.dirname(__file__)))
if current_path not in sys.path:
    sys.path.append(current_path)

try:
    from utils.api import llm_api
except ImportError:
    print("缺少api.py文件，请先配置api")
    exit(1)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class GeneratorConfig:
    """Configuration for LLM Generator."""
    max_concurrent_tasks: int = 30
    initial_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    retry_multiplier: float = 2.0
    max_retries: int = 5

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'GeneratorConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config.items() if k in cls.__dataclass_fields__})


PromptType = Union[str, Sequence[ChatCompletionMessageParam]]
PromptsType = Union[PromptType, Sequence[PromptType], None]
JSONSchemaInput = Union[JSONSchema, Sequence[JSONSchema | None], None]


class Generator:
    """Asynchronous LLM text generator with batching and retry capabilities."""

    _default_config = GeneratorConfig()

    def __init__(
        self,
        ai_name: str,
        test_mode: bool = False,
        config: GeneratorConfig | None = None
    ) -> None:
        """Initialize Generator with LLM configuration.

        Args:
            ai_name: Name of the AI model to use
            test_mode: If True, returns mock responses instead of calling LLM
            config: Generator configuration options
        """
        if ai_name not in llm_api:
            available = ', '.join(llm_api.keys())
            raise ValueError(f"Invalid model name: {ai_name}. Available: {available}")

        api = llm_api[ai_name]
        self.client = AsyncOpenAI(api_key=api['api_key'], base_url=api['base_url'])
        self.model_name = api['model_name']
        self.test_mode = test_mode
        self.config = config or self._default_config

        self._prompts: List[PromptType] = []

    def add_prompt(self, prompt: PromptType) -> None:
        """Add a prompt to the internal queue.

        Args:
            prompt: A single prompt (string or message sequence)
        """
        self._prompts.append(prompt)

    def _normalize_messages(
        self,
        prompt: PromptType
    ) -> Sequence[ChatCompletionMessageParam]:
        """Convert prompt to standardized message format.

        Args:
            prompt: String prompt or message sequence

        Returns:
            Sequence of ChatCompletionMessageParam
        """
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]  # type: ignore
        return prompt

    async def _generate_single(
        self,
        prompt: PromptType,
        json_schema: JSONSchema | None = None
    ) -> str:
        """Generate response for a single prompt with retry logic.

        Args:
            prompt: The prompt to generate from
            json_schema: Optional JSON schema for structured output

        Returns:
            Generated text response
        """
        if self.test_mode:
            delay = random.uniform(0.1, 0.5)
            await asyncio.sleep(delay)
            return """
<test result>
this is a test output.
```cpp
// this is a test code block
```
```java
// this is another test code block
```"""
        messages = self._normalize_messages(prompt)
        wait_time = self.config.initial_retry_delay

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.chat.completions.create( # type: ignore
                    model=self.model_name,
                    messages=messages,
                    response_format=( # type: ignore
                        {"type": "json_schema", "json_schema": json_schema}
                        if json_schema else None
                    ),
                    stream=True,
                )

                result = ''
                async for chunk in response:
                    if chunk.choices:
                        result += chunk.choices[0].delta.content or ''
                return result

            except Exception as e:
                prompt_preview = str(prompt)[:100] + '...' if len(str(prompt)) > 100 else str(prompt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} failed for prompt '{prompt_preview}': {e}"
                )

                if attempt < self.config.max_retries - 1:
                    actual_delay = min(wait_time, self.config.max_retry_delay)
                    logger.info(f"Retrying in {actual_delay:.1f} seconds...")
                    await asyncio.sleep(actual_delay)
                    wait_time *= self.config.retry_multiplier
                else:
                    logger.error(f"Max retries exceeded for prompt: {prompt_preview}")
                    raise
        return ""  # Should never reach here
    async def _generate_batch(
        self,
        prompts: Sequence[PromptType],
        json_schemas: Sequence[JSONSchema | None] | None = None
    ) -> List[str]:
        """Generate responses for a batch of prompts concurrently.

        Args:
            prompts: Sequence of prompts to process
            json_schemas: Optional sequence of JSON schemas (one per prompt),
                         or a single schema to apply to all prompts

        Returns:
            List of generated responses
        """
        if not prompts:
            return []

        # Normalize json_schemas to a sequence
        if json_schemas is None:
            json_schemas = [None] * len(prompts)
        elif self._is_single_schema(json_schemas):
            # Single JSONSchema object - apply to all prompts
            json_schemas = [json_schemas] * len(prompts)  # type: ignore

        # Validate lengths match
        if len(json_schemas) != len(prompts):  # type: ignore
            raise ValueError(
                f"Number of JSON schemas ({len(json_schemas)}) must match "  # type: ignore
                f"number of prompts ({len(prompts)})"
            )

        # Create tasks with paired prompts and schemas
        tasks = [
            self._generate_single(prompt, schema)
            for prompt, schema in zip(prompts, json_schemas)  # type: ignore
        ]

        results = await tqdm_asyncio.gather(*tasks)
        return results

    def _is_single_schema(self, json_schemas: Any) -> bool:
        """Check if json_schemas is a single schema object (not a sequence).

        Args:
            json_schemas: Object to check

        Returns:
            True if it appears to be a single JSONSchema dict
        """
        # Check if it's a dict with JSONSchema-like structure
        if isinstance(json_schemas, dict):
            return True
        return False

    def _normalize_prompts(
        self,
        prompts: PromptsType
    ) -> Sequence[PromptType]:
        """Normalize various prompt input formats to a sequence.

        Args:
            prompts: Input in various formats (None, single, or sequence)

        Returns:
            Sequence of normalized prompts
        """
        if prompts is None:
            prompts = self._prompts
            self._prompts = []
        elif not prompts:
            return []

        # Handle single prompt (string or message list)
        if isinstance(prompts, str):
            return [prompts]

        # Check if it's already a sequence of message lists or strings
        try:
            first_item = list(islice(prompts, 1))[0]  # type: ignore
            # If first item is a dict (message), wrap the whole thing
            if isinstance(first_item, dict):
                return [prompts]  # type: ignore
        except (StopIteration, TypeError):
            pass

        return prompts  # type: ignore

    def generate(
        self,
        prompts: PromptsType = None,
        json_schema: JSONSchemaInput = None
    ) -> List[str]:
        """Generate responses for prompts with batching.

        This method runs the async generation in an event loop and handles
        batching of large numbers of prompts to avoid overwhelming the API.

        Args:
            prompts: Prompts to generate from (uses internal queue if None)
            json_schema: JSON schema configuration. Can be:
                - None: no schema for any prompt
                - Single JSONSchema: apply to all prompts
                - Sequence of JSONSchema/None: one schema per prompt

        Returns:
            List of generated responses

        Examples:
            >>> # No schema
            >>> gen.generate(["Hello", "World"])

            >>> # Same schema for all prompts
            >>> schema = JSONSchema(name="output", strict=True)
            >>> gen.generate(["Hello", "World"], json_schema=schema)

            >>> # Different schema per prompt
            >>> schemas = [schema1, schema2, None]
            >>> gen.generate(["p1", "p2", "p3"], json_schema=schemas)
        """
        normalized_prompts = self._normalize_prompts(prompts)

        if not normalized_prompts:
            return []

        # Convert to list for iteration
        prompt_list = list(normalized_prompts)
        all_results = []

        # Normalize json_schemas to match prompt_list length
        json_schemas = self._normalize_json_schemas(json_schema, len(prompt_list))

        # Process in batches to avoid overwhelming the API
        batch_size = self.config.max_concurrent_tasks
        total_batches = (len(prompt_list) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(prompt_list)} prompts in {total_batches} batches")

        for i in range(0, len(prompt_list), batch_size):
            batch = prompt_list[i:i + batch_size]
            batch_schemas = json_schemas[i:i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} prompts)")

            batch_results = asyncio.run(self._generate_batch(batch, batch_schemas))
            all_results.extend(batch_results)

        logger.info(f"Completed processing {len(all_results)} prompts")
        return all_results

    def _normalize_json_schemas(
        self,
        json_schema: JSONSchemaInput,
        num_prompts: int
    ) -> Sequence[JSONSchema | None]:
        """Normalize JSON schema input to a sequence of schemas.

        Args:
            json_schema: Input in various formats
            num_prompts: Number of prompts to match

        Returns:
            Sequence of JSONSchema/None matching num_prompts length
        """
        if json_schema is None:
            return [None] * num_prompts

        # Check if it's a single JSONSchema object (not a sequence)
        if self._is_single_schema(json_schema):
            return [json_schema] * num_prompts  # type: ignore

        # It's already a sequence
        schema_list = list(json_schema)  # type: ignore

        if len(schema_list) != num_prompts:
            raise ValueError(
                f"Number of JSON schemas ({len(schema_list)}) must match "
                f"number of prompts ({num_prompts})"
            )

        return schema_list


# Default generator instance for backward compatibility
default_generator = Generator('deepseek')


def _run_tests() -> None:
    """Run test cases to verify Generator functionality."""
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)

    test_generator = Generator('qwen', test_mode=True)

    # Test 1: Single string prompt
    print("=== Test 1: Single String Prompt ===")
    test1 = "Who are you?"
    result1 = test_generator.generate(test1)
    print(f"Result: {result1[0][:50]}...")

    # Test 2: Single message sequence
    print("\n=== Test 2: Single Message Sequence ===")
    test2 = [
        {"role": "user", "content": "Who are you?"},
        {"role": "assistant", "content": "I am a chatbot."},
        {"role": "user", "content": "What is your name?"},
    ]
    result2 = test_generator.generate(test2)
    print(f"Result: {result2[0][:50]}...")

    # Test 3: Multiple string prompts
    print("\n=== Test 3: Multiple String Prompts ===")
    test3 = [
        "Who are you?",
        "What can you do?"
    ]
    result3 = test_generator.generate(test3)
    print(f"Results: {len(result3)} responses")

    # Test 4: Multiple message sequences
    print("\n=== Test 4: Multiple Message Sequences ===")
    test4 = [
        [
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am a chatbot."},
            {"role": "user", "content": "What is your name?"},
        ],
        [
            {"role": "user", "content": "What can you do?"}
        ]
    ]
    result4 = test_generator.generate(test4)
    print(f"Results: {len(result4)} responses")

    # Test 5: Using add_prompt
    print("\n=== Test 5: Using add_prompt ===")
    test_generator.add_prompt("Test prompt 1")
    test_generator.add_prompt("Test prompt 2")
    result5 = test_generator.generate()
    print(f"Results: {len(result5)} responses")

    # Test 6: Different JSON schemas per prompt
    print("\n=== Test 6: Different JSON Schemas Per Prompt ===")
    from openai.types.shared_params import FunctionDefinition

    # Create different schemas
    schema1 = JSONSchema(
        name="person",
        strict=True,
        schema=FunctionDefinition(
            name="person",
            strict=True,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"],
                "additionalProperties": False
            }
        )
    )

    schema2 = JSONSchema(
        name="location",
        strict=True,
        schema=FunctionDefinition(
            name="location",
            strict=True,
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "country": {"type": "string"}
                },
                "required": ["city", "country"],
                "additionalProperties": False
            }
        )
    )

    test6 = [
        f"Extract person info from: John is 25 years old",
        f"Extract location from: Paris, France",
        f"This one has no schema requirement"
    ]

    result6 = test_generator.generate(test6, json_schema=[schema1, schema2, None])
    print(f"Results: {len(result6)} responses")
    print("  - Prompt 1 uses person schema")
    print("  - Prompt 2 uses location schema")
    print("  - Prompt 3 has no schema")

    # Test 7: Same schema for all prompts
    print("\n=== Test 7: Same Schema for All Prompts ===")
    test7 = [
        "Extract person from: Alice is 30",
        "Extract person from: Bob is 35"
    ]
    result7 = test_generator.generate(test7, json_schema=schema1)
    print(f"Results: {len(result7)} responses (all with person schema)")

    print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    _run_tests()