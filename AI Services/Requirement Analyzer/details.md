# AI Requirement Analyzer

## Overview
This service analyzes a trainee's profile against the **actual technical content** found in course materials (syllabi). It generates the data for the "Course Requirements Analysis" radar chart and a professional summary for the "AI Notes" box.

## Input (System Output)
- **Course Metadata**: Title and Description.
- **Course Content**: Text extracted from session material files (PDF/TXT).
- **Trainee Data**: Technical skills, academic history, and professional summary.

## Output (LLM Input)
The system receives a two-stage response:
1.  **Quantitative Analysis**: A JSON object with 5 requirement dimensions and scores (0-100).
2.  **Qualitative Summary**: A 2-3 sentence professional assessment in Arabic.

## UI Display
- **Radar Chart**: Populates `apInteractChart` in the Admin Profile view.
- **AI Notes**: Populates the `ملاحظات الذكاء الاصطناعي` container.
