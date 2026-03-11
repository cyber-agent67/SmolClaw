#!/usr/bin/env python3
"""Simple test to verify .env configuration."""

import os
import sys

# Read .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

print("\n" + "=" * 70)
print("  Testing .env Configuration")
print("=" * 70)

if not os.path.exists(env_path):
    print(f"\n✗ .env not found at: {env_path}")
    sys.exit(1)

print(f"\n✓ .env found at: {env_path}")

# Load variables
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Check HF token
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    print(f"\n✅ HF_TOKEN: Loaded")
    print(f"   Value: {hf_token[:10]}...{hf_token[-5:]}")
    print(f"   Length: {len(hf_token)} characters")
else:
    print(f"\n✗ HF_TOKEN: Not found")
    sys.exit(1)

# Check other config
print("\n" + "=" * 70)
print("  Configuration Summary")
print("=" * 70)

config_vars = [
    "HF_TOKEN",
    "HUGGINGFACE_TOKEN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GATEWAY_HOST",
    "GATEWAY_PORT",
]

for var in config_vars:
    value = os.getenv(var)
    if value:
        if "TOKEN" in var or "KEY" in var:
            print(f"✓ {var}: {value[:10]}...{value[-5:]}")
        else:
            print(f"✓ {var}: {value}")
    else:
        print(f"○ {var}: Not set")

print("\n" + "=" * 70)
print("  ✅ .env Configuration: VALID")
print("=" * 70)
print("\nYour HF token is securely stored and ready to use!")
print("\nNext steps:")
print("  1. Install: pip install -e .")
print("  2. Run: python3 tests/test_env.py")
print("  3. Start gateway: smolclaw gateway start")
print("  4. Connect TUI: smolclaw tui")
print("=" * 70 + "\n")
