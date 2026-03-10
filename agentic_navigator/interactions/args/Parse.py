"""Parse CLI args interaction."""

import argparse
import os


class ParseArgs:
    @staticmethod
    def execute(argv=None):
        parser = argparse.ArgumentParser(description="SMOL claw")
        parser.add_argument("--url", default="https://www.google.com")
        parser.add_argument("--prompt", default=None)
        parser.add_argument("--output", default=os.path.join("data", "output.json"))
        parser.add_argument("--model-type", default="LiteLLMModel")
        parser.add_argument("--model-id", default="gpt-4o")
        return parser.parse_args(argv)
