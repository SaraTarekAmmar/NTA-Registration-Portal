# AI Quiz Generator

## Service Name
AI Quiz Generation Service

## Output Sent from System (Input to LLM)
- **Document Content**: Extracted text or binary file (PDF/DOCX) containing course materials.
- **Parameters**: 
    - `num_questions`: Number of questions to generate.
    - `course_id`: Target course for the quiz.

## Input Taken from LLM (Output from LLM)
- **Quiz Data (JSON)**: A structured JSON object containing:
    - `questions`: List of question objects.
    - `options`: List of multiple-choice options per question.
    - `answer`: The correct option string.

## Currently Displayed
- **Admin/Trainer Dashboard**: Quiz Management page where generated questions are reviewed and saved to the database.
- **Trainee View**: Once approved, the quiz is displayed in the course curriculum for trainees to attempt.
