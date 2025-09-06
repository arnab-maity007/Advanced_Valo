#!/usr/bin/env python3
"""
Test script for DualCast Commentary System
"""

import json
import time
import os
import sys

# Add the current directory to sys.path to import buycommentary
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from buycommentary import BuyPhaseCommentator, create_sample_events

def test_commentary_system():
    """Test the commentary system with sample events"""
    print("🧪 Testing DualCast Commentary System...")
    print("=" * 50)
    
    # Create sample events
    print("📝 Creating sample events...")
    create_sample_events()
    
    # Initialize commentator
    print("🎮 Initializing commentary system...")
    commentator = BuyPhaseCommentator()
    
    # Set shorter duration for testing
    commentator.phase_duration = 5  # 5 seconds
    commentator.commentary_interval = 1  # 1 second between commentary
    
    print("🎯 Starting test phase...")
    print("⏱️  Test Duration: 5 seconds")
    print("🎙️  Commentary Interval: 1 second")
    print("-" * 50)
    
    # Run a single buy phase test
    start_time = time.time()
    while time.time() - start_time < 8:  # Run for 8 seconds to see full cycle
        if not commentator.process_buy_phase():
            print("✅ Buy phase completed successfully!")
            break
        time.sleep(0.2)  # Check every 200ms
    
    # Get summary
    summary = commentator.get_commentary_summary()
    print("\n📊 Test Results:")
    print(f"   Events Processed: {summary['events_processed']}")
    print(f"   Commentary Lines: {summary['commentary_lines']}")
    
    if summary['commentary_lines'] > 0:
        print("✅ Commentary system is working correctly!")
        print("\n🎙️  Generated Commentary:")
        for line in summary['commentary']:
            print(f"   [{line['caster']}] {line['text']}")
    else:
        print("❌ No commentary was generated")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_commentary_system()
