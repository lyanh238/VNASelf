#!/usr/bin/env python3
"""
Test script for conflict detection and resolution system
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core import MultiAgentSystem

async def test_conflict_detection():
    """Test the conflict detection and resolution system."""
    print("=" * 60)
    print("Testing Conflict Detection and Resolution System")
    print("=" * 60)
    
    # Initialize the system
    system = MultiAgentSystem()
    await system.initialize()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Create event without conflict",
            "query": "Tạo cuộc họp 'Test Meeting' vào ngày mai lúc 9:00 AM đến 10:00 AM"
        },
        {
            "name": "Create event with potential conflict",
            "query": "Tạo cuộc họp 'Another Meeting' vào ngày mai lúc 9:30 AM đến 10:30 AM"
        },
        {
            "name": "Check calendar availability",
            "query": "Kiểm tra lịch trống ngày mai từ 8:00 AM đến 12:00 PM"
        },
        {
            "name": "View upcoming events",
            "query": "Xem các sự kiện sắp tới"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print("-" * 40)
        
        try:
            response = await system.process_message(test_case['query'])
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 40)
    
    # Cleanup
    await system.close()
    print("\nTest completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_conflict_detection())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
