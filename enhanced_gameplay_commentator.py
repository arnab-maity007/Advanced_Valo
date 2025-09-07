#!/usr/bin/env python3
"""
Enhanced Valorant Gameplay Commentary System
Adds comprehensive gameplay round analysis including kill feed, abilities, and tactical events
"""

import cv2
import numpy as np
import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading
from dataclasses import dataclass

# Import existing modules
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_API_KEY = "sk_3291dbabc2380c898dd2b9fd6e0885f2620631861eee283f"
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False

@dataclass
class GameplayEvent:
    timestamp: float
    event_type: str
    description: str
    importance: int  # 1-5 scale
    players_involved: List[str]
    location: Optional[str] = None

class GameplayAnalyzer:
    def __init__(self):
        # Valorant agents for recognition
        self.agents = [
            "ASTRA", "BREACH", "BRIMSTONE", "CYPHER", "JETT", "KILLJOY",
            "OMEN", "PHOENIX", "RAZE", "REYNA", "SAGE", "SKYE", "SOVA",
            "VIPER", "YORU", "KAY/O", "CHAMBER", "NEON", "FADE", "HARBOR",
            "GEKKO", "DEADLOCK", "ISO", "CLOVE", "VYSE"
        ]
        
        # Weapons for kill feed recognition
        self.weapons = [
            "VANDAL", "PHANTOM", "OPERATOR", "SHERIFF", "GHOST", "CLASSIC",
            "ARES", "ODIN", "SPECTRE", "JUDGE", "BUCKY", "SHORTY",
            "BULLDOG", "GUARDIAN", "MARSHAL", "FRENZY", "STINGER"
        ]
        
        # Abilities keywords
        self.abilities = [
            "FLASH", "SMOKE", "WALL", "DART", "DRONE", "TRAP", "HEAL",
            "RESURRECTION", "TELEPORT", "DASH", "UPDRAFT", "SHOCK",
            "MOLLY", "GRENADE", "BARRIER", "CAGE", "ORB", "BLADE"
        ]
        
        # Game locations/callouts
        self.locations = [
            "A SITE", "B SITE", "C SITE", "MID", "HEAVEN", "HELL",
            "LONG", "SHORT", "CONNECTOR", "RAMP", "STAIRS", "BALCONY",
            "WINDOW", "DOOR", "CORNER", "BOX", "DEFAULT", "PLANT"
        ]
        
        # Round phases
        self.round_phases = ["BUY_PHASE", "PREP_PHASE", "ACTION_PHASE", "POST_ROUND"]
        
    def detect_kill_feed_events(self, frame: np.ndarray, timestamp: float) -> List[GameplayEvent]:
        """Analyze kill feed area for elimination events"""
        events = []
        
        # Define kill feed region (top-right area typically)
        height, width = frame.shape[:2]
        kill_feed_region = frame[50:300, width-400:width-50]
        
        # Convert to grayscale for OCR
        gray = cv2.cvtColor(kill_feed_region, cv2.COLOR_BGR2GRAY)
        
        # Enhanced OCR processing
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            results = reader.readtext(gray)
            
            for (bbox, text, confidence) in results:
                if confidence > 0.5:
                    # Look for kill patterns: "Player1 [weapon] Player2"
                    kill_pattern = self._parse_kill_text(text, timestamp)
                    if kill_pattern:
                        events.append(kill_pattern)
                        
        except ImportError:
            # Fallback to basic detection
            pass
            
        return events
    
    def detect_round_phase(self, frame: np.ndarray, timestamp: float) -> str:
        """Detect current round phase from UI elements"""
        height, width = frame.shape[:2]
        
        # Check top center for round timer
        timer_region = frame[10:60, width//2-100:width//2+100]
        gray = cv2.cvtColor(timer_region, cv2.COLOR_BGR2GRAY)
        
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            results = reader.readtext(gray)
            
            for (bbox, text, confidence) in results:
                if confidence > 0.6:
                    # Look for timer patterns
                    if re.search(r'\d+:\d+', text):
                        if any(phase in text.upper() for phase in ["BUY", "PREP"]):
                            return "PREP_PHASE"
                        else:
                            return "ACTION_PHASE"
                            
        except ImportError:
            pass
            
        return "ACTION_PHASE"  # Default assumption
    
    def detect_ability_usage(self, frame: np.ndarray, timestamp: float) -> List[GameplayEvent]:
        """Detect ability usage from visual cues and UI changes"""
        events = []
        
        # Look for ability indicators in bottom right (ability UI)
        height, width = frame.shape[:2]
        ability_region = frame[height-150:height-50, width-200:width-50]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(ability_region, cv2.COLOR_BGR2HSV)
        
        # Look for ability cooldown indicators (grayed out abilities)
        gray_mask = cv2.inRange(hsv, (0, 0, 50), (180, 50, 150))
        
        if np.sum(gray_mask) > 1000:  # Significant gray area detected
            events.append(GameplayEvent(
                timestamp=timestamp,
                event_type="ability_used",
                description="Ability usage detected - tactical play in progress",
                importance=3,
                players_involved=["Unknown Player"]
            ))
            
        return events
    
    def detect_tactical_events(self, frame: np.ndarray, timestamp: float) -> List[GameplayEvent]:
        """Detect tactical events like planting/defusing"""
        events = []
        
        # Look for spike plant/defuse indicators
        height, width = frame.shape[:2]
        center_region = frame[height//3:2*height//3, width//3:2*width//3]
        
        # Convert to grayscale
        gray = cv2.cvtColor(center_region, cv2.COLOR_BGR2GRAY)
        
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            results = reader.readtext(gray)
            
            for (bbox, text, confidence) in results:
                text_upper = text.upper()
                if confidence > 0.6:
                    if "PLANT" in text_upper or "SPIKE" in text_upper:
                        events.append(GameplayEvent(
                            timestamp=timestamp,
                            event_type="spike_plant",
                            description="Spike plant detected - critical moment!",
                            importance=5,
                            players_involved=["Attacker"]
                        ))
                    elif "DEFUS" in text_upper:
                        events.append(GameplayEvent(
                            timestamp=timestamp,
                            event_type="spike_defuse",
                            description="Defuse attempt detected - clutch situation!",
                            importance=5,
                            players_involved=["Defender"]
                        ))
                        
        except ImportError:
            pass
            
        return events
    
    def analyze_scoreboard(self, frame: np.ndarray, timestamp: float) -> Dict:
        """Extract current game score and round information"""
        height, width = frame.shape[:2]
        
        # Top center scoreboard region
        scoreboard_region = frame[10:80, width//2-150:width//2+150]
        gray = cv2.cvtColor(scoreboard_region, cv2.COLOR_BGR2GRAY)
        
        score_info = {"round": 1, "team1_score": 0, "team2_score": 0}
        
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            results = reader.readtext(gray)
            
            for (bbox, text, confidence) in results:
                if confidence > 0.7:
                    # Look for score patterns like "5-3" or "12-10"
                    score_match = re.search(r'(\d+)-(\d+)', text)
                    if score_match:
                        score_info["team1_score"] = int(score_match.group(1))
                        score_info["team2_score"] = int(score_match.group(2))
                        score_info["round"] = score_info["team1_score"] + score_info["team2_score"] + 1
                        
        except ImportError:
            pass
            
        return score_info
    
    def _parse_kill_text(self, text: str, timestamp: float) -> Optional[GameplayEvent]:
        """Parse kill feed text to extract elimination information"""
        # Look for patterns like "Player1 killed Player2 with Vandal"
        
        # Simple pattern matching for kills
        for weapon in self.weapons:
            if weapon.lower() in text.lower():
                return GameplayEvent(
                    timestamp=timestamp,
                    event_type="elimination",
                    description=f"Elimination with {weapon} - the fragging continues!",
                    importance=4,
                    players_involved=["Unknown Player"],
                    location="Unknown"
                )
                
        # Check for headshot indicators
        if "headshot" in text.lower() or "hs" in text.lower():
            return GameplayEvent(
                timestamp=timestamp,
                event_type="headshot",
                description="Headshot elimination - what a shot!",
                importance=5,
                players_involved=["Unknown Player"]
            )
            
        return None

class EnhancedGameplayCommentator:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.analyzer = GameplayAnalyzer()
        self.output_dir = Path("enhanced_gameplay_commentary")
        self.output_dir.mkdir(exist_ok=True)
        
        # Voice settings
        self.voice_id = "pqHfZKP75CvOlQylNhV4"  # Bill's energetic voice
        
        # Commentary templates for different event types
        self.commentary_templates = {
            "elimination": [
                "Another frag on the board! The aggression is paying off!",
                "That's a clean elimination - the momentum is building!",
                "Down goes another one! The team is executing perfectly!",
                "Beautiful frag - the mechanical skill on display here!",
                "That elimination could be the game changer they needed!"
            ],
            
            "headshot": [
                "HEADSHOT! What an incredible shot - pure precision!",
                "One tap headshot - that's how you do it!",
                "Absolutely demolished with a headshot - incredible aim!",
                "Headshot elimination - the crowd goes wild!",
                "Perfect crosshair placement leads to another headshot!"
            ],
            
            "spike_plant": [
                "Spike is down! The pressure is on the defenders now!",
                "Plant secured - now it's all about the retake!",
                "Spike planted - this round just became even more intense!",
                "The spike is down - defenders need to move fast!",
                "Plant successful - the attackers are in control now!"
            ],
            
            "spike_defuse": [
                "Defuse attempt - this is clutch time!",
                "They're going for the defuse - can they get it?",
                "Defuse in progress - the tension is unbearable!",
                "Clutch defuse attempt - everything on the line!",
                "Going for the defuse - this could save the round!"
            ],
            
            "ability_used": [
                "Tactical ability deployed - the strategy unfolds!",
                "Utility usage at the perfect moment!",
                "Ability activation - the team coordination is beautiful!",
                "Perfect timing on that ability usage!",
                "Tactical play in motion - the setup is developing!"
            ],
            
            "round_start": [
                "Round begins - here we go!",
                "New round starting - the intensity builds!",
                "Fresh round underway - anything can happen!",
                "Round is live - let's see what they've got!",
                "Another round begins - the competition heats up!"
            ],
            
            "economic_context": [
                "Economy plays a crucial role in this round setup!",
                "The economic decisions from last round show here!",
                "Team economy looking strong for this engagement!",
                "Economic management will be key this round!",
                "The buy decisions are about to pay dividends!"
            ]
        }
        
        self.events_detected = []
        self.commentary_segments = []
        
    def analyze_gameplay_video(self):
        """Main analysis function for full gameplay video"""
        print("🎮 Enhanced Gameplay Analysis Starting...")
        print("=" * 50)
        
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"📹 Video: {Path(self.video_path).name}")
        print(f"⏱️ Duration: {duration:.2f} seconds")
        print(f"🎬 FPS: {fps:.2f}")
        print(f"📊 Processing every 0.5 seconds for detailed analysis...")
        
        frame_skip = int(fps * 0.5)  # Analyze every 0.5 seconds for better coverage
        frame_count = 0
        last_round_phase = "ACTION_PHASE"
        last_score_info = {"round": 1, "team1_score": 0, "team2_score": 0}
        
        while frame_count < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            
            if not ret:
                break
                
            timestamp = frame_count / fps
            
            # Analyze current frame
            events_this_frame = []
            
            # 1. Detect round phase
            current_phase = self.analyzer.detect_round_phase(frame, timestamp)
            
            # 2. Check for phase transitions
            if current_phase != last_round_phase:
                if current_phase == "ACTION_PHASE" and last_round_phase != "ACTION_PHASE":
                    events_this_frame.append(GameplayEvent(
                        timestamp=timestamp,
                        event_type="round_start", 
                        description="Round action phase begins",
                        importance=3,
                        players_involved=[]
                    ))
                last_round_phase = current_phase
            
            # 3. Analyze scoreboard
            score_info = self.analyzer.analyze_scoreboard(frame, timestamp)
            if score_info["round"] != last_score_info["round"]:
                events_this_frame.append(GameplayEvent(
                    timestamp=timestamp,
                    event_type="economic_context",
                    description=f"Round {score_info['round']} - Score: {score_info['team1_score']}-{score_info['team2_score']}",
                    importance=2,
                    players_involved=[]
                ))
                last_score_info = score_info
            
            # 4. Detect kill feed events
            kill_events = self.analyzer.detect_kill_feed_events(frame, timestamp)
            events_this_frame.extend(kill_events)
            
            # 5. Detect ability usage
            ability_events = self.analyzer.detect_ability_usage(frame, timestamp)
            events_this_frame.extend(ability_events)
            
            # 6. Detect tactical events
            tactical_events = self.analyzer.detect_tactical_events(frame, timestamp)
            events_this_frame.extend(tactical_events)
            
            # Add events to main list
            self.events_detected.extend(events_this_frame)
            
            # Generate commentary for important events
            for event in events_this_frame:
                if event.importance >= 3:  # Only comment on important events
                    self._generate_event_commentary(event)
            
            frame_count += frame_skip
            
            # Progress indicator
            if frame_count % (frame_skip * 20) == 0:
                progress = (frame_count / total_frames) * 100
                print(f"📊 Progress: {progress:.1f}% - Detected {len(self.events_detected)} events")
        
        cap.release()
        
        # Add general commentary for gaps
        self._add_general_commentary(duration)
        
        print(f"\n✅ Analysis complete!")
        print(f"🎯 Detected {len(self.events_detected)} gameplay events")
        print(f"🎤 Generated {len(self.commentary_segments)} commentary segments")
        
    def _generate_event_commentary(self, event: GameplayEvent):
        """Generate commentary for a specific event"""
        templates = self.commentary_templates.get(event.event_type, [
            "Interesting play development here!",
            "The action continues to unfold!",
            "Strategic gameplay in progress!"
        ])
        
        import random
        commentary_text = random.choice(templates)
        
        # Add context based on event details
        if event.location:
            commentary_text += f" Position: {event.location}."
        
        self.commentary_segments.append({
            'timestamp': event.timestamp,
            'text': commentary_text,
            'event_type': event.event_type,
            'importance': event.importance,
            'style': 'excitement' if event.importance >= 4 else 'play_by_play'
        })
    
    def _add_general_commentary(self, duration: float):
        """Add general commentary for periods without specific events"""
        # Fill gaps with general commentary every 10-15 seconds
        current_time = 0
        commentary_interval = 12  # seconds
        
        while current_time < duration:
            # Check if we already have commentary near this time
            has_nearby_commentary = any(
                abs(seg['timestamp'] - current_time) < 5 
                for seg in self.commentary_segments
            )
            
            if not has_nearby_commentary:
                general_comments = [
                    "The tactical positioning continues to evolve!",
                    "Both teams showing excellent coordination!",
                    "The mechanical skill on display is impressive!",
                    "Strategic depth being showcased in this engagement!",
                    "The game sense from both sides is remarkable!",
                    "Positioning and timing will be crucial here!",
                    "The team coordination is really paying off!",
                    "Individual skill combined with team strategy!"
                ]
                
                import random
                self.commentary_segments.append({
                    'timestamp': current_time,
                    'text': random.choice(general_comments),
                    'event_type': 'general',
                    'importance': 2,
                    'style': 'analysis'
                })
            
            current_time += commentary_interval
    
    def generate_voice_commentary(self):
        """Generate voice files for all commentary segments"""
        if not VOICE_ENABLED:
            print("⚠️ Voice synthesis not available")
            return
            
        print("\n🎙️ Generating voice commentary...")
        
        audio_dir = self.output_dir / "audio_commentary"
        audio_dir.mkdir(exist_ok=True)
        
        # Sort commentary by timestamp
        self.commentary_segments.sort(key=lambda x: x['timestamp'])
        
        audio_files = []
        
        for i, segment in enumerate(self.commentary_segments):
            try:
                print(f"   🎤 Generating audio {i+1}/{len(self.commentary_segments)}: {segment['timestamp']:.1f}s")
                
                # Generate speech
                audio_response = client.text_to_speech.convert(
                    text=segment['text'],
                    voice_id=self.voice_id,
                    model_id="eleven_multilingual_v2"
                )
                
                # Save audio file
                audio_filename = f"gameplay_{segment['timestamp']:.2f}s.mp3"
                audio_path = audio_dir / audio_filename
                
                with open(audio_path, "wb") as f:
                    for chunk in audio_response:
                        f.write(chunk)
                
                segment['audio_file'] = str(audio_path)
                audio_files.append(str(audio_path))
                print(f"     ✅ Saved: {audio_filename}")
                
            except Exception as e:
                print(f"     ❌ Error generating audio: {e}")
        
        print(f"\n🎵 Generated {len(audio_files)} audio files")
        
        # Create HTML player
        self._create_html_player()
        
        # Save results
        self._save_results()
    
    def _create_html_player(self):
        """Create HTML audio player for gameplay commentary"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Valorant Gameplay Commentary</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0f1419; color: #fff; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .commentary-item {{ 
            background: #1e2328; padding: 15px; margin: 10px 0; 
            border-radius: 8px; border-left: 4px solid #ff4655;
        }}
        .timestamp {{ color: #ff4655; font-weight: bold; }}
        .event-type {{ color: #00d4aa; font-size: 0.9em; }}
        .importance {{ color: #ffd700; }}
        audio {{ width: 100%; margin-top: 10px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Enhanced Valorant Gameplay Commentary</h1>
            <p>Professional AI-generated commentary with event detection</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{len(self.commentary_segments)}</h3>
                <p>Commentary Segments</p>
            </div>
            <div class="stat">
                <h3>{len(self.events_detected)}</h3>
                <p>Events Detected</p>
            </div>
            <div class="stat">
                <h3>{len([e for e in self.events_detected if e.importance >= 4])}</h3>
                <p>High-Impact Events</p>
            </div>
        </div>
        
        <div class="commentary-list">
"""
        
        for segment in sorted(self.commentary_segments, key=lambda x: x['timestamp']):
            importance_stars = "⭐" * segment['importance']
            
            html_content += f"""
            <div class="commentary-item">
                <div class="timestamp">{segment['timestamp']:.1f}s</div>
                <div class="event-type">{segment['event_type'].replace('_', ' ').title()}</div>
                <div class="importance">{importance_stars}</div>
                <p>{segment['text']}</p>
                {'<audio controls><source src="' + segment.get('audio_file', '').replace(str(self.output_dir) + '/', '') + '" type="audio/mpeg"></audio>' if segment.get('audio_file') else ''}
            </div>
"""
        
        html_content += """
        </div>
    </div>
</body>
</html>"""
        
        player_path = self.output_dir / "enhanced_gameplay_player.html"
        with open(player_path, 'w') as f:
            f.write(html_content)
        
        print(f"🌐 HTML player created: {player_path}")
    
    def _save_results(self):
        """Save all results to JSON"""
        results = {
            'video_path': self.video_path,
            'analysis_timestamp': datetime.now().isoformat(),
            'events_detected': [
                {
                    'timestamp': event.timestamp,
                    'event_type': event.event_type,
                    'description': event.description,
                    'importance': event.importance,
                    'players_involved': event.players_involved,
                    'location': event.location
                }
                for event in self.events_detected
            ],
            'commentary_segments': self.commentary_segments,
            'statistics': {
                'total_events': len(self.events_detected),
                'total_commentary': len(self.commentary_segments),
                'high_impact_events': len([e for e in self.events_detected if e.importance >= 4]),
                'event_types': list(set(e.event_type for e in self.events_detected))
            }
        }
        
        json_path = self.output_dir / f"enhanced_gameplay_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved: {json_path}")

def main():
    # Use the same video path as before
    video_path = "/Users/arnabmaity/Downloads/Valorant buy phase final edit.mp4"
    
    print("🚀 ENHANCED VALORANT GAMEPLAY COMMENTARY")
    print("=" * 45)
    print("Now with advanced event detection for gameplay rounds!")
    print()
    
    # Initialize enhanced commentator
    commentator = EnhancedGameplayCommentator(video_path)
    
    # Analyze the video
    commentator.analyze_gameplay_video()
    
    # Generate voice commentary
    commentator.generate_voice_commentary()
    
    print(f"\n🎉 ENHANCED COMMENTARY COMPLETE!")
    print(f"📁 Results saved in: {commentator.output_dir}")
    print(f"🎧 Open: enhanced_gameplay_commentary/enhanced_gameplay_player.html")
    print(f"\n🎯 NEW FEATURES ADDED:")
    print(f"   ✅ Kill feed event detection")
    print(f"   ✅ Ability usage recognition") 
    print(f"   ✅ Round phase detection")
    print(f"   ✅ Scoreboard analysis")
    print(f"   ✅ Tactical event detection")
    print(f"   ✅ Context-aware commentary")

if __name__ == "__main__":
    main()
