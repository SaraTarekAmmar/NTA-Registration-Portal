# Chat Assistant Configuration

## Backend Implementation
- **File Path**: `admin/backend/core/chat_engine.py`
- **Class**: `ChatEngine`

## Configuration Steps
1. **API Key**: Set the `LLM_API_KEY` environment variable in the `.env` file.
2. **Provider**: The current implementation is designed to be provider-agnostic (supports OpenAI, Gemini, etc., via HTTP calls).
3. **Persona Management**: System prompts are defined in the `self.system_prompts` dictionary within `chat_engine.py`.

## Environment Variables
```bash
LLM_API_KEY=your_api_key_here
```
