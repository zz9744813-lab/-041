from typing import Optional
import os
from fastapi.templating import Jinja2Templates

templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)