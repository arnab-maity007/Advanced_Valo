#!/usr/bin/env python3
"""
Advanced Valorant Video Commentary Generator
Integrates with existing buy phase commentary system to generate real AI commentary
"""

import cv2
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess
import tempfile
import shutil

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "Output Processed Json"))

class AdvancedVideoCommentaryGenerator:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.output_dir = Path("advanced_video_commentary")
        self.output_dir.mkdir(exist_ok=True)
        
        # Video properties
        self.fps = 30
        self.total_frames = 0
        self.duration = 0
        
        # Processing results
        self.commentary_segments = []
        self.processed_frames = []
        
        print(f"🎮 Advanced Valorant Video Commentary Generator")
        print(f"📹 Video: {Path(video_path).name}")
        print(f"📁 Output: {self.output_dir}")
        
    def analyze_video_properties(self):
        """Analyze video properties"""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
            
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        
        cap.release()
        
        print(f"📊 Video Analysis:")
        print(f"   Duration: {self.duration:.2f} seconds")
        print(f"   FPS: {self.fps:.2f}")
        print(f"   Total Frames: {self.total_frames}")
        
    def extract_frames_for_analysis(self, interval_seconds: float = 1.0):
        """Extract frames at regular intervals for analysis"""
        frames_dir = self.output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        cap = cv2.VideoCapture(self.video_path)
        frame_interval = int(self.fps * interval_seconds)
        
        print(f"🔍 Extracting frames every {interval_seconds}s ({frame_interval} frames)")
        
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / self.fps
                frame_filename = f"frame_{extracted_count:04d}_{timestamp:.2f}s.jpg"
                frame_path = frames_dir / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                
                self.processed_frames.append({
                    'path': str(frame_path),
                    'timestamp': timestamp,
                    'frame_number': frame_count,
                    'extracted_index': extracted_count
                })
                
                extracted_count += 1
                if extracted_count % 10 == 0:
                    print(f"   Extracted {extracted_count} frames...")
                    
            frame_count += 1
            
        cap.release()
        print(f"✅ Extracted {extracted_count} frames for analysis")
        
    def run_buy_phase_detection(self):
        """Run buy phase detection on extracted frames using existing YOLO model"""
        print(f"🎯 Running buy phase detection on frames...")
        
        # Check if YOLO model exists
        model_path = "best.pt"
        if not os.path.exists(model_path):
            print(f"⚠️ YOLO model not found at {model_path}")
            print("   Generating mock detections for demonstration...")
            self._generate_mock_detections()
            return
            
        # Try to use existing buyphase processor
        try:
            from buyphase import YOLOProcessor
            processor = YOLOProcessor(model_path=model_path, confidence_threshold=0.7)
            
            detections = []
            for frame_info in self.processed_frames:
                try:
                    result = processor.process_single_image(frame_info['path'])
                    if result and result.get('predictions'):
                        detections.append({
                            'timestamp': frame_info['timestamp'],
                            'frame_path': frame_info['path'],
                            'detections': result['predictions']
                        })
                        print(f"   🎯 Detections at {frame_info['timestamp']:.2f}s: {len(result['predictions'])} objects")
                        
                except Exception as e:
                    print(f"   ❌ Error processing {frame_info['path']}: {e}")
                    
            # Save detection results
            detections_file = self.output_dir / "buy_phase_detections.json"
            with open(detections_file, 'w') as f:
                json.dump(detections, f, indent=2)
                
            print(f"✅ Buy phase detection complete. Found {len(detections)} frames with detections")
            
        except ImportError:
            print("⚠️ Could not import YOLO processor. Using mock detections.")
            self._generate_mock_detections()
            
    def _generate_mock_detections(self):
        """Generate mock detections for demonstration when YOLO is not available"""
        print("🎭 Generating mock buy phase detections...")
        
        mock_detections = []
        for i, frame_info in enumerate(self.processed_frames):
            # Generate mock detection every few frames
            if i % 3 == 0:  # Every 3rd frame has "buy phase activity"
                mock_detections.append({
                    'timestamp': frame_info['timestamp'],
                    'frame_path': frame_info['path'],
                    'detections': [
                        {
                            'class': 'event-box',
                            'confidence': 0.85 + (i % 10) * 0.01,
                            'bbox': [100, 100, 200, 150],
                            'mock_ocr_text': self._generate_mock_ocr_text(i)
                        }
                    ]
                })
                
        # Save mock detection results
        detections_file = self.output_dir / "mock_buy_phase_detections.json"
        with open(detections_file, 'w') as f:
            json.dump(mock_detections, f, indent=2)
            
        print(f"✅ Generated {len(mock_detections)} mock detection frames")
        
    def _generate_mock_ocr_text(self, index: int):
        """Generate realistic mock OCR text for buy phase elements"""
        weapons = ['Vandal', 'Phantom', 'Operator', 'Ghost', 'Sheriff', 'Spectre', 'Judge']
        statuses = ['OWNED', 'REQUESTING', 'EQUIPPED']
        players = ['TenZ', 'ScreaM', 'Shroud', 'Player1', 'Player2']
        
        weapon = weapons[index % len(weapons)]
        status = statuses[index % len(statuses)]
        player = players[index % len(players)]
        
        return f"{status} {weapon} {player}"
        
    def generate_ai_commentary(self):
        """Generate AI commentary using existing commentary system"""
        print(f"🎤 Generating AI commentary...")
        
        # Load detection results
        detections_file = self.output_dir / "buy_phase_detections.json"
        mock_detections_file = self.output_dir / "mock_buy_phase_detections.json"
        
        detections = []
        if detections_file.exists():
            with open(detections_file, 'r') as f:
                detections = json.load(f)
        elif mock_detections_file.exists():
            with open(mock_detections_file, 'r') as f:
                detections = json.load(f)
                
        if not detections:
            print("❌ No detections found for commentary generation")
            return
            
        # Try to use existing commentary system
        try:
            self._use_existing_commentary_system(detections)
        except ImportError:
            print("⚠️ Using backup commentary generation...")
            self._generate_backup_commentary(detections)
            
    def _use_existing_commentary_system(self, detections):
        """Use the existing buycommentary system"""
        from buycommentary import BuyPhaseCommentator, Event, EventType
        
        commentator = BuyPhaseCommentator()
        
        for detection in detections:
            timestamp = detection['timestamp']
            
            # Convert detections to events
            for det in detection['detections']:
                mock_text = det.get('mock_ocr_text', '')
                
                if 'REQUESTING' in mock_text:
                    weapon = self._extract_weapon_from_text(mock_text)
                    player = self._extract_player_from_text(mock_text)
                    
                    event = Event(
                        timestamp=timestamp,
                        event_type=EventType.REQUESTING_WEAPON.value,
                        player=player,
                        weapon=weapon
                    )
                    
                    commentary = commentator.generate_commentary(event)
                    if commentary:
                        self.commentary_segments.append({
                            'timestamp': timestamp,
                            'text': commentary.text,
                            'caster': commentary.caster,
                            'event_type': 'requesting_weapon',
                            'player': player,
                            'weapon': weapon
                        })
                        
                elif 'OWNED' in mock_text:
                    weapon = self._extract_weapon_from_text(mock_text)
                    player = self._extract_player_from_text(mock_text)
                    
                    event = Event(
                        timestamp=timestamp,
                        event_type=EventType.WEAPON_OWNED.value,
                        player=player,
                        weapon=weapon
                    )
                    
                    commentary = commentator.generate_commentary(event)
                    if commentary:
                        self.commentary_segments.append({
                            'timestamp': timestamp,
                            'text': commentary.text,
                            'caster': commentary.caster,
                            'event_type': 'weapon_owned',
                            'player': player,
                            'weapon': weapon
                        })
                        
        print(f"✅ Generated {len(self.commentary_segments)} commentary segments using AI system")
        
    def _generate_backup_commentary(self, detections):
        """Backup commentary generation when existing system is not available"""
        commentary_templates = {
            'requesting': [
                "{player} is calling for a {weapon}! The team needs to step up!",
                "Big request from {player} — they want that {weapon}!",
                "{player} asking for backup! They need a {weapon} drop!",
                "Communication is key! {player} wants a {weapon} — who's got their back?",
                "Strategic call from {player}! {weapon} request on the table!"
            ],
            'owned': [
                "{player} locks in the {weapon}! Let's go!",
                "Full commitment! {player} grabs the {weapon}!",
                "{player} locked and loaded with that {weapon}!",
                "Business time! {player} secures the {weapon}!",
                "Perfect buy from {player} — {weapon} in hand!"
            ]
        }
        
        for detection in detections:
            timestamp = detection['timestamp']
            
            for det in detection['detections']:
                mock_text = det.get('mock_ocr_text', '')
                
                if 'REQUESTING' in mock_text:
                    weapon = self._extract_weapon_from_text(mock_text)
                    player = self._extract_player_from_text(mock_text)
                    
                    import random
                    template = random.choice(commentary_templates['requesting'])
                    commentary_text = template.format(player=player, weapon=weapon)
                    
                    self.commentary_segments.append({
                        'timestamp': timestamp,
                        'text': commentary_text,
                        'caster': 'Hype',
                        'event_type': 'requesting_weapon',
                        'player': player,
                        'weapon': weapon
                    })
                    
                elif 'OWNED' in mock_text:
                    weapon = self._extract_weapon_from_text(mock_text)
                    player = self._extract_player_from_text(mock_text)
                    
                    import random
                    template = random.choice(commentary_templates['owned'])
                    commentary_text = template.format(player=player, weapon=weapon)
                    
                    self.commentary_segments.append({
                        'timestamp': timestamp,
                        'text': commentary_text,
                        'caster': 'Hype',
                        'event_type': 'weapon_owned',
                        'player': player,
                        'weapon': weapon
                    })
                    
        print(f"✅ Generated {len(self.commentary_segments)} backup commentary segments")
        
    def _extract_weapon_from_text(self, text: str) -> str:
        """Extract weapon name from OCR text"""
        weapons = ['Vandal', 'Phantom', 'Operator', 'Ghost', 'Sheriff', 'Spectre', 'Judge']
        text_upper = text.upper()
        
        for weapon in weapons:
            if weapon.upper() in text_upper:
                return weapon
                
        return 'Unknown'
        
    def _extract_player_from_text(self, text: str) -> str:
        """Extract player name from OCR text"""
        players = ['TenZ', 'ScreaM', 'Shroud', 'Player1', 'Player2']
        
        for player in players:
            if player in text:
                return player
                
        return 'Player'
        
    def save_final_results(self):
        """Save all final results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(self.video_path).stem
        
        # Save complete results as JSON
        results_file = self.output_dir / f"{video_name}_complete_results_{timestamp}.json"
        complete_results = {
            'video_path': self.video_path,
            'video_name': video_name,
            'generated_at': datetime.now().isoformat(),
            'video_properties': {
                'duration': self.duration,
                'fps': self.fps,
                'total_frames': self.total_frames
            },
            'processing_summary': {
                'frames_extracted': len(self.processed_frames),
                'commentary_segments': len(self.commentary_segments)
            },
            'commentary_segments': self.commentary_segments
        }
        
        with open(results_file, 'w') as f:
            json.dump(complete_results, f, indent=2)
            
        # Generate commentary transcript
        transcript_file = self.output_dir / f"{video_name}_ai_commentary_{timestamp}.txt"
        with open(transcript_file, 'w') as f:
            f.write("🎮 VALORANT AI BUY PHASE COMMENTARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Video: {Path(self.video_path).name}\n")
            f.write(f"Duration: {self.duration:.2f} seconds\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Commentary Segments: {len(self.commentary_segments)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, segment in enumerate(self.commentary_segments, 1):
                timestamp_str = f"{segment['timestamp']:.2f}s"
                caster = segment.get('caster', 'AI')
                
                f.write(f"[{i:3d}] {timestamp_str:>8} | [{caster:>8}] {segment['text']}\n")
                
                # Add event details if available
                if 'event_type' in segment:
                    event_details = f"        Event: {segment['event_type']}"
                    if 'player' in segment:
                        event_details += f" | Player: {segment['player']}"
                    if 'weapon' in segment:
                        event_details += f" | Weapon: {segment['weapon']}"
                    f.write(f"        {event_details}\n")
                f.write("\n")
                
            f.write("=" * 60 + "\n")
            f.write("End of AI Commentary\n")
            
        print(f"\n💾 Final Results Saved:")
        print(f"   📄 Complete JSON: {results_file.name}")
        print(f"   📝 AI Commentary: {transcript_file.name}")
        print(f"   📁 All files in: {self.output_dir}")
        
    def process_video(self):
        """Main processing pipeline"""
        try:
            print(f"\n🚀 Starting advanced video commentary generation...")
            start_time = time.time()
            
            # Step 1: Analyze video
            print(f"\n📊 Step 1: Analyzing video properties...")
            self.analyze_video_properties()
            
            # Step 2: Extract frames
            print(f"\n🔍 Step 2: Extracting frames for analysis...")
            self.extract_frames_for_analysis(interval_seconds=1.0)
            
            # Step 3: Run buy phase detection
            print(f"\n🎯 Step 3: Running buy phase detection...")
            self.run_buy_phase_detection()
            
            # Step 4: Generate AI commentary
            print(f"\n🎤 Step 4: Generating AI commentary...")
            self.generate_ai_commentary()
            
            # Step 5: Save results
            print(f"\n💾 Step 5: Saving final results...")
            self.save_final_results()
            
            processing_time = time.time() - start_time
            
            print(f"\n✅ PROCESSING COMPLETE!")
            print(f"⏱️ Total time: {processing_time:.2f} seconds")
            print(f"🎤 Generated {len(self.commentary_segments)} commentary segments")
            print(f"📁 Results saved in: {self.output_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            return False

def main():
    """Main function"""
    print("🎮 Advanced Valorant Video Commentary Generator")
    print("=" * 50)
    
    # Use the provided video path
    video_path = "/Users/arnabmaity/Downloads/Valorant buy phase final edit.mp4"
    print(f"📹 Using video file: {video_path}")
    
    # Check for command line argument override
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"📹 Command line override: {video_path}")
        
    if not video_path or not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
        
    # Create generator and process video
    generator = AdvancedVideoCommentaryGenerator(video_path)
    success = generator.process_video()
    
    if success:
        print(f"\n🎉 Success! Your AI commentary is ready!")
        print(f"📂 Check the results in: {generator.output_dir}")
    else:
        print(f"❌ Processing failed. Check the error messages above.")

if __name__ == "__main__":
    main()
