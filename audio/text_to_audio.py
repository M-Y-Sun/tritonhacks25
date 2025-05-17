#!/usr/bin/env python3

import sys
import os
from gtts import gTTS
from datetime import datetime

def text_to_speech(text):
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '911_dashboard', 'data', 'audio')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'speech_{timestamp}.mp3')
        
        # Create gTTS object and save directly to output file
        print(f"Converting text to speech: {text}")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        
        print(f"Audio saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python text_to_audio.py 'Your text message here'")
        sys.exit(1)
    
    # Get the input text from command line arguments
    input_text = ' '.join(sys.argv[1:])
    
    # Convert text to speech
    output_file = text_to_speech(input_text)
    
    if output_file:
        print("Text-to-speech conversion completed successfully!")
    else:
        print("Failed to convert text to speech.")
        sys.exit(1)

if __name__ == "__main__":
    main()
