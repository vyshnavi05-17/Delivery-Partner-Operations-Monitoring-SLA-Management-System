from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def load_main_app():
    existing = sys.modules.get("app")
    if existing is not None and hasattr(existing, "dashboard"):
        return existing
    root = Path(__file__).resolve().parent
    sys.modules.pop("app", None)
    package_dir = root / "app"
    package_spec = spec_from_file_location("app", package_dir / "__init__.py", submodule_search_locations=[str(package_dir)])
    package = module_from_spec(package_spec)
    sys.modules["app"] = package
    package_spec.loader.exec_module(package)
    module_spec = spec_from_file_location("app.app", package_dir / "app.py")
    module = module_from_spec(module_spec)
    sys.modules["app.app"] = module
    module_spec.loader.exec_module(module)
    return module
