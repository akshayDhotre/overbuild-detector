import asyncio

from overbuild.cli import _run_demos


def main() -> None:
    asyncio.run(_run_demos(json_output=False))


if __name__ == "__main__":
    main()
