"""Los módulos abren Data/... con rutas relativas a la raíz del repo: los tests corren desde ahí aunque pytest se lance
desde otra carpeta."""
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
