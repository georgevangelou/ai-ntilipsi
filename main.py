#!/usr/bin/env python3

import argparse
import asyncio

# Local component imports
from config_manager import DEFAULT_MODEL
from assistant import Assistant


def main():
    parser = argparse.ArgumentParser(description="Hardened Local Orchestration Environment Client.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Target processing model")
    args = parser.parse_args()

    asyncio.run(Assistant(args.model).run_async())

if __name__ == "__main__":
    main()
