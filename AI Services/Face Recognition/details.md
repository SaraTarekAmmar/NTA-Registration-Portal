# Face Recognition Service

## Service Name
AI Face Enrollment & Verification Service

## Output Sent from System (Input to LLM)
- **Image Data**: Base64 encoded image of the trainee.
- **Label**: (For enrollment) Trainee's name or National ID.

## Input Taken from LLM (Output from LLM)
- **Enrollment Result**: Success/Failure status.
- **Verification Result**: Confidence score and predicted label (National ID).

## Currently Displayed
- **Attendance Check-in**: Used at the physical entrance or virtual session start to verify identity.
- **Admin Attendance Logs**: Shows the captured photo and matching score for each attendance record.
