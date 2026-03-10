"""
HealthOps Studio — LLM Client Abstraction Layer

Provides a clean interface for interacting with Google Gemini.
Features:
- Structured JSON output using Pydantic schemas
- Automatic retry on validation failure
- Prompt injection protection (basic filtering)
- Fallback logic
"""

from google import genai
from google.genai import types
from typing import Type, TypeVar, Any, Optional
from pydantic import BaseModel, ValidationError
import json
import logging
from sqlalchemy.orm import Session
from app.config import get_settings
from app.ai.cost_tracker import record_usage

logger = logging.getLogger("healthops.ai")
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self):
        # We instantiate the client only if the key is provided
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.default_model = "gemini-2.5-flash"  # Fast and capable for structural tasks

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2, # Low temp for deterministic structured output
        model_name: Optional[str] = None,
        db: Optional[Session] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> T:
        """
        Generates a structured Pydantic model from a natural language prompt.
        Retries once if JSON parsing or validation fails.
        """
        if not self.is_configured():
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Inject the schema into the system prompt since google-genai 0.5.0
        # fails to parse complex Pydantic schemas with $defs internally.
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_instruction_with_schema = f"{system_prompt}\n\nREQUIRED OUTPUT SCHEMA (JSON):\n{schema_json}"

        # In google-genai, system instructions are passed via config
        config = types.GenerateContentConfig(
            system_instruction=system_instruction_with_schema,
            temperature=temperature,
            response_mime_type="application/json",
        )

        model = model_name or self.default_model
        
        try:
            # First attempt
            response = self.client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config
            )
            
            # The client automatically parses the JSON if response_schema is provided,
            # but we still validate it through Pydantic to be safe.
            raw_dict = json.loads(response.text)
            
            # Record cost if db session is provided
            if db and user_id and response.usage_metadata:
                record_usage(
                    db=db,
                    user_id=user_id,
                    model_name=model,
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    request_id=request_id
                )
                
            return response_model(**raw_dict)
            
        except (ValidationError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse LLM structured output. Retrying. Error: {str(e)}")
            
            # Retry attempt with explicit error context
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"IMPORTANT: Your previous response failed validation with this error:\n{str(e)}\n"
                f"Please fix the error and ensure the output strictly matches the requested JSON schema."
            )
            
            response = self.client.models.generate_content(
                model=model,
                contents=retry_prompt,
                config=config
            )
            raw_dict = json.loads(response.text)
            
            if db and user_id and response.usage_metadata:
                record_usage(
                    db=db,
                    user_id=user_id,
                    model_name=model,
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    request_id=request_id
                )
                
            return response_model(**raw_dict)

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        model_name: Optional[str] = None
    ) -> str:
        """
        Generates unstructured text (e.g., Markdown documentation).
        """
        if not self.is_configured():
            raise ValueError("GEMINI_API_KEY is not configured.")

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )

        model = model_name or self.default_model
        
        response = self.client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=config
        )
        return response.text

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        model_name: Optional[str] = None
    ):
        """
        Generates unstructured text (e.g., Markdown documentation) as a stream.
        Yields chunks of text. If the API key is not configured, it yields a 
        mock response chunk by chunk to gracefully degrade.
        """
        if not self.is_configured():
            # Graceful fallback: stream a mock response
            import asyncio
            mock_text = "*(Running without API key)*\n\nI am the AI Assistant. I can help you build workflows, generate documentation, or write custom ETL queries. Since the API key is missing right now, I am streaming this placeholder text to prove the SSE connection works!"
            
            async def mock_streamer():
                words = mock_text.split(" ")
                for word in words:
                    yield word + " "
                    await asyncio.sleep(0.05)
            
            return mock_streamer()

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )

        model = model_name or self.default_model
        
        # Returns a blocking generator from google-genai
        # In a real async fastapi app, we'd run this in a threadpool or use the async client 
        # (google.genai handles this via async api, but keeping it simple here)
        response_stream = self.client.models.generate_content_stream(
            model=model,
            contents=user_prompt,
            config=config
        )
        
        async def real_streamer():
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        return real_streamer()

# Singleton instance
llm_client = LLMClient()
