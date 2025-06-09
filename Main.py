import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import requests
import configparser
import threading
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CONFIG_PATH = os.path.join(ASSETS_DIR, "twitch.config.ini")
BG_IMAGE_PATH = os.path.join(ASSETS_DIR, "afk.png")

# Twitch API
class TwitchAPI:
    def __init__(self, client_id, access_token, user_login):
        self.client_id = client_id
        self.access_token = access_token
        self.user_login = user_login
        self.headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
        self.api_url = "https://api.twitch.tv/helix/streams"

    def get_stream_info(self):
        params = {"user_login": self.user_login}
        try:
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json().get("data", [])
            if data:
                stream = data[0]
                return {
                    "is_live": True,
                    "viewer_count": stream.get("viewer_count", 0),
                    "title": stream.get("title", "No Title")
                }
            else:
                return {"is_live": False}
        except Exception as e:
            return {"is_live": False, "error": str(e)}

# GUI
class AfkScreen:
    def __init__(self, root, twitch_api):
        self.root = root
        self.twitch_api = twitch_api
        self.root.title("main.py - AFK Screen")
        self.root.geometry("800x450")
        self.root.resizable(False, False)

        # Bg
        self.bg_image = Image.open(BG_IMAGE_PATH)
        self.bg_image = self.bg_image.resize((800, 450), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.canvas = tk.Canvas(root, width=800, height=450)
        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # fonts
        self.title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self.status_font = font.Font(family="Segoe UI", size=14)
        self.afk_font = font.Font(family="Segoe UI", size=16, slant="italic")

        # Twitch Status
        self.status_text = self.canvas.create_text(400, 50, text="Loading Twitch Data...", fill="white", font=self.title_font)

        # Viewer Count & Title
        self.viewer_text = self.canvas.create_text(400, 90, text="", fill="white", font=self.status_font)
        self.title_text = self.canvas.create_text(400, 130, text="", fill="white", font=self.status_font, width=700)

        # AFK Reason
        self.afk_reason_var = tk.StringVar()
        self.afk_reason_var.set("Afk because of...")

        self.afk_entry = tk.Entry(root, textvariable=self.afk_reason_var, font=self.afk_font, width=50, justify="center")
        self.afk_entry.place(x=100, y=400)

        # Refresh
        self.refresh_button = tk.Button(root, text="refresh", command=self.update_stream_status)
        self.refresh_button.place(x=350, y=360)

        # auto refresh
        self.running = True
        self.update_thread = threading.Thread(target=self.auto_update, daemon=True)
        self.update_thread.start()

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.running = False
        self.root.destroy()

    def update_stream_status(self):
        info = self.twitch_api.get_stream_info()
        if info.get("is_live"):
            status = "🔴 Live on Twitch!"
            viewer = f"viewer: {info.get('viewer_count', 0)}"
            title = f"{info.get('title', 'Kein Titel')}"
        else:
            status = "⚪️ You are Offline..."
            viewer = "Go online to see your viewers"
            title = "Untitled Stream"

        # Update text
        self.canvas.itemconfig(self.status_text, text=status)
        self.canvas.itemconfig(self.viewer_text, text=viewer)
        self.canvas.itemconfig(self.title_text, text=title)

    def auto_update(self):
        while self.running:
            self.update_stream_status()
            time.sleep(5)  # refresh all 5 seconds

def main():
    # Twitch config
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    try:
        client_id = config["Twitch"]["client_id"]
        access_token = config["Twitch"]["access_token"]
        user_login = config["Twitch"]["user_login"]
    except KeyError:
        print("Bitte fülle die twitch.config.ini korrekt aus!")
        return

    twitch_api = TwitchAPI(client_id, access_token, user_login)

    root = tk.Tk()
    app = AfkScreen(root, twitch_api)
    root.mainloop()

if __name__ == "__main__":
    main()
