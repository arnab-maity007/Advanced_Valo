#!/usr/bin/env python3
"""
Valorant Video Commentary Generator with Voice Synthesis
Processes video files and generates AI commentary with TTS audio output
"""

import cv2
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import threading
import subprocess
from typing import List, Dict

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "Output Processed Json"))

# ElevenLabs for voice synthesis
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_API_KEY = "sk_3291dbabc2380c898dd2b9fd6e0885f2620631861eee283f"
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    VOICE_ENABLED = True
    print("✅ ElevenLabs voice synthesis enabled")
except ImportError:
    print("⚠️ ElevenLabs not available - audio commentary disabled")
    VOICE_ENABLED = False

class VoiceCommentaryGenerator:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.output_dir = Path("voice_commentary_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Voice settings
        self.voice_id = "pqHfZKP75CvOlQylNhV4"  # Bill voice
        self.voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
        
        # Audio output directory
        self.audio_dir = self.output_dir / "audio_commentary"
        self.audio_dir.mkdir(exist_ok=True)
        
        # Processing results
        self.commentary_segments = []
        self.audio_files = []
        
        print(f"🎤 Voice Commentary Generator Initialized")
        print(f"📹 Video: {Path(video_path).name}")
        print(f"📁 Output: {self.output_dir}")
        print(f"🔊 Audio: {self.audio_dir}")
        
    def analyze_video_and_extract_frames(self, interval_seconds: float = 3.0):
        """Analyze video and extract frames for commentary"""
        print(f"📊 Analyzing video and extracting frames...")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   FPS: {fps:.2f}")
        print(f"   Extracting frames every {interval_seconds}s")
        
        # Extract frames
        frame_interval = int(fps * interval_seconds)
        frames_dir = self.output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        frame_count = 0
        extracted_frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frame_filename = f"frame_{timestamp:.2f}s.jpg"
                frame_path = frames_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                
                extracted_frames.append({
                    'path': str(frame_path),
                    'timestamp': timestamp,
                    'frame_number': frame_count
                })
                
            frame_count += 1
            
        cap.release()
        print(f"✅ Extracted {len(extracted_frames)} frames")
        return extracted_frames, duration, fps
        
    def generate_advanced_commentary(self, frames: List[Dict], duration: float):
        """Generate more realistic and varied commentary"""
        print(f"🎤 Generating advanced commentary...")
        
        # Advanced commentary templates with different styles
        commentary_styles = {
            'play_by_play': [
                "We're in the buy phase now, and the economic decisions are crucial here.",
                "Players are weighing their options carefully - every credit counts.",
                "The team is coordinating their purchases for maximum impact.",
                "Smart economic management on display as they plan their loadouts.",
                "Critical buy phase decisions being made - this could define the round.",
                "The economy is looking strong, enabling some powerful weapon purchases.",
                "Tactical considerations are paramount during this buy phase.",
                "Team coordination is key as they allocate their resources wisely."
            ],
            'analysis': [
                "From a tactical standpoint, these weapon choices make perfect sense.",
                "The economic flow of this team has been impressive throughout the match.",
                "Notice how they're prioritizing utility alongside their weapon purchases.",
                "This buy strategy shows excellent understanding of the current game state.",
                "The risk-reward calculation here is fascinating to observe.",
                "Strategic depth on full display during this purchasing phase.",
                "These economic decisions reflect a well-coordinated team strategy.",
                "The meta considerations are clearly influencing their buy choices."
            ],
            'excitement': [
                "This is where the magic happens - the buy phase that could change everything!",
                "Look at the confidence in these purchases - they're going for the big play!",
                "The anticipation is building as they lock in these weapon selections!",
                "Full send mode activated - these buys show they mean business!",
                "The crowd can feel the energy as these crucial decisions unfold!",
                "Game-changing potential in every purchase being made right now!",
                "The intensity is palpable during this critical buy phase!",
                "Championship-level decision making happening before our eyes!"
            ],
            'educational': [
                "For newer players watching, notice how they balance weapons and utility.",
                "This is a textbook example of proper economic management in Valorant.",
                "The thought process behind each purchase teaches us about team coordination.",
                "Understanding these buy patterns is crucial for improving your gameplay.",
                "Pay attention to how they prioritize different weapon categories.",
                "This demonstrates the importance of communication during buy phases.",
                "Learning from these professional-level purchasing decisions is invaluable.",
                "These economic principles apply to players at every skill level."
            ]
        }
        
        # Generate commentary with variety
        style_rotation = ['play_by_play', 'analysis', 'excitement', 'educational']
        current_style_index = 0
        
        for i, frame_info in enumerate(frames):
            # Generate commentary every few frames to avoid overwhelming
            if i % 4 == 0:  # Commentary every ~12 seconds
                timestamp = frame_info['timestamp']
                
                # Rotate through commentary styles for variety
                current_style = style_rotation[current_style_index % len(style_rotation)]
                current_style_index += 1
                
                # Select commentary from current style
                import random
                commentary_text = random.choice(commentary_styles[current_style])
                
                # Add timestamp context for some commentary
                if 'crucial' in commentary_text.lower() or 'critical' in commentary_text.lower():
                    if timestamp < duration * 0.3:
                        commentary_text += " Early in the video, setting the tone for what's to come."
                    elif timestamp > duration * 0.7:
                        commentary_text += " As we approach the later stages, the stakes are higher."
                
                self.commentary_segments.append({
                    'timestamp': timestamp,
                    'text': commentary_text,
                    'style': current_style,
                    'frame_path': frame_info['path']
                })
                
                print(f"   📝 {timestamp:.1f}s: [{current_style}] {commentary_text[:60]}...")
                
        print(f"✅ Generated {len(self.commentary_segments)} commentary segments")
        
    def generate_voice_commentary(self):
        """Generate voice audio for each commentary segment"""
        if not VOICE_ENABLED:
            print("❌ Voice synthesis not available - skipping audio generation")
            return
            
        print(f"🔊 Generating voice commentary using ElevenLabs...")
        
        for i, segment in enumerate(self.commentary_segments):
            try:
                print(f"   🎙️ Generating audio {i+1}/{len(self.commentary_segments)}: {segment['timestamp']:.1f}s")
                
                # Generate speech using correct ElevenLabs API
                audio_response = client.text_to_speech.convert(
                    text=segment['text'],
                    voice_id=self.voice_id,
                    model_id="eleven_multilingual_v2"
                )
                
                # Save audio file
                audio_filename = f"commentary_{segment['timestamp']:.2f}s.mp3"
                audio_path = self.audio_dir / audio_filename
                
                with open(audio_path, "wb") as f:
                    for chunk in audio_response:
                        f.write(chunk)
                        
                segment['audio_file'] = str(audio_path)
                self.audio_files.append(str(audio_path))
                
                print(f"     ✅ Saved: {audio_filename}")
                
                # Small delay to respect API limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"     ❌ Error generating audio for segment {i+1}: {e}")
                segment['audio_file'] = None
                
        print(f"✅ Generated {len(self.audio_files)} audio files")
        
    def create_audio_playlist(self):
        """Create an audio playlist/compilation"""
        if not self.audio_files:
            print("❌ No audio files to compile")
            return
            
        print(f"🎵 Creating audio playlist...")
        
        # Create a simple M3U playlist
        playlist_file = self.output_dir / "commentary_playlist.m3u"
        with open(playlist_file, 'w') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Valorant Buy Phase Commentary Playlist\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for segment in self.commentary_segments:
                if segment.get('audio_file'):
                    audio_file = Path(segment['audio_file'])
                    f.write(f"#EXTINF:-1,Commentary at {segment['timestamp']:.1f}s\n")
                    f.write(f"{audio_file.name}\n")
                    
        print(f"✅ Playlist created: {playlist_file.name}")
        
        # Create a simple HTML player
        html_player = self.output_dir / "commentary_player.html"
        with open(html_player, 'w') as f:
            f.write(self._generate_html_player())
            
        print(f"✅ HTML player created: {html_player.name}")
        
    def _generate_html_player(self):
        """Generate HTML audio player"""
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Valorant Commentary Player</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f1419; color: #ff4654; }
        h1 { text-align: center; color: #ff4654; }
        .commentary-item { background: #1e2328; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4654; }
        .timestamp { font-weight: bold; color: #00f5ff; }
        .style { color: #ffb800; font-size: 0.9em; }
        .text { margin: 10px 0; line-height: 1.4; }
        audio { width: 100%; margin-top: 10px; }
        .stats { background: #2a2d33; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🎮 Valorant Buy Phase Commentary</h1>
    
    <div class="stats">
        <h3>Commentary Statistics</h3>
        <p><strong>Total Segments:</strong> """ + str(len(self.commentary_segments)) + """</p>
        <p><strong>Audio Files:</strong> """ + str(len(self.audio_files)) + """</p>
        <p><strong>Video:</strong> """ + Path(self.video_path).name + """</p>
    </div>
    
"""
        
        for segment in self.commentary_segments:
            html += f"""
    <div class="commentary-item">
        <div class="timestamp">⏱️ {segment['timestamp']:.1f}s</div>
        <div class="style">📺 Style: {segment.get('style', 'general').replace('_', ' ').title()}</div>
        <div class="text">{segment['text']}</div>
"""
            if segment.get('audio_file'):
                audio_path = Path(segment['audio_file']).name
                html += f'        <audio controls><source src="audio_commentary/{audio_path}" type="audio/mpeg">Your browser does not support audio.</audio>\n'
            html += "    </div>\n"
            
        html += """
    <div style="text-align: center; margin-top: 30px; color: #666;">
        <p>Generated by Valorant AI Commentary System</p>
    </div>
</body>
</html>
"""
        return html
        
    def save_results(self):
        """Save all results including voice commentary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(self.video_path).stem
        
        # Save complete results as JSON
        results_file = self.output_dir / f"{video_name}_voice_commentary_{timestamp}.json"
        results = {
            'video_path': self.video_path,
            'video_name': video_name,
            'generated_at': datetime.now().isoformat(),
            'voice_enabled': VOICE_ENABLED,
            'total_commentary_segments': len(self.commentary_segments),
            'total_audio_files': len(self.audio_files),
            'commentary_segments': self.commentary_segments,
            'audio_files': self.audio_files
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        # Generate enhanced transcript
        transcript_file = self.output_dir / f"{video_name}_voice_transcript_{timestamp}.txt"
        with open(transcript_file, 'w') as f:
            f.write("🎤 VALORANT VOICE COMMENTARY TRANSCRIPT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Video: {Path(self.video_path).name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Voice Synthesis: {'Enabled' if VOICE_ENABLED else 'Disabled'}\n")
            f.write(f"Commentary Segments: {len(self.commentary_segments)}\n")
            f.write(f"Audio Files: {len(self.audio_files)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, segment in enumerate(self.commentary_segments, 1):
                timestamp_str = f"{segment['timestamp']:.1f}s"
                style = segment.get('style', 'general').replace('_', ' ').title()
                audio_status = "🔊" if segment.get('audio_file') else "🔇"
                
                f.write(f"[{i:2d}] {timestamp_str:>8} | {audio_status} [{style:>12}] {segment['text']}\n")
                if segment.get('audio_file'):
                    f.write(f"     Audio: {Path(segment['audio_file']).name}\n")
                f.write("\n")
                
        print(f"\n💾 Results Saved:")
        print(f"   📄 JSON: {results_file.name}")
        print(f"   📝 Transcript: {transcript_file.name}")
        print(f"   🎵 Playlist: commentary_playlist.m3u")
        print(f"   🌐 Player: commentary_player.html")
        print(f"   🔊 Audio Files: {len(self.audio_files)} files in audio_commentary/")
        
    def process_video_with_voice(self):
        """Main processing pipeline with voice synthesis"""
        try:
            print(f"\n🚀 Starting voice commentary generation...")
            start_time = time.time()
            
            # Step 1: Extract frames and analyze
            print(f"\n📊 Step 1: Analyzing video and extracting frames...")
            frames, duration, fps = self.analyze_video_and_extract_frames(interval_seconds=3.0)
            
            # Step 2: Generate commentary
            print(f"\n🎤 Step 2: Generating advanced commentary...")
            self.generate_advanced_commentary(frames, duration)
            
            # Step 3: Generate voice audio
            print(f"\n🔊 Step 3: Generating voice synthesis...")
            self.generate_voice_commentary()
            
            # Step 4: Create audio playlist and player
            print(f"\n🎵 Step 4: Creating audio playlist and player...")
            self.create_audio_playlist()
            
            # Step 5: Save results
            print(f"\n💾 Step 5: Saving results...")
            self.save_results()
            
            processing_time = time.time() - start_time
            
            print(f"\n🎉 VOICE COMMENTARY COMPLETE!")
            print(f"⏱️ Total time: {processing_time:.2f} seconds")
            print(f"🎤 Generated {len(self.commentary_segments)} commentary segments")
            print(f"🔊 Created {len(self.audio_files)} audio files")
            print(f"📁 Results saved in: {self.output_dir}")
            print(f"\n🎧 To listen to commentary:")
            print(f"   - Open: {self.output_dir}/commentary_player.html")
            print(f"   - Or play individual files from: {self.audio_dir}/")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    print("🎤 Valorant Voice Commentary Generator")
    print("=" * 50)
    
    # Use the provided video path
    video_path = "/Users/arnabmaity/Downloads/Valorant buy phase final edit.mp4"
    print(f"📹 Processing: {Path(video_path).name}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
        
    # Create generator and process video with voice
    generator = VoiceCommentaryGenerator(video_path)
    success = generator.process_video_with_voice()
    
    if success:
        print(f"\n🎉 Success! Your voice commentary is ready!")
        print(f"🌐 Open the HTML player to listen: {generator.output_dir}/commentary_player.html")
    else:
        print(f"❌ Processing failed. Check the error messages above.")

if __name__ == "__main__":
    main()
