#!/usr/bin/env python3
"""
Simple Video Commentary Test Script
Processes your test video and generates buy phase commentary
"""

import cv2
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "Output Processed Json"))

def test_video_commentary(video_path: str):
    """
    Simple test function to process your video and generate commentary
    """
    print("🎮 Valorant Buy Phase Video Commentary Generator")
    print("=" * 50)
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("Please provide the correct path to your test video")
        return
    
    # Create output directory
    output_dir = Path("video_commentary_results")
    output_dir.mkdir(exist_ok=True)
    
    print(f"📹 Processing video: {video_path}")
    print(f"💾 Output directory: {output_dir}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video file: {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"📊 Video Properties:")
    print(f"   - Duration: {duration:.2f} seconds")
    print(f"   - FPS: {fps:.2f}")
    print(f"   - Total Frames: {total_frames}")
    
    # Extract frames at intervals (every 2 seconds)
    frame_interval = int(fps * 2)  # Every 2 seconds
    frames_dir = output_dir / "extracted_frames"
    frames_dir.mkdir(exist_ok=True)
    
    extracted_frames = []
    frame_count = 0
    commentary_segments = []
    
    print(f"\n🔍 Extracting frames every {frame_interval} frames (~2 seconds)")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            # Save frame
            timestamp = frame_count / fps
            frame_filename = f"frame_{timestamp:.2f}s.jpg"
            frame_path = frames_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)
            extracted_frames.append({
                'path': str(frame_path),
                'timestamp': timestamp,
                'frame_number': frame_count
            })
            
            print(f"   📸 Extracted frame at {timestamp:.2f}s")
            
            # Generate mock commentary for demonstration
            commentary = generate_mock_commentary(timestamp, frame_count)
            if commentary:
                commentary_segments.append({
                    'timestamp': timestamp,
                    'text': commentary,
                    'frame_path': str(frame_path)
                })
                print(f"   🎤 Commentary: {commentary}")
        
        frame_count += 1
    
    cap.release()
    
    # Save results
    save_commentary_results(output_dir, video_path, commentary_segments, extracted_frames)
    
    print(f"\n✅ Processing complete!")
    print(f"📈 Extracted {len(extracted_frames)} frames")
    print(f"🎤 Generated {len(commentary_segments)} commentary segments")
    print(f"📁 Results saved in: {output_dir}")

def generate_mock_commentary(timestamp: float, frame_number: int) -> str:
    """
    Generate mock commentary for demonstration
    In a real implementation, this would use OCR and AI analysis
    """
    # Mock commentary templates
    commentary_templates = [
        "The buy phase is heating up! Players are making their weapon selections.",
        "Interesting economic decisions being made here at the {:.1f} second mark.",
        "We can see some strategic weapon purchases happening right now.",
        "The team is coordinating their buys - this could be crucial for the upcoming round.",
        "Look at that weapon selection! Someone's going for a full buy here.",
        "Economic management is key in Valorant, and we're seeing it in action.",
        "The buy phase dynamics are really coming into play at this moment.",
        "Strategic thinking on display as players make their purchasing decisions.",
        "This is where game knowledge really shows - smart buy phase choices.",
        "The team economy is being managed beautifully here."
    ]
    
    # Generate commentary every ~6 seconds
    if int(timestamp) % 6 == 0:
        import random
        return random.choice(commentary_templates).format(timestamp)
    
    return None

def save_commentary_results(output_dir: Path, video_path: str, commentary_segments: list, extracted_frames: list):
    """Save all results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_name = Path(video_path).stem
    
    # Save commentary as JSON
    commentary_file = output_dir / f"{video_name}_commentary_{timestamp}.json"
    results = {
        'video_path': video_path,
        'generated_at': datetime.now().isoformat(),
        'video_name': video_name,
        'total_commentary_segments': len(commentary_segments),
        'total_frames_extracted': len(extracted_frames),
        'commentary_segments': commentary_segments,
        'extracted_frames': extracted_frames
    }
    
    with open(commentary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate commentary transcript
    transcript_file = output_dir / f"{video_name}_transcript_{timestamp}.txt"
    with open(transcript_file, 'w') as f:
        f.write(f"VALORANT BUY PHASE COMMENTARY TRANSCRIPT\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Video: {Path(video_path).name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Segments: {len(commentary_segments)}\n")
        f.write(f"{'=' * 50}\n\n")
        
        for i, segment in enumerate(commentary_segments, 1):
            timestamp_str = f"{segment['timestamp']:.2f}s"
            f.write(f"[{i:2d}] {timestamp_str:>8} | {segment['text']}\n")
        
        f.write(f"\n{'=' * 50}\n")
        f.write(f"End of Commentary Transcript\n")
    
    print(f"\n💾 Files saved:")
    print(f"   📄 Commentary JSON: {commentary_file.name}")
    print(f"   📝 Transcript: {transcript_file.name}")
    print(f"   📁 Frames: extracted_frames/ ({len(extracted_frames)} files)")

def main():
    """Main function to run the test"""
    print("🎬 Welcome to Valorant Video Commentary Generator!")
    
    # Use the provided video path
    video_path = "/Users/arnabmaity/Downloads/Valorant buy phase final edit.mp4"
    
    print(f"📹 Using video file: {video_path}")
    
    # Check for command line argument override
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"📹 Command line override: {video_path}")
    
    # Run the test
    test_video_commentary(video_path)

if __name__ == "__main__":
    main()
