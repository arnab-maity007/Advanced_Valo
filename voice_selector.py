#!/usr/bin/env python3
"""
Voice Selector for Valorant Commentary
Allows users to preview and select different ElevenLabs voices
"""

from elevenlabs.client import ElevenLabs
import os
from pathlib import Path

# ElevenLabs setup
ELEVENLABS_API_KEY = "sk_3291dbabc2380c898dd2b9fd6e0885f2620631861eee283f"
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Pre-defined voice options with descriptions
VOICE_OPTIONS = {
    "1": {
        "id": "pNInz6obpgDQGcFmaJgB", 
        "name": "Adam", 
        "description": "Deep, authoritative analyst voice - perfect for strategic breakdowns"
    },
    "2": {
        "id": "Xb7hH8MSUJpSbSDYk0k2", 
        "name": "Brian", 
        "description": "Professional, clear commentator voice - great for play-by-play (current)"
    },
    "3": {
        "id": "pqHfZKP75CvOlQylNhV4", 
        "name": "Bill", 
        "description": "Energetic, exciting hype voice - ideal for intense moments"
    },
    "4": {
        "id": "EXAVITQu4vr4xnSDxMaL", 
        "name": "Bella", 
        "description": "Clear, engaging female voice - excellent for educational content"
    },
    "5": {
        "id": "ErXwobaYiN019PkySvjV", 
        "name": "Antoni", 
        "description": "Smooth, charismatic voice - perfect for entertainment commentary"
    },
    "6": {
        "id": "VR6AewLTigWG4xSOukaG", 
        "name": "Arnold", 
        "description": "Strong, confident voice - great for competitive analysis"
    }
}

def list_available_voices():
    """Display all available voice options"""
    print("\n🎤 AVAILABLE VOICES FOR VALORANT COMMENTARY")
    print("=" * 50)
    
    for key, voice in VOICE_OPTIONS.items():
        current = " (CURRENT)" if voice["id"] == "Xb7hH8MSUJpSbSDYk0k2" else ""
        print(f"{key}. {voice['name']}{current}")
        print(f"   {voice['description']}")
        print()

def generate_voice_preview(voice_id: str, voice_name: str):
    """Generate a preview audio file for the selected voice"""
    preview_text = "Welcome to Valorant commentary! The buy phase is crucial for team success. Let's analyze these strategic decisions."
    
    try:
        print(f"🎙️ Generating preview for {voice_name}...")
        
        # Generate audio
        audio_response = client.text_to_speech.convert(
            text=preview_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2"
        )
        
        # Save preview file
        preview_dir = Path("voice_previews")
        preview_dir.mkdir(exist_ok=True)
        
        preview_file = preview_dir / f"preview_{voice_name.lower()}.mp3"
        
        with open(preview_file, "wb") as f:
            for chunk in audio_response:
                f.write(chunk)
        
        print(f"✅ Preview saved: {preview_file}")
        print(f"🎧 Play the file to hear {voice_name}'s voice!")
        
        # Try to play the audio on macOS
        try:
            import subprocess
            subprocess.run(["afplay", str(preview_file)], check=True, capture_output=True)
            print(f"🔊 Playing preview for {voice_name}...")
        except:
            print(f"💡 Manually play: {preview_file}")
            
        return str(preview_file)
        
    except Exception as e:
        print(f"❌ Error generating preview: {e}")
        return None

def update_voice_in_generator(new_voice_id: str, new_voice_name: str):
    """Update the voice ID in the main voice commentary generator"""
    file_path = Path("voice_commentary_generator.py")
    
    try:
        # Read the current file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the voice ID
        old_line = 'self.voice_id = "Xb7hH8MSUJpSbSDYk0k2"  # Professional voice'
        new_line = f'self.voice_id = "{new_voice_id}"  # {new_voice_name} voice'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
        else:
            # Try to find any voice_id line and replace it
            import re
            pattern = r'self\.voice_id = "[^"]*".*'
            replacement = f'self.voice_id = "{new_voice_id}"  # {new_voice_name} voice'
            content = re.sub(pattern, replacement, content)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Updated voice_commentary_generator.py to use {new_voice_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        return False

def main():
    print("🎤 VALORANT VOICE COMMENTARY SELECTOR")
    print("=" * 40)
    
    while True:
        list_available_voices()
        
        print("Options:")
        print("P - Preview a voice")
        print("S - Select and apply a voice")
        print("Q - Quit")
        
        choice = input("\nEnter your choice: ").strip().upper()
        
        if choice == 'Q':
            print("👋 Goodbye!")
            break
            
        elif choice == 'P':
            voice_num = input("Enter voice number to preview (1-6): ").strip()
            if voice_num in VOICE_OPTIONS:
                voice = VOICE_OPTIONS[voice_num]
                generate_voice_preview(voice["id"], voice["name"])
            else:
                print("❌ Invalid voice number!")
                
        elif choice == 'S':
            voice_num = input("Enter voice number to select (1-6): ").strip()
            if voice_num in VOICE_OPTIONS:
                voice = VOICE_OPTIONS[voice_num]
                
                print(f"\n🎯 Selected: {voice['name']}")
                print(f"📝 Description: {voice['description']}")
                
                confirm = input("Apply this voice? (y/n): ").strip().lower()
                if confirm == 'y':
                    if update_voice_in_generator(voice["id"], voice["name"]):
                        print(f"\n🎉 Success! Voice changed to {voice['name']}")
                        print("🚀 Run 'python voice_commentary_generator.py' to generate commentary with the new voice!")
                        break
                    else:
                        print("❌ Failed to update voice")
                else:
                    print("❌ Voice change cancelled")
            else:
                print("❌ Invalid voice number!")
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
