import shutil
from pathlib import Path
from datetime import datetime

NOVELS_DIR = Path(__file__).parent.parent.parent / "novels"


def _ensure_chapter_dir(project_id: str, chapter_id: str) -> Path:
    """Ensure the chapter's directory exists and return the file path."""
    chapter_dir = NOVELS_DIR / project_id / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    return chapter_dir / f"{chapter_id}.md"


def _ensure_backup_dir(project_id: str, chapter_id: str) -> Path:
    """Ensure the backup directory exists and return it."""
    backup_dir = NOVELS_DIR / project_id / ".backups" / chapter_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


async def read_chapter(project_id: str, chapter_id: str) -> str:
    """Read chapter content from markdown file. Returns empty string if not found."""
    filepath = _ensure_chapter_dir(project_id, chapter_id)
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


async def write_chapter(project_id: str, chapter_id: str, content: str) -> None:
    """Write chapter content to markdown file."""
    filepath = _ensure_chapter_dir(project_id, chapter_id)
    filepath.write_text(content, encoding="utf-8")


async def backup_chapter(project_id: str, chapter_id: str) -> str:
    """Create a timestamped backup of the chapter file. Returns the backup path."""
    source = NOVELS_DIR / project_id / "chapters" / f"{chapter_id}.md"
    if not source.exists():
        return ""

    backup_dir = _ensure_backup_dir(project_id, chapter_id)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{timestamp}.md"
    shutil.copy2(str(source), str(backup_path))
    return str(backup_path)


async def delete_chapter_file(project_id: str, chapter_id: str) -> None:
    """Delete the chapter markdown file if it exists."""
    filepath = NOVELS_DIR / project_id / "chapters" / f"{chapter_id}.md"
    if filepath.exists():
        filepath.unlink()