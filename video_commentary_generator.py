#!/usr/bin/env python3
"""
Valorant Video Commentary Generator
Processes video files containing buy phase clips and generates real-time AI commentary
"""

import cv2
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import argparse
from datetime import datetime
import numpy as np

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Output Processed Json"))

try:
    from buyphase import YOLOProcessor
    from easy_ocr import EasyOCRProcessor
    from buycommentary import BuyPhaseCommentator, Event, EventType
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Make sure all dependencies are installed")

class VideoCommentaryGenerator:
    def __init__(self, 
                 model_path: str = "best.pt",
                 confidence_threshold: float = 0.7,
                 commentary_interval: float = 2.0,
                 output_dir: str = "video_commentary_output"):
        """
        Initialize the video commentary generator
        
        Args:
            model_path: Path to YOLO model
            confidence_threshold: Confidence threshold for detections
            commentary_interval: Seconds between commentary generation
            output_dir: Directory to save output files
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.commentary_interval = commentary_interval
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize processors
        self.yolo_processor = None
        self.ocr_processor = None
        self.commentator = None
        
        # Video processing state
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.last_commentary_time = 0
        
        # Results storage
        self.all_commentary = []
        self.frame_analysis = []
        
        self._initialize_processors()
        
    def _initialize_processors(self):
        """Initialize all processing components"""
        try:
            # Initialize YOLO processor for buy phase detection
            self.yolo_processor = YOLOProcessor(
                model_path=self.model_path,
                confidence_threshold=self.confidence_threshold
            )
            print("✅ YOLO processor initialized")
            
            # Initialize OCR processor
            self.ocr_processor = EasyOCRProcessor()
            print("✅ OCR processor initialized")
            
            # Initialize commentary generator
            self.commentator = BuyPhaseCommentator()
            print("✅ Commentary generator initialized")
            
        except Exception as e:
            print(f"❌ Error initializing processors: {e}")
            print("Some features may not work properly")
            
    def extract_frames_from_video(self, video_path: str, frame_interval: int = 30) -> List[str]:
        """
        Extract frames from video at specified intervals
        
        Args:
            video_path: Path to video file
            frame_interval: Extract every N frames (default: every 30 frames = 1 second at 30fps)
            
        Returns:
            List of extracted frame paths
        """
        print(f"🎬 Extracting frames from {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
            
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = self.total_frames / self.fps
        
        print(f"📊 Video Info:")
        print(f"   - Duration: {duration:.2f} seconds")
        print(f"   - FPS: {self.fps}")
        print(f"   - Total Frames: {self.total_frames}")
        print(f"   - Extracting every {frame_interval} frames")
        
        # Create frames directory
        frames_dir = self.output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        extracted_frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                # Save frame
                frame_filename = f"frame_{frame_count:06d}.jpg"
                frame_path = frames_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                extracted_frames.append(str(frame_path))
                
                # Calculate timestamp
                timestamp = frame_count / self.fps
                print(f"   - Extracted frame at {timestamp:.2f}s: {frame_filename}")
                
            frame_count += 1
            
        cap.release()
        print(f"✅ Extracted {len(extracted_frames)} frames")
        return extracted_frames
        
    def process_frame(self, frame_path: str, timestamp: float) -> Dict:
        """
        Process a single frame for buy phase detection and OCR
        
        Args:
            frame_path: Path to frame image
            timestamp: Timestamp in video
            
        Returns:
            Dictionary containing analysis results
        """
        frame_result = {
            'frame_path': frame_path,
            'timestamp': timestamp,
            'buy_phase_detected': False,
            'events': [],
            'ocr_results': None,
            'commentary': None
        }
        
        try:
            # Run YOLO detection for buy phase elements
            if self.yolo_processor:
                yolo_results = self.yolo_processor.process_single_image(frame_path)
                
                # Check if buy phase elements are detected
                if yolo_results and yolo_results.get('predictions'):
                    frame_result['buy_phase_detected'] = True
                    frame_result['yolo_results'] = yolo_results
                    
                    # Run OCR on detected regions
                    ocr_results = self._process_ocr_on_detections(frame_path, yolo_results)
                    frame_result['ocr_results'] = ocr_results
                    
                    # Extract events from OCR results
                    events = self._extract_events_from_ocr(ocr_results, timestamp)
                    frame_result['events'] = events
                    
                    print(f"🎯 Frame {timestamp:.2f}s: Found {len(events)} buy phase events")
                    
        except Exception as e:
            print(f"❌ Error processing frame {frame_path}: {e}")
            
        return frame_result
        
    def _process_ocr_on_detections(self, frame_path: str, yolo_results: Dict) -> Dict:
        """Run OCR on YOLO detected regions"""
        if not self.ocr_processor:
            return {}
            
        try:
            # Load the frame
            frame = cv2.imread(frame_path)
            height, width = frame.shape[:2]
            
            ocr_results = []
            
            for prediction in yolo_results.get('predictions', []):
                # Extract bounding box
                bbox = prediction.get('bbox', [])
                if len(bbox) >= 4:
                    x, y, w, h = bbox
                    
                    # Ensure coordinates are within frame bounds
                    x1 = max(0, int(x))
                    y1 = max(0, int(y))
                    x2 = min(width, int(x + w))
                    y2 = min(height, int(y + h))
                    
                    # Crop the region
                    cropped = frame[y1:y2, x1:x2]
                    
                    if cropped.size > 0:
                        # Run OCR on cropped region
                        ocr_result = self.ocr_processor.process_image(cropped)
                        if ocr_result:
                            ocr_result['bbox'] = [x1, y1, x2, y2]
                            ocr_result['yolo_class'] = prediction.get('class', '')
                            ocr_results.append(ocr_result)
                            
            return {'results': ocr_results}
            
        except Exception as e:
            print(f"❌ OCR processing error: {e}")
            return {}
            
    def _extract_events_from_ocr(self, ocr_results: Dict, timestamp: float) -> List[Event]:
        """Extract buy phase events from OCR results"""
        events = []
        
        try:
            if not ocr_results or 'results' not in ocr_results:
                return events
                
            for result in ocr_results['results']:
                text = result.get('text', '').lower().strip()
                
                if not text:
                    continue
                    
                # Detect event types based on text content
                event = self._classify_text_to_event(text, timestamp)
                if event:
                    events.append(event)
                    
        except Exception as e:
            print(f"❌ Event extraction error: {e}")
            
        return events
        
    def _classify_text_to_event(self, text: str, timestamp: float) -> Optional[Event]:
        """Classify OCR text into buy phase events"""
        text = text.lower().strip()
        
        # Define weapons and their variants
        weapons = {
            'vandal': ['vandal', 'vandl', 'vanda'],
            'phantom': ['phantom', 'fantom', 'phant'],
            'operator': ['operator', 'op', 'opertr'],
            'ghost': ['ghost', 'gost', 'ghst'],
            'sheriff': ['sheriff', 'sherif'],
            'classic': ['classic', 'clasic'],
            'spectre': ['spectre', 'specter'],
            'judge': ['judge', 'juge'],
            'odin': ['odin', 'odn'],
            'ares': ['ares', 'are']
        }
        
        # Check for requesting patterns
        if any(req in text for req in ['requesting', 'request', 'req']):
            for weapon, variants in weapons.items():
                if any(variant in text for variant in variants):
                    return Event(
                        timestamp=timestamp,
                        event_type=EventType.REQUESTING_WEAPON.value,
                        player="Player",  # Could be extracted from other OCR
                        weapon=weapon
                    )
                    
        # Check for owned patterns
        if any(own in text for own in ['owned', 'ownd', 'own', 'equipped', 'omned']):
            for weapon, variants in weapons.items():
                if any(variant in text for variant in variants):
                    return Event(
                        timestamp=timestamp,
                        event_type=EventType.WEAPON_OWNED.value,
                        player="Player",
                        weapon=weapon
                    )
                    
        # Check for shield patterns
        if any(shield in text for shield in ['shield', 'armor', 'shields']):
            if any(own in text for own in ['owned', 'equipped', 'omned']):
                return Event(
                    timestamp=timestamp,
                    event_type=EventType.SHIELD_OWNED.value,
                    player="Player",
                    weapon="shields"
                )
                
        return None
        
    def generate_commentary_for_events(self, events: List[Event], timestamp: float) -> Optional[str]:
        """Generate commentary for detected events"""
        if not events or not self.commentator:
            return None
            
        try:
            # Check if enough time has passed since last commentary
            if timestamp - self.last_commentary_time < self.commentary_interval:
                return None
                
            # Generate commentary for the most significant event
            event = events[0]  # Take first event for now
            
            # Create commentary using the existing system
            commentary = self.commentator.generate_commentary(event)
            
            if commentary:
                self.last_commentary_time = timestamp
                return commentary.text
                
        except Exception as e:
            print(f"❌ Commentary generation error: {e}")
            
        return None
        
    def process_video(self, video_path: str, frame_interval: int = 30) -> Dict:
        """
        Process entire video and generate commentary
        
        Args:
            video_path: Path to video file
            frame_interval: Process every N frames
            
        Returns:
            Complete analysis results
        """
        print(f"🚀 Starting video commentary generation for: {video_path}")
        start_time = time.time()
        
        # Extract frames
        frames = self.extract_frames_from_video(video_path, frame_interval)
        
        # Process each frame
        print(f"\n🔍 Processing {len(frames)} frames for buy phase analysis...")
        
        for i, frame_path in enumerate(frames):
            # Calculate timestamp
            frame_number = int(Path(frame_path).stem.split('_')[1])
            timestamp = frame_number / self.fps
            
            print(f"\n📊 Processing frame {i+1}/{len(frames)} (t={timestamp:.2f}s)")
            
            # Analyze frame
            frame_result = self.process_frame(frame_path, timestamp)
            
            # Generate commentary if events found
            if frame_result['events']:
                commentary = self.generate_commentary_for_events(
                    frame_result['events'], 
                    timestamp
                )
                frame_result['commentary'] = commentary
                
                if commentary:
                    print(f"🎤 Commentary: {commentary}")
                    self.all_commentary.append({
                        'timestamp': timestamp,
                        'text': commentary,
                        'events': [e.__dict__ for e in frame_result['events']]
                    })
                    
            self.frame_analysis.append(frame_result)
            
        # Save results
        self._save_results(video_path)
        
        processing_time = time.time() - start_time
        print(f"\n✅ Video processing completed in {processing_time:.2f} seconds")
        print(f"📈 Generated {len(self.all_commentary)} commentary segments")
        
        return {
            'video_path': video_path,
            'processing_time': processing_time,
            'total_frames_processed': len(frames),
            'commentary_segments': len(self.all_commentary),
            'output_dir': str(self.output_dir)
        }
        
    def _save_results(self, video_path: str):
        """Save all results to files"""
        video_name = Path(video_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save commentary as JSON
        commentary_file = self.output_dir / f"{video_name}_commentary_{timestamp}.json"
        with open(commentary_file, 'w') as f:
            json.dump({
                'video_path': video_path,
                'generated_at': datetime.now().isoformat(),
                'commentary': self.all_commentary,
                'total_segments': len(self.all_commentary)
            }, f, indent=2)
            
        # Save detailed frame analysis
        analysis_file = self.output_dir / f"{video_name}_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            # Convert Events to dicts for JSON serialization
            serializable_analysis = []
            for frame in self.frame_analysis:
                frame_copy = frame.copy()
                frame_copy['events'] = [e.__dict__ for e in frame['events']]
                serializable_analysis.append(frame_copy)
                
            json.dump({
                'video_path': video_path,
                'generated_at': datetime.now().isoformat(),
                'frame_analysis': serializable_analysis
            }, f, indent=2)
            
        # Generate commentary transcript
        transcript_file = self.output_dir / f"{video_name}_transcript_{timestamp}.txt"
        with open(transcript_file, 'w') as f:
            f.write(f"Valorant Buy Phase Commentary Transcript\n")
            f.write(f"Video: {video_path}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for comm in self.all_commentary:
                timestamp_str = f"{comm['timestamp']:.2f}s"
                f.write(f"[{timestamp_str}] {comm['text']}\n\n")
                
        print(f"💾 Results saved:")
        print(f"   - Commentary: {commentary_file}")
        print(f"   - Analysis: {analysis_file}")
        print(f"   - Transcript: {transcript_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate AI commentary for Valorant buy phase video clips')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('--model', default='best.pt', help='Path to YOLO model (default: best.pt)')
    parser.add_argument('--confidence', type=float, default=0.7, help='Confidence threshold (default: 0.7)')
    parser.add_argument('--interval', type=int, default=30, help='Frame interval for processing (default: 30)')
    parser.add_argument('--commentary-interval', type=float, default=2.0, help='Seconds between commentary (default: 2.0)')
    parser.add_argument('--output', default='video_commentary_output', help='Output directory (default: video_commentary_output)')
    
    args = parser.parse_args()
    
    # Validate video file
    if not os.path.exists(args.video_path):
        print(f"❌ Video file not found: {args.video_path}")
        return
        
    # Initialize generator
    generator = VideoCommentaryGenerator(
        model_path=args.model,
        confidence_threshold=args.confidence,
        commentary_interval=args.commentary_interval,
        output_dir=args.output
    )
    
    # Process video
    try:
        results = generator.process_video(args.video_path, args.interval)
        print(f"\n🎉 Success! Check the output directory: {results['output_dir']}")
        
    except Exception as e:
        print(f"❌ Error processing video: {e}")

if __name__ == "__main__":
    main()
