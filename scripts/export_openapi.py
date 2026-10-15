"""Generate the API contract without loading user configuration or data."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from specbridge.main import create_app


def main() -> None:
    with TemporaryDirectory() as directory:
        app = create_app(
            data_dir=Path(directory),
            token="contract-generation-only",
            allowed_origin="http://127.0.0.1:5173",
        )
        output = ROOT / "packages/contracts/openapi.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
