import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SpecBridge on this computer")
    parser.add_argument("--host", choices=["127.0.0.1", "::1"], default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(
        "specbridge.main:create_default_app",
        factory=True,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
