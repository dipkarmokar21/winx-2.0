import sys
import queue
import threading
import random
import subprocess
import webbrowser
import re
import math
from datetime import datetime
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QTextCursor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QTimer, QObject

import pyttsx3
import speech_recognition as sr

# --- Google Gemini Setup ---
import google.generativeai as genai
GOOGLE_API_KEY = "Enter Your api key"
genai.configure(api_key=GOOGLE_API_KEY)
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

CREATOR_QUESTIONS = [
    "who is your creator", "who made you", "who is your developer", "your creator",
    "your developer", "created by whom", "who developed you", "developer", "creative", "who is your creative"
]
NAME_QUESTIONS = [
    "what is your name", "your name", "tell me your name", "who are you"
]
CREATOR_REPLIES = [
    "My existence is possible because of Dip Karmokar, my creator. ✨",
    "Dip Karmokar is the brilliant creator behind who I am. 💡",
    "All thanks to Dip Karmokar, the visionary who created me. 🙏✨",
    "I was brought to life by the creativity of Dip Karmokar. 🎨🤖",
    "Dip Karmokar imagined, designed, and created me. 🧠✍️",
    "My creator, Dip Karmokar, is the inspiration behind my abilities. 🌟",
    "The credit for my creation goes to Dip Karmokar. 🏆",
    "Dip Karmokar shaped and developed who I am today. 🛠️🌱",
    "Dip Karmokar is the creator who brought me to life. 🌟🤖"
]

def is_creator_question(text):
    txt = text.lower()
    return any(q in txt for q in CREATOR_QUESTIONS)

def is_name_question(text):
    txt = text.lower()
    return any(q in txt for q in NAME_QUESTIONS)

def autocorrect_command(text):
    corrections = {
        "poppins portray": "open spotify",
        "spotty pie": "open spotify",
        "poppins": "open spotify",
        "spotify": "open spotify",
        "you tube": "open youtube",
        "youtub": "open youtube",
        "open file": "open file explorer",
        "open explore": "open file explorer",
        "chat gpt": "open chatgpt",
        "hey deo": "hey deo",
        "open portal": "open portal",
        "vs code": "open vs code",
        "v s code": "open vs code",
        "vs": "open vs code",
        "visual studio": "open vs code",
        "code": "open vs code",
        "terminal": "open terminal",
        "cmd": "open terminal",
        "command prompt": "open terminal",
        "what's the time": "what is the time now",
        "what is time": "what is the time now",
        "what's time": "what is the time now",
        "time now": "what is the time now",
        "what's the date": "what is the date today",
        "what date": "what is the date today",
        "date today": "what is the date today",
        "today date": "what is the date today",
        "open google": "open google",
        "what is current date": "what is the date today"
    }
    for k, v in corrections.items():
        if k in text:
            return v
    return text

def clean_for_speech(text):
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\*\_`#>~\[\]\(\)\-]', '', text)
    text = re.sub(r':\w+:', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def handle_special_commands(user_text, window):
    text = user_text.lower()
    if any(phrase in text for phrase in [
        "what is the time now", "what time is it", "current time", "now time", "current time is", "tell me the time"
    ]):
        now = datetime.now()
        now_str = now.strftime("%I:%M %p")
        return f"The current time is {now_str}.", True
    if any(phrase in text for phrase in [
        "what is the date today", "today's date", "what date is today", "what is today", "date today", "what is the current date",
        "today date", "current date", "tell me the date"
    ]):
        today = datetime.now()
        date_str = today.strftime("%A, %d %B %Y")
        return f"Today's date is {date_str}.", True

    if user_text in ["open youtube"]:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube...", True
    if user_text in ["open facebook"]:
        webbrowser.open("https://facebook.com")
        return "Opening Facebook...", True
    if user_text in ["open google"]:
        webbrowser.open("https://google.com")
        return "Opening Google...", True
    if user_text in ["open file explorer"]:
        try:
            subprocess.Popen('explorer')
        except Exception:
            return "Sorry, couldn't open File Explorer.", True
        return "Opening File Explorer...", True
    if user_text in ["open spotify"]:
        spotify_paths = [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            r"C:\Program Files\Spotify\Spotify.exe",
            r"C:\Program Files (x86)\Spotify\Spotify.exe"
        ]
        for path in spotify_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path])
                    return "Opening Spotify...", True
                except Exception:
                    pass
        return "Sorry, couldn't open Spotify. Please make sure it's installed.", True
    if user_text in ["open chatgpt"]:
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT...", True
    if user_text in ["open portal"]:
        webbrowser.open("https://studentportal.green.edu.bd/")
        return "Opening Green University Student Portal...", True
    if user_text in ["open vs code"]:
        try:
            subprocess.Popen("code")
        except Exception:
            return "Sorry, couldn't open VS Code. Is it installed?", True
        return "Opening VS Code...", True
    if user_text in ["open terminal"]:
        try:
            subprocess.Popen("cmd")
        except Exception:
            return "Sorry, couldn't open Terminal.", True
        return "Opening Terminal...", True
    if user_text.strip() == "hey deo":
        return "Yes Boss, I'm listening! 👂", True
    return None, False

class GeminiWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
    def run(self):
        try:
            if is_creator_question(self.prompt):
                self.finished.emit(random.choice(CREATOR_REPLIES))
                return
            elif is_name_question(self.prompt):
                self.finished.emit("My name is DEO.")
                return
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            chat = model.start_chat()
            response = chat.send_message(self.prompt)
            text = ""
            if hasattr(response, "text") and response.text:
                text = response.text.strip()
            else:
                text = "Sorry, Gemini did not return a text reply."
            self.finished.emit(text)
        except Exception as e:
            err_msg = f"Sorry, AI service unavailable.<br><b>Error:</b> {str(e)}"
            self.error.emit(err_msg)

class SpeechManager(QThread):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.engine = pyttsx3.init()
        self._stop_flag = threading.Event()
        self._running = False
        self.voice_gender = "male"  # Default, will be set externally
    def set_gender(self, gender):
        voices = self.engine.getProperty('voices')
        # Try to match by gender text (if supported), else fallback to index
        gender = gender.lower()
        found = False
        for v in voices:
            try:
                if hasattr(v, "gender") and gender in v.gender.lower():
                    self.engine.setProperty('voice', v.id)
                    found = True
                    break
            except:
                continue
        if not found:
            if gender == "female":
                self.engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
            else:
                self.engine.setProperty('voice', voices[0].id)
        self.voice_gender = gender
    def speak(self, text):
        self._stop_flag.clear()
        self.q.put(text)
        if not self.isRunning():
            self.start()
    def run(self):
        self._running = True
        while not self.q.empty() and not self._stop_flag.is_set():
            text = self.q.get()
            with self.lock:
                self.engine.say(clean_for_speech(text))
                try:
                    self.engine.runAndWait()
                except Exception:
                    pass
            if self._stop_flag.is_set():
                break
        self._running = False
        self.finished.emit()
    def stop_speaking(self):
        self._stop_flag.set()
        try:
            self.engine.stop()
        except Exception:
            pass

class VoiceThread(QThread):
    result = pyqtSignal(str)
    def run(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                audio = r.listen(source, phrase_time_limit=5)
            try:
                text = r.recognize_google(audio, language="en-US")
                self.result.emit(text)
            except Exception:
                self.result.emit("")
        except Exception:
            self.result.emit("")

def animate_widget(widget, property_name, start_value, end_value, duration=400):
    anim = QPropertyAnimation(widget, property_name.encode())
    anim.setDuration(duration)
    anim.setStartValue(start_value)
    anim.setEndValue(end_value)
    anim.start()
    return anim

def detect_sentiment(text):
    text = text.strip().lower()
    if not text:
        return 'neutral'
    happy_words = ["happy", "great", "awesome", "good", "fantastic", "excellent", "yes boss", "perfect"]
    sad_words = ["sad", "sorry", "bad", "unfortunately", "can't", "cannot", "error", "fail"]
    surprise_words = ["wow", "amazing", "incredible", "unbelievable", "really?"]
    if any(e in text for e in ['😂', '😁', '😄', '😃', '😊', '🙂', '😸', '😎', '😍', '🥰']):
        return 'happy'
    if any(e in text for e in ['😔', '😢', '😭', '😞', '☹', '🙁', '😩', '😫']):
        return 'sad'
    if any(w in text for w in happy_words):
        return 'happy'
    if any(w in text for w in sad_words):
        return 'sad'
    if any(w in text for w in surprise_words):
        return 'surprised'
    return 'neutral'

class ListeningWaveform(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(70)
        self.amplitudes = [random.uniform(0.4, 1.0) for _ in range(36)]
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.setVisible(False)
    def start(self):
        self.setVisible(True)
        self.timer.start(38)
    def stop(self):
        self.setVisible(False)
        self.timer.stop()
    def animate(self):
        self.phase += 0.18
        for i in range(len(self.amplitudes)):
            self.amplitudes[i] = 0.9 + 0.6 * math.sin(self.phase + i * 0.19 + random.uniform(-0.07, 0.07))
        self.update()
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        n = len(self.amplitudes)
        y_center = int(h * 0.44)
        amp = int(h * 0.33)
        for glow in range(8, 1, -2):
            qp.setPen(QPen(QColor(80, 190, 255, int(13*glow)), glow, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            self._draw_wave(qp, w, n, y_center, amp * (1+glow/18))
        qp.setPen(QPen(QColor(70, 200, 255, 180), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        self._draw_wave(qp, w, n, y_center, amp)
        qp.setPen(QPen(QColor(222, 77, 255, 120), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        self._draw_wave(qp, w, n, y_center, amp*0.77)
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        qp.setFont(font)
        x = w//2 - 65
        y = int(h*0.91)
        for d in range(5, 1, -1):
            qp.setPen(QPen(QColor(70, 225, 255, 18*d), d*3))
            qp.drawText(x, y, "Listening")
        qp.setPen(QColor("#23d8fc"))
        qp.drawText(x, y, "Listening")
    def _draw_wave(self, qp, w, n, y_center, amp):
        pts = []
        for i in range(n):
            x = int(i * w / (n-1))
            y = int(y_center + self.amplitudes[i] * math.sin(i * 0.19 + self.phase*1.25) * amp * (0.98 + 0.02 * math.sin(self.phase + i)))
            pts.append((x, y))
        for i in range(n-1):
            qp.drawLine(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

class AvatarAnimation(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setFixedHeight(82)
        self.emotion = 'neutral'
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.repaint)
        self.pulse_timer.start(170)
        self.glow_phase = 0
    def set_emotion(self, emotion):
        self.emotion = emotion
        self.repaint()
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        self.glow_phase += 0.18
        for r in range(42, 24, -2):
            qp.setPen(Qt.PenStyle.NoPen)
            glow_alpha = 48 + 13 * (r-24)
            if self.emotion == 'happy':
                qp.setBrush(QColor(98, 232, 255, glow_alpha))
            elif self.emotion == 'sad':
                qp.setBrush(QColor(232, 119, 172, glow_alpha))
            elif self.emotion == 'surprised':
                qp.setBrush(QColor(255, 233, 72, glow_alpha))
            else:
                qp.setBrush(QColor(133, 145, 255, glow_alpha))
            qp.drawEllipse(w//2-r//2, h//2-r//2-4, r, r)
        qp.setBrush(QColor(38, 40, 60) if self.emotion=='neutral' else
                    QColor(90, 244, 255) if self.emotion=='happy' else
                    QColor(248, 140, 180) if self.emotion=='sad' else
                    QColor(255, 233, 110))
        qp.setPen(QPen(QColor(42,64,134), 2))
        qp.drawEllipse(w//2-20, h//2-20-3, 40, 40)
        qp.setBrush(QColor(0,0,0))
        qp.setPen(Qt.PenStyle.NoPen)
        qp.drawEllipse(w//2-10, h//2-7, 5, 6)
        qp.drawEllipse(w//2+5, h//2-7, 5, 6)
        qp.setPen(QPen(QColor(0,0,0),2))
        if self.emotion=='happy':
            qp.drawArc(w//2-7, h//2+3, 14, 8, 0, 180*16)
        elif self.emotion=='sad':
            qp.drawArc(w//2-7, h//2+10, 14, 8, 180*16, 180*16)
        elif self.emotion=='surprised':
            qp.drawEllipse(w//2-4, h//2+7, 9, 9)
        else:
            qp.drawArc(w//2-7, h//2+6, 14, 8, 0, 180*16)

HOTWORDS = ["hey deo", "computer"]

class HotwordThread(QThread):
    hotword_detected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
    def run(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        while self.running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                if not self.running:
                    break
                try:
                    text = recognizer.recognize_google(audio, language="en-US").lower()
                    for word in HOTWORDS:
                        if word in text:
                            self.hotword_detected.emit(word)
                            self.running = False
                            return
                except:
                    pass
            except:
                pass
    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class ModernDEO(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DEO — Liquid Glass AI")
        self.setGeometry(300, 100, 560, 680)
        self.dark_mode = True
        self.locked = False
        self.history = []
        self.speech_manager = None

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # ---- Voice এবং Theme বাটন এক Row-এ ----
        mode_row = QHBoxLayout()
        mode_row.addStretch(1)
        # ---- Voice Toggle Button (শুধু emoji + কাস্টম স্টাইল) ----
        self.voice_gender = "male"  # default
        self.voice_toggle_btn = QPushButton("🙎‍♂️")
        self.voice_toggle_btn.setFont(QFont("Segoe UI Emoji", 19))
        self.voice_toggle_btn.setFixedWidth(45)
        self.voice_toggle_btn.clicked.connect(self.toggle_voice)
        self.voice_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #34e3e3;
                padding: 0px;
            }
            QPushButton:hover {
                color: #ffd966;
            }
        """)
        mode_row.addWidget(self.voice_toggle_btn)  # আগে Voice, পরে Theme

        # ---- Theme Switch Button ----
        self.mode_btn = QPushButton("🌙")
        self.mode_btn.setFont(QFont("Segoe UI Emoji", 16))
        self.mode_btn.setFixedWidth(44)
        self.mode_btn.setStyleSheet("""
            QPushButton {background: transparent; border: none; color: #34e3e3;}
            QPushButton:hover { color: #ffd966; }
        """)
        self.mode_btn.clicked.connect(self.toggle_mode)
        mode_row.addWidget(self.mode_btn)

        main_layout.addLayout(mode_row)
        # ------------------------------------------------

        self.avatar = AvatarAnimation()
        main_layout.addWidget(self.avatar)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        main_layout.addWidget(self.chat)

        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        self.input.setPlaceholderText("Type or speak to DEO…")
        self.input.returnPressed.connect(self.send)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.send_btn.clicked.connect(self.send)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFont(QFont("Segoe UI Emoji", 19))
        self.voice_btn.setFixedWidth(45)
        self.voice_btn.clicked.connect(self.listen_voice)

        input_layout.addWidget(self.input)
        input_layout.addWidget(self.voice_btn)
        input_layout.addWidget(self.send_btn)
        main_layout.addLayout(input_layout)

        self.status = QLabel("")
        self.status.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        main_layout.addWidget(self.status)

        self.waveform = ListeningWaveform()
        main_layout.addWidget(self.waveform)
        self.waveform.setVisible(False)

        self.end_btn = QPushButton("End")
        self.end_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.end_btn.setStyleSheet("""
            QPushButton {
                background: #ff5656;
                color: #fff;
                border-radius: 12px;
                padding: 10px 30px;
                font-weight: bold;
                letter-spacing: 1.1px;
                border: none;
            }
            QPushButton:hover { background: #ff3131; }
        """)
        self.end_btn.setVisible(False)
        self.end_btn.clicked.connect(self.end_speech)
        main_layout.addWidget(self.end_btn)

        self.setLayout(main_layout)
        self.set_stylesheet()
        self.lock_ui(False)
        self.chat.setWindowOpacity(0.15)
        animate_widget(self.chat, "windowOpacity", 0.15, 1, duration=700)

        QTimer.singleShot(600, self.greet)

        # Hotword support
        self.hotword_thread = None
        self.resume_hotword()

    # ======= MALE/FEMALE SIMPLE BUTTON: UI FUNCTION =======
    def toggle_voice(self):
        if self.voice_gender == "male":
            self.voice_gender = "female"
            self.voice_toggle_btn.setText("🙎‍♀️")
        else:
            self.voice_gender = "male"
            self.voice_toggle_btn.setText("🙎‍♂️")

    # ... (বাকিটা একদম আগের মতো) ...

    def pause_hotword(self):
        if self.hotword_thread is not None:
            self.hotword_thread.stop()
            self.hotword_thread = None

    def resume_hotword(self):
        self.pause_hotword()
        self.hotword_thread = HotwordThread(self)
        self.hotword_thread.hotword_detected.connect(self.on_hotword_detected)
        self.hotword_thread.start()
        self.status.setText("Hotword listening...")

    def on_hotword_detected(self, hotword):
        self.status.setText(f"Hotword '{hotword}' detected. Listening...")
        self.pause_hotword()
        QTimer.singleShot(100, self.listen_voice)

    def greet(self):
        greeting = "Hi, I'm DEO! How can I help you?"
        self.history.append({'who': 'ai', 'msg': greeting})
        self.render_history()
        self.lock_ui(True)
        self.start_speech(greeting)
        self.avatar.set_emotion('happy')

    def set_stylesheet(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #161b22, stop:1 #232526);}
            """)
            self.chat.setStyleSheet("""
                QTextEdit {background: rgba(26,27,36,0.98); border-radius:22px; border:2px solid #2d384a; padding:20px; font-size:20px; color:#fff;}
            """)
            self.input.setStyleSheet("""
                QLineEdit {background:rgba(34,38,51,0.99); border-radius:14px; border:2px solid #344156; padding:12px; font-size:19px; color:#34e3e3;}
            """)
            self.status.setStyleSheet("""
                color:#34e3e3; padding:8px; letter-spacing:1.2px;
                font-size:18px; font-weight:bold; border-radius:12px;
            """)
            self.avatar.setStyleSheet("background: transparent;")
            self.voice_btn.setStyleSheet("""
                QPushButton {background:#23272e; border-radius:12px; font-size:21px; border:2px solid #233e54; color:#34e3e3;}
                QPushButton:hover { background: #34e3e3; color: #161b22;}
            """)
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #112b44, stop:1 #34e3e3);
                    color: #fff;
                    padding: 11px 24px;
                    border-radius: 15px;
                    border: none;
                    font-weight:bold;
                    letter-spacing:1px;
                }
                QPushButton:hover { background: #34e3e3; color: #232526;}
            """)
            self.mode_btn.setText("🌙")
        else:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(245,248,255,0.82);
                    border-radius:28px;
                }
            """)
            self.chat.setStyleSheet("""
                QTextEdit {
                    background: #f6fafd;
                    border-radius:24px;
                    border: 2px solid #bed6ef;
                    padding:18px;
                    font-size:20px;
                    color:#143057;
                }
            """)
            self.input.setStyleSheet("""
                QLineEdit {
                    background:#e8f1fc;
                    border-radius:14px;
                    border:2px solid #99c8f6;
                    padding:10px;
                    font-size:19px;
                    color:#123871;
                }
            """)
            self.status.setStyleSheet("""
                color: #2151a8;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e3edfa, stop:1 #b0ccff);
                font-size: 20px;
                font-weight: bold;
                padding: 11px 30px;
                border-radius: 19px;
                letter-spacing: 1.2px;
                border: 1.7px solid #7fa3e5;
            """)
            self.avatar.setStyleSheet("background: transparent; color:#1a60af;")
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background:#dbeafe;
                    border-radius:12px;
                    font-size:21px;
                    border:2px solid #99c8f6;
                    color:#1a60af;
                }
                QPushButton:hover { background: #b1d7fd; color: #fff;}
            """)
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e6ad3, stop:1 #9be4fd);
                    color: #fff;
                    padding: 14px 32px;
                    border-radius: 20px;
                    border: 2px solid #4db4fc;
                    font-weight: bold;
                    font-size: 19px;
                    letter-spacing: 1.2px;
                }
                QPushButton:hover { background: #143057; color: #9be4fd;}
            """)
            self.mode_btn.setText("☀️")
        self.render_history()

    def render_history(self):
        html = ""
        for item in self.history:
            user_color = "#34e3e3" if self.dark_mode else "#143057"
            ai_color = "#fff" if self.dark_mode else "#1a60af"
            if item['who'] == 'user':
                html += f'<span style="color:{user_color}; font-weight:bold; font-size:22px;">You: {item["msg"]}</span><br>'
            else:
                html += f'<span style="color:{ai_color}; font-weight:bold; font-size:22px;">DEO: {item["msg"]}</span><br>'
        self.chat.setHtml(html)
        self.chat.moveCursor(QTextCursor.MoveOperation.End)

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.set_stylesheet()

    def lock_ui(self, locked=True):
        self.input.setDisabled(locked)
        self.send_btn.setDisabled(locked)
        self.voice_btn.setDisabled(locked)
        self.locked = locked
        if locked:
            self.send_btn.setStyleSheet(self.send_btn.styleSheet() +
                "QPushButton {background: #ff4a54 !important; color: #fff !important;}")
        else:
            self.set_stylesheet()

    def send(self):
        if self.locked: return
        user_text = self.input.text().strip().lower()
        user_text = autocorrect_command(user_text)
        if user_text:
            self.history.append({'who': 'user', 'msg': user_text})
            self.input.clear()
            self.render_history()
            self.lock_ui(True)
            special_reply, handled = handle_special_commands(user_text, self)
            if handled:
                self.handle_ai_reply(special_reply)
                return
            self.gemini_thread = QThread()
            self.gemini_worker = GeminiWorker(user_text)
            self.gemini_worker.moveToThread(self.gemini_thread)
            self.gemini_thread.started.connect(self.gemini_worker.run)
            self.gemini_worker.finished.connect(self.handle_ai_reply)
            self.gemini_worker.error.connect(self.handle_ai_error)
            self.gemini_worker.finished.connect(self.gemini_thread.quit)
            self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
            self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
            self.gemini_worker.error.connect(self.gemini_thread.quit)
            self.gemini_worker.error.connect(self.gemini_worker.deleteLater)
            self.gemini_thread.start()

    def handle_ai_reply(self, ai_response):
        emotion = detect_sentiment(ai_response)
        self.avatar.set_emotion(emotion)
        self.history.append({'who': 'ai', 'msg': ai_response})
        self.render_history()
        self.end_btn.setVisible(True)
        self.start_speech(ai_response)
        animate_widget(self.chat, "windowOpacity", 0.7, 1, duration=300)

    def handle_ai_error(self, error_msg):
        self.avatar.set_emotion('sad')
        self.history.append({'who': 'ai', 'msg': error_msg})
        self.render_history()
        self.lock_ui(False)

    def on_speech_done(self):
        self.end_btn.setVisible(False)
        self.lock_ui(False)
        self.avatar.set_emotion('neutral')
        self.speech_manager = None
        self.resume_hotword()

    def start_speech(self, text):
        if self.speech_manager:
            self.speech_manager.stop_speaking()
            self.speech_manager = None
        self.speech_manager = SpeechManager()
        self.speech_manager.set_gender(self.voice_gender)
        self.speech_manager.finished.connect(self.on_speech_done)
        self.speech_manager.speak(text)

    def listen_voice(self):
        if self.locked:
            return
        self.status.setText("")
        self.lock_ui(True)
        self.waveform.start()
        self.voice_thread = VoiceThread()
        self.voice_thread.result.connect(self.voice_done)
        self.voice_thread.start()

    def voice_done(self, text):
        self.status.setText("")
        self.waveform.stop()
        text = text.strip().lower()
        text = autocorrect_command(text)
        if text:
            self.input.setText(text)
            self.lock_ui(False)
            self.send()
        else:
            self.lock_ui(False)
        self.resume_hotword()

    def end_speech(self):
        if self.speech_manager:
            self.speech_manager.stop_speaking()
        self.end_btn.setVisible(False)
        self.lock_ui(False)
        self.resume_hotword()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 15))
    window = ModernDEO()
    window.show()
    sys.exit(app.exec())