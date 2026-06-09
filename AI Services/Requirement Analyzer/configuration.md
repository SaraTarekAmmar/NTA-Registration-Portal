# Requirement Analyzer Configuration

## Implementation
- **Location**: `AI Services/Requirement Analyzer/analyzer.py`
- **Engine**: vLLM (Local server)

## Setup
1. **Server**: Ensure the vLLM server is running at the address specified in `VLLM_BASE_URL`.
2. **Model**: The service uses `google/gemma-4-31B-it` by default.
3. **Database**: Requires connection to the `nta_portal` MySQL database to fetch course materials and trainee profiles.

## Environment Variables
Required in the `.env` file:
```bash
VLLM_BASE_URL=http://localhost:7834
VLLM_MODEL=google/gemma-4-31B-it
```

## How it works
1.  **Extraction**: The service reads `.txt` files from `data/courses/`.
2.  **Analysis**: Two sequential LLM calls (Step 1: JSON, Step 2: Arabic Summary).
3.  **Storage**: Results are saved to the `cv_matching_results` table.
