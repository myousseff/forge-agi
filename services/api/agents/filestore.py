import os
import uuid
from pathlib import Path
from services.contracts.models import FileInfo

class LocalFileStore:
    def __init__(self, root: str = "work/uploads"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, file: bytes, mime: str) -> FileInfo:
        file_id = str(uuid.uuid4())
        ext = mime.split('/')[-1]
        filename = f"{file_id}.{ext}"
        path = self.root / filename
        with open(path, "wb") as f:
            f.write(file)
        url = f"/uploads/{filename}"
        return FileInfo(file_id=file_id, url=url, mime=mime, size=len(file))
