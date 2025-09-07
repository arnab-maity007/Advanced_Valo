#!/usr/bin/env python3
"""
Valorant AI Commentary Integration Bridge
Connects the web interface with the OCR/commentary Python system
"""

import sys
import os
import json
import threading
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import socketio
import asyncio
import argparse

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from buycommentary import CommentaryGenerator
    from easy_ocr import EasyOCRProcessor
    from video import VideoProcessor
    from model import AgentDetector
except ImportError as e:
    print(f"Warning: Could not import existing modules: {e}")
    print("Make sure all dependencies are installed and modules are accessible")

class WebCommentaryBridge:
    def __init__(self, server_url="http://localhost:3000"):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.session_id = None
        self.commentary_active = False
        self.ocr_processor = None
        self.commentary_generator = None
        self.video_processor = None
        self.agent_detector = None
        
        # Threading control
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # Game state
        self.current_game_data = {
            'map': None,
            'agent': None,
            'phase': None,
            'round_number': None,
            'score': None
        }
        
        self.setup_socket_handlers()
        
    def setup_socket_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            print("Connected to web server")
            
        @self.sio.event
        def disconnect():
            print("Disconnected from web server")
            
        @self.sio.on('start-commentary')
        def on_start_commentary(data):
            self.start_commentary_session(data)
            
        @self.sio.on('stop-commentary')
        def on_stop_commentary(data):
            self.stop_commentary_session()
            
        @self.sio.on('pause-commentary')
        def on_pause_commentary(data):
            self.pause_commentary()
            
        @self.sio.on('resume-commentary')
        def on_resume_commentary(data):
            self.resume_commentary()
            
    def connect_to_server(self):
        """Connect to the web server"""
        try:
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
            
    def initialize_processors(self):
        """Initialize OCR and commentary processors"""
        try:
            # Initialize OCR processor
            self.ocr_processor = EasyOCRProcessor()
            
            # Initialize commentary generator
            self.commentary_generator = CommentaryGenerator()
            
            # Initialize video processor
            self.video_processor = VideoProcessor()
            
            # Initialize agent detector
            self.agent_detector = AgentDetector()
            
            print("All processors initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize processors: {e}")
            return False
            
    def start_commentary_session(self, session_data):
        """Start a new commentary session"""
        if self.commentary_active:
            print("Commentary already active")
            return
            
        self.session_id = session_data.get('sessionId')
        game_settings = session_data.get('gameSettings', {})
        
        print(f"Starting commentary session: {self.session_id}")
        print(f"Game settings: {game_settings}")
        
        # Store game settings
        self.current_game_data.update({
            'map': game_settings.get('map'),
            'agent': game_settings.get('agent'),
            'commentary_style': game_settings.get('commentaryStyle', 'professional')
        })
        
        # Initialize processors if not already done
        if not self.ocr_processor:
            if not self.initialize_processors():
                self.emit_error("Failed to initialize processors")
                return
                
        # Start processing thread
        self.commentary_active = True
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self.commentary_loop)
        self.processing_thread.start()
        
        # Notify server
        self.sio.emit('commentary-started', {
            'sessionId': self.session_id,
            'status': 'active'
        })
        
    def stop_commentary_session(self):
        """Stop the current commentary session"""
        if not self.commentary_active:
            return
            
        print(f"Stopping commentary session: {self.session_id}")
        
        self.commentary_active = False
        self.stop_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
            
        # Notify server
        self.sio.emit('commentary-stopped', {
            'sessionId': self.session_id,
            'status': 'stopped'
        })
        
        self.session_id = None
        
    def pause_commentary(self):
        """Pause commentary processing"""
        if self.commentary_active:
            self.commentary_active = False
            print("Commentary paused")
            
    def resume_commentary(self):
        """Resume commentary processing"""
        if not self.commentary_active and self.session_id:
            self.commentary_active = True
            print("Commentary resumed")
            
    def commentary_loop(self):
        """Main commentary processing loop"""
        print("Starting commentary loop")
        frame_count = 0
        last_commentary_time = 0
        commentary_interval = 2.0  # Generate commentary every 2 seconds
        
        while not self.stop_event.is_set():
            try:
                if not self.commentary_active:
                    time.sleep(0.1)
                    continue
                    
                # Capture screen
                screenshot = self.capture_screen()
                if screenshot is None:
                    time.sleep(0.1)
                    continue
                    
                frame_count += 1
                current_time = time.time()
                
                # Process OCR every frame for real-time updates
                ocr_data = self.process_ocr(screenshot)
                
                # Update game state
                self.update_game_state(ocr_data)
                
                # Generate commentary at intervals
                if current_time - last_commentary_time > commentary_interval:
                    commentary = self.generate_commentary(ocr_data)
                    if commentary:
                        self.emit_commentary(commentary)
                        last_commentary_time = current_time
                        
                # Emit game updates
                self.emit_game_update({
                    'timestamp': datetime.now().isoformat(),
                    'frame': frame_count,
                    'game_data': self.current_game_data,
                    'ocr_data': ocr_data
                })
                
                # Small delay to prevent overwhelming
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in commentary loop: {e}")
                time.sleep(1)
                
        print("Commentary loop ended")
        
    def capture_screen(self):
        """Capture current screen"""
        try:
            # Use the existing video processor to capture screen
            if self.video_processor:
                return self.video_processor.capture_frame()
            else:
                # Fallback screenshot method
                import pyautogui
                return pyautogui.screenshot()
        except Exception as e:
            print(f"Failed to capture screen: {e}")
            return None
            
    def process_ocr(self, image):
        """Process OCR on captured image"""
        try:
            if self.ocr_processor and image:
                results = self.ocr_processor.process_image(image)
                return results
        except Exception as e:
            print(f"OCR processing error: {e}")
        return {}
        
    def update_game_state(self, ocr_data):
        """Update current game state based on OCR data"""
        try:
            # Extract game information from OCR
            if 'buy_phase' in ocr_data:
                self.current_game_data['phase'] = 'buy'
            elif 'round_start' in ocr_data:
                self.current_game_data['phase'] = 'round'
            elif 'round_end' in ocr_data:
                self.current_game_data['phase'] = 'end'
                
            # Extract score if available
            if 'score' in ocr_data:
                self.current_game_data['score'] = ocr_data['score']
                
            # Detect agent if not specified
            if not self.current_game_data['agent'] and self.agent_detector:
                detected_agent = self.agent_detector.detect_agent(ocr_data)
                if detected_agent:
                    self.current_game_data['agent'] = detected_agent
                    
        except Exception as e:
            print(f"Failed to update game state: {e}")
            
    def generate_commentary(self, ocr_data):
        """Generate commentary based on current game state"""
        try:
            if self.commentary_generator:
                context = {
                    'game_data': self.current_game_data,
                    'ocr_data': ocr_data,
                    'style': self.current_game_data.get('commentary_style', 'professional')
                }
                
                commentary_text = self.commentary_generator.generate(context)
                
                return {
                    'text': commentary_text,
                    'timestamp': datetime.now().isoformat(),
                    'context': context,
                    'session_id': self.session_id
                }
                
        except Exception as e:
            print(f"Failed to generate commentary: {e}")
            
        return None
        
    def emit_commentary(self, commentary):
        """Send commentary to web interface"""
        if self.sio.connected:
            self.sio.emit('commentary', commentary)
            print(f"Commentary: {commentary['text']}")
            
    def emit_game_update(self, game_data):
        """Send game update to web interface"""
        if self.sio.connected:
            self.sio.emit('game-update', game_data)
            
    def emit_error(self, error_message):
        """Send error to web interface"""
        if self.sio.connected:
            self.sio.emit('error', {
                'message': error_message,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            })
            
    def run(self):
        """Main run method"""
        print("Starting Valorant AI Commentary Bridge")
        
        if not self.connect_to_server():
            print("Failed to connect to server. Exiting.")
            return
            
        try:
            # Keep the client running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        if self.commentary_active:
            self.stop_commentary_session()
            
        if self.sio.connected:
            self.sio.disconnect()
            
        print("Cleanup completed")

def main():
    parser = argparse.ArgumentParser(description='Valorant AI Commentary Bridge')
    parser.add_argument('--server', default='http://localhost:3000', 
                       help='Web server URL (default: http://localhost:3000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
    # Create and run bridge
    bridge = WebCommentaryBridge(args.server)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print('\nReceived shutdown signal')
        bridge.cleanup()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bridge.run()

if __name__ == "__main__":
    main()
