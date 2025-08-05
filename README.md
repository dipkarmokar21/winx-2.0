# 🤖 DEO - AI Voice Assistant (Python + Gemini API)

DEO is a lightweight AI assistant built with Python, PyQt6, and Google Gemini API. It uses voice input to understand your queries and responds using Gemini AI with voice output. Perfect for basic AI interaction through a simple GUI!

------------------------------------------
🌟 Features
------------------------------------------
- 🎤 Voice input using speech_recognition  
- 🧠 AI response using Google Gemini API  
- 🗣️ Voice output using pyttsx3  
- 🖼️ GUI interface built with PyQt6  
- 🔊 Animated avatar & waveform  
- ⚙️ Special command handling (YouTube, Spotify, etc.)

------------------------------------------
🚀 Requirements & Installation
------------------------------------------

# Install required Python modules:
pip install pyttsx3 speechrecognition google-generativeai PyQt6

# Optional (for better voice support):
pip install pyaudio

# ⚠️ If pyaudio fails to install on Android or some systems, you can skip it.

------------------------------------------
🔑 Add Your Gemini API Key
------------------------------------------

# Step 1: Get your API key from:
# https://aistudio.google.com/app/apikey

# Step 2: Open main.py and replace this line:
GOOGLE_API_KEY = "PASTE_YOUR_API_KEY_HERE"

# Never share this key publicly!

------------------------------------------
📂 Project Structure
------------------------------------------

DEO/
├── main.py            # Main app logic
├── voice.py           # Voice input/output functions
├── ui.py              # PyQt6 GUI and animations
└── README.md          # Project documentation

------------------------------------------
📌 Notes
------------------------------------------

- DEO needs internet to fetch responses from Gemini AI  
- Works best on desktop. Android possible with Pydroid3  
- You can customize commands, animations, UI, etc.