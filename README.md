🧙‍♂️ Harry Potter Talking Painting – README
This project simulates a Harry Potter–style magical painting that listens to your voice, responds like a portrait at Hogwarts, and plays a video of the "talking painting" using AI tools including Whisper, OpenAI, ElevenLabs, and Hedra video generation.

🪄 What It Does
 -- Asks the user if they want to talk to the painting.
  
 -- Records audio on confirmation.
  
 -- Transcribes your voice using Whisper.
  
 -- Sends the transcription to ChatGPT with a magical-themed prompt.
  
 -- Converts the AI-generated response into speech using ElevenLabs.
  
 -- Creates a moving painting video with Hedra, animating an image (e.g., the Fat Lady).
  
 -- Plays the final video using your system’s default video player or OpenCV as fallback.

🧰 Requirements
Install the following Python libraries:

uv add sounddevice scipy openai python-dotenv requests opencv-python elevenlabs whisper 
# i use uv but you can also use pip i think
You also need:
 -Python 3.8+
 -ffmpeg (for Whisper)

🔐 API Keys Required
You must add API keys for the following:

  --OpenAI (for GPT-4o)
  
  --ElevenLabs (for text-to-speech)
  
  --Hedra (for AI video generation)

You can either:

Paste your keys directly into the code (as shown)

Or store them in a .env file and load with dotenv
