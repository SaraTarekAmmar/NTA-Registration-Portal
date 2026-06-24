import os
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

# Base directory for uploads relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip', '.rar'}
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'application/zip',
    'application/x-rar-compressed',
    'application/x-zip-compressed',
}

# Mapping of categories to subfolders
CATEGORY_MAP = {
    "trainee_id": "temp",
    "trainee_doc": "temp",
    "course_image": "courses/images",
    "course_material": "courses/materials",
    "admin_photo": "admins/photos",
    "trainer_id": "temp",
    "trainer_doc": "temp",
    "trainer_photo": "temp",
    "review_attachment": "admission",
    "temp": "temp"
}

# Magic-byte signatures for allowed file types.
# Checked against the first 8 bytes of the actual file — not the client-supplied MIME type.
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF", "application/pdf"),
    (b"\xd0\xcf\x11\xe0", "application/msword"),           # .doc (OLE compound)
    (b"PK\x03\x04", "application/zip"),                    # .docx / .xlsx / .zip (ZIP-based)
    (b"\xff\xd8\xff", "image/jpeg"),                       # JPEG
    (b"\x89PNG\r\n\x1a\n", "image/png"),                  # PNG
    (b"Rar!\x1a\x07", "application/x-rar-compressed"),    # RAR
]


def _check_magic_bytes(header: bytes) -> bool:
    """Return True if the file header matches at least one known allowed signature."""
    for sig, _ in _MAGIC_SIGNATURES:
        if header.startswith(sig):
            return True
    return False


async def save_upload_file(file: UploadFile, category: str = "temp", identifier: str = "admin") -> str:
    """
    Saves an uploaded file to the server and returns the relative path.
    Validates both file extension AND actual magic bytes (not just client MIME type).
    """
    file_extension = Path(file.filename).suffix.lower() if file.filename else ""

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '{file_extension}' not allowed.")

    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(status_code=400, detail=f"MIME type '{file.content_type}' not allowed.")

    # Read and validate magic bytes — defence against MIME spoofing
    header = await file.read(8)
    if not _check_magic_bytes(header):
        raise HTTPException(status_code=400, detail="محتوى الملف لا يطابق نوعه. الرجاء رفع ملف صحيح.")
    # Rewind so the full content is written below
    await file.seek(0)

    # Determine target directory based on category
    subfolder = CATEGORY_MAP.get(category, "temp")
    target_dir = UPLOAD_DIR / subfolder
    os.makedirs(target_dir, exist_ok=True)

    # Generate a descriptive filename: {category}_{identifier}_{timestamp}{ext}
    import time
    import re
    timestamp = int(time.time())
    clean_original = re.sub(r'[^a-zA-Z0-9_]', '', Path(file.filename).stem) if file.filename else "file"

    # For course materials, keep it minimal since it's already in a course folder
    if category == "course_material":
        unique_filename = f"{timestamp}_{clean_original}{file_extension}"
    else:
        unique_filename = f"{category}_{identifier}_{timestamp}_{clean_original}{file_extension}"

    file_path = target_dir / unique_filename

    # Save the file
    MAX_FILE_SIZE = 20 * 1024 * 1024 # 20MB
    file_size = 0

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                buffer.close()
                os.remove(file_path)
                from fastapi import HTTPException
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 20MB.")
            buffer.write(chunk)

    # Return the relative path (e.g., 'data/reviews/...')
    relative_path = os.path.join("data", subfolder, unique_filename).replace("\\", "/")
    return relative_path

def _safe_resolve(rel_path: str) -> "Path | None":
    """Resolve a relative path and ensure it stays within UPLOAD_DIR."""
    try:
        full = (PROJECT_ROOT / rel_path.lstrip('/')).resolve()
        if UPLOAD_DIR.resolve() in full.parents or full.parent == UPLOAD_DIR.resolve():
            return full
    except Exception:
        pass
    return None

def move_user_files_to_user_folder(name: str, nid: str, role: str, file_paths: list) -> dict:
    """
    Moves a list of relative file paths to a user-centric folder: data/{role}/{name}_{nid}/
    Returns a mapping of {old_path: new_path}
    """
    import shutil
    name_slug = name.strip().replace(' ', '_')
    if not name_slug: name_slug = "user"

    role_folder = "trainees" if role == 'trainee' else "trainers"
    if role in ['admin', 'superadmin', 'editor']:
        role_folder = "admins"

    user_folder = UPLOAD_DIR / role_folder / f"{name_slug}_{nid}"
    os.makedirs(user_folder, exist_ok=True)

    path_map = {}
    for old_rel_path in file_paths:
        if not old_rel_path: continue

        # old_rel_path is like 'data/trainees/ids/...'
        old_full_path = _safe_resolve(old_rel_path)
        if old_full_path and old_full_path.exists() and old_full_path.is_file():
            filename = old_full_path.name
            new_full_path = user_folder / filename
            
            # Avoid moving if it's already there
            if old_full_path.resolve() != new_full_path.resolve():
                shutil.move(str(old_full_path), str(new_full_path))
            
            new_rel_path = os.path.join("data", role_folder, f"{name_slug}_{nid}", filename).replace("\\", "/")
            path_map[old_rel_path] = new_rel_path
            
    return path_map

def move_course_files_to_course_folder(course_id: int, title: str, file_paths: list) -> dict:
    """
    Moves a list of relative file paths to a course-centric folder: data/courses/{title_slug}_{course_id}/
    Returns a mapping of {old_path: new_path}
    """
    import shutil
    # Use the title directly for the folder name (replacing spaces with underscores)
    title_slug = title.strip().replace(' ', '_')
    if not title_slug:
        title_slug = f"course_{course_id}"
        
    course_folder = UPLOAD_DIR / "courses" / f"{title_slug}_{course_id}"
    os.makedirs(course_folder, exist_ok=True)
    
    path_map = {}
    for old_rel_path in file_paths:
        if not old_rel_path: continue

        old_full_path = _safe_resolve(old_rel_path)
        if old_full_path and old_full_path.exists() and old_full_path.is_file():
            filename = old_full_path.name
            new_full_path = course_folder / filename

            if old_full_path.resolve() != new_full_path.resolve():
                shutil.move(str(old_full_path), str(new_full_path))

            new_rel_path = os.path.join("data", "courses", f"{title_slug}_{course_id}", filename).replace("\\", "/")
            path_map[old_rel_path] = new_rel_path

    return path_map

def move_admission_file_to_folder(trainee_nid: str, admin_nid: str, file_paths: list) -> dict:
    """
    Moves a list of relative file paths to an admission-specific folder: data/admission/{trainee_nid}_{admin_nid}/
    Returns a mapping of {old_path: new_path}
    """
    import shutil

    admission_folder = UPLOAD_DIR / "admission" / f"{trainee_nid}_{admin_nid}"
    os.makedirs(admission_folder, exist_ok=True)

    path_map = {}
    for old_rel_path in file_paths:
        if not old_rel_path: continue

        old_full_path = _safe_resolve(old_rel_path)
        if old_full_path and old_full_path.exists() and old_full_path.is_file():
            filename = old_full_path.name
            new_full_path = admission_folder / filename

            if old_full_path.resolve() != new_full_path.resolve():
                shutil.move(str(old_full_path), str(new_full_path))

            new_rel_path = os.path.join("data", "admission", f"{trainee_nid}_{admin_nid}", filename).replace("\\", "/")
            path_map[old_rel_path] = new_rel_path

    return path_map

def delete_trainee_folder(name: str, nid: str):
    """
    Permanently deletes the trainee's data folder: data/trainees/{name}_{nid}/
    Used upon rejection to allow clean re-registration.
    """
    import shutil
    name_slug = name.strip().replace(' ', '_')
    if not name_slug: name_slug = "user"
    
    user_folder = UPLOAD_DIR / "trainees" / f"{name_slug}_{nid}"
    if user_folder.exists() and user_folder.is_dir():
        shutil.rmtree(user_folder)
        return True
    return False
