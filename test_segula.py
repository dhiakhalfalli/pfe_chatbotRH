import sys
import os
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

# Mock settings if needed or just use them
from backend.config.settings import settings
from backend.agents.segula_agent import segula_agent

async def test():
    print("Testing segula_agent.answer_general...")
    result = segula_agent.answer_general("What are the benefits?")
    print("\nRESULT:")
    print(result.get("response", "NO RESPONSE"))

if __name__ == "__main__":
    asyncio.run(test())
