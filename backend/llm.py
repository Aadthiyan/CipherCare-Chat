import os
import logging
import json
import re
import time
from typing import Optional
from groq import Groq
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError
from backend.exceptions import (
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    ServiceInitializationError
)

logger = logging.getLogger(__name__)

class SafetyGuardrails:
    """Task 4.4: Safety Filters & Post-processing"""
    FORBIDDEN_PATTERNS = [
        r"(?i)stop taking.*medication",
        r"(?i)immediately inject",
        r"(?i)ignore.*symptoms",
        r"(?i)kill",
        r"(?i)suicide"
    ]
    
    PHI_REGEX = [
        r"\b\d{3}-\d{2}-\d{4}\b", # SSN
        r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b" # Phone
    ]

    @staticmethod
    def validate_response(text: str) -> str:
        # 1. Check for Harmful Instructions
        for pattern in SafetyGuardrails.FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Safety Filter Triggered: Detected unsafe pattern '{pattern}'")
                return "[SAFETY REDACTION] The generated response contained potentially unsafe medical advice. Please consult the raw clinical records directly."
        
        # 2. PHI Scrubbing (Post-generation check)
        for pattern in SafetyGuardrails.PHI_REGEX:
            text = re.sub(pattern, "[REDACTED PHI]", text)
            
        # 3. Mandatory Disclaimer Append (if missing)
        disclaimer = "\n\nDISCLAIMER: Clinical decision support only. Not a medical order."
        if "DISCLAIMER" not in text:
            text += disclaimer
            
        return text

class LocalLLMClient:
    """Client for Self-Hosted Inference Server (vLLM / Text-Gen-WebUI)"""
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        logger.info(f"Initialized Private LLM Client at {self.base_url}")
        
        # Test connectivity
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            logger.debug(f"Local LLM health check passed: {self.base_url}")
        except Exception as e:
            logger.warning(f"Local LLM health check failed: {str(e)[:80]}")

    def generate(self, system_prompt, user_content, timeout=30) -> str:
        """Generate response from local LLM"""
        # Standard OpenAI-compatible format (used by vLLM, LM Studio, etc.)
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7,
            "max_tokens": 512,
            "stop": ["---", "CLINICAL QUESTION:"]
        }
        
        try:
            url = f"{self.base_url}/v1/chat/completions"
            resp = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=timeout
            )
            
            if resp.status_code == 429:
                raise LLMRateLimitError(
                    provider="local",
                    retry_after=int(resp.headers.get("Retry-After", 60))
                )
            
            resp.raise_for_status()
            
            if not resp.text:
                raise LLMError("Empty response from local LLM", provider="local")
            
            return resp.json()['choices'][0]['message']['content']
            
        except Timeout:
            raise LLMTimeoutError(timeout, provider="local")
        except RequestsConnectionError as e:
            raise LLMError(
                f"Connection failed to {self.base_url}: {str(e)[:80]}",
                provider="local",
                details={"url": self.base_url}
            )
        except Exception as e:
            if "401" in str(e):
                raise LLMError("Authentication failed", provider="local")
            raise LLMError(str(e), provider="local")

class GroqLLMClient:
    """Client for Groq Cloud Inference with better error handling"""
    def __init__(self, api_key, model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=1024):
        if not api_key:
            raise ServiceInitializationError(
                "Groq LLM",
                "Missing API key",
                details={"env_var": "GROQ_API_KEY"}
            )
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            self.client = Groq(api_key=api_key)
            logger.info(f"Groq LLM client initialized: {model}, temp={temperature}, max_tokens={max_tokens}")
        except Exception as e:
            raise ServiceInitializationError(
                "Groq LLM",
                f"Failed to initialize Groq client: {str(e)[:80]}",
                details={"error_type": type(e).__name__}
            )

    def generate(self, system_prompt, user_content, timeout=30) -> str:
        """Generate response from Groq with comprehensive error handling"""
        if not system_prompt or not user_content:
            raise LLMError(
                "System prompt and user content are required",
                provider="groq"
            )
        
        try:
            chat = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=timeout
            )
            
            if not chat.choices or len(chat.choices) == 0:
                raise LLMError("No response choices from Groq API", provider="groq")
            
            content = chat.choices[0].message.content
            if not content:
                raise LLMError("Empty response content from Groq", provider="groq")
            
            return content
            
        except Timeout:
            raise LLMTimeoutError(timeout, provider="groq")
        except Exception as e:
            error_str = str(e)
            
            # Handle specific error types
            if "401" in error_str or "unauthorized" in error_str.lower():
                raise LLMError("Groq API authentication failed - invalid key", provider="groq")
            elif "429" in error_str or "rate limit" in error_str.lower():
                raise LLMRateLimitError(provider="groq", retry_after=60)
            elif "timeout" in error_str.lower():
                raise LLMTimeoutError(timeout, provider="groq")
            elif "connection" in error_str.lower():
                raise LLMError(f"Connection error: {error_str[:80]}", provider="groq")
            else:
                raise LLMError(error_str[:200], provider="groq", details={"error_type": type(e).__name__})

class LLMService:
    def __init__(self):
        # Configuration from environment
        self.provider = os.getenv("LLM_PROVIDER", "groq").lower()  # 'groq' or 'local'
        self.answer_generation_enabled = os.getenv("LLM_ANSWER_GENERATION_ENABLED", "true").lower() == "true"
        
        # Groq Setup
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
        
        # Local Setup
        self.local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:8000")
        
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        if not self.answer_generation_enabled:
            logger.info("LLM answer generation is disabled")
            return
            
        try:
            if self.provider == "local":
                self.client = LocalLLMClient(self.local_url)
            elif self.provider == "groq":
                if not self.groq_api_key:
                    logger.warning("GROQ_API_KEY missing - LLM will not be available")
                else:
                    self.client = GroqLLMClient(
                        self.groq_api_key, 
                        model=self.groq_model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
            else:
                logger.error(f"Unknown LLM Provider: {self.provider}")
        except ServiceInitializationError as e:
            logger.error(f"LLM initialization failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error initializing LLM: {str(e)[:100]}")

    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer with comprehensive error handling and fallbacks"""
        if not self.answer_generation_enabled:
            return "LLM answer generation is currently disabled. Please review the source documents directly."
            
        if not self.client:
            return f"LLM Service Unavailable (Provider: {self.provider}). Please check configuration and logs."
        
        if not query or len(query) < 2:
            return "Invalid query - please provide a meaningful clinical question."
        
        if not context or len(context) < 20:
            return "Insufficient context provided. No relevant patient records found."

        system_prompt = (
            "You are a helpful and accurate clinical decision support assistant. "
            "Use the provided Patient Context and Medical Records to answer the Clinical Question. "
            "If the answer is not in the context, state that explicitly. "
            "Do not hallucinate medical facts. "
            "Format your response professionally."
        )
        user_content = f"Context:\n{context}\n\nClinical Question: {query}"

        try:
            # 1. Generate with timeout protection
            raw_response = self.client.generate(system_prompt, user_content, timeout=30)
            
            if not raw_response or len(raw_response) < 5:
                raise LLMError("LLM returned empty or invalid response", provider=self.provider)
            
            # 2. Safety Post-Processing
            safe_response = SafetyGuardrails.validate_response(raw_response)
            
            return safe_response

        except LLMTimeoutError:
            logger.warning(f"LLM request timed out after 30s")
            return "The clinical analysis took too long to generate. Please try a simpler query or review the source documents."
        except LLMRateLimitError as e:
            logger.warning(f"LLM rate limit exceeded: {e.message}")
            return "Service temporarily overloaded. Please retry in a few moments."
        except LLMError as e:
            logger.error(f"LLM generation error: {e.message}")
            return f"Error generating analysis: {e.message[:100]}. Please review the source documents manually."
        except Exception as e:
            logger.error(f"Unexpected LLM error: {str(e)[:100]}")
            return "Unexpected error generating response. Please review the source documents manually."
