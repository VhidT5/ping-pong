from pygame import *
import socket
import json
from threading import Thread
import os
import sys

# ---PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

font_title = font.Font(None, 64)
font_button = font.Font(None, 36)
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)
font_small = font.Font(None, 24)

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# === ЗАВАНТАЖЕННЯ ЗВУКІВ ===
def load_sound_safe(path, volume=0.5):
    try:
        sound = mixer.Sound(path)
        sound.set_volume(volume)
        return sound
    except Exception as e:
        print(f"⚠️ Не вдалося завантажити звук {path}: {e}")
        return None

def load_music_safe(path, volume=0.3):
    try:
        mixer.music.load(path)
        mixer.music.set_volume(volume)
        return True
    except Exception as e:
        print(f"⚠️ Не вдалося завантажити фонову музику {path}: {e}")
        return False

print("🔊 Завантажую звуки...")

paddle_hit_sound = load_sound_safe('audio/bounce.mp3', 1)
wall_hit_sound = load_sound_safe('audio/bounce.mp3', 1)
menu_click_sound = load_sound_safe('audio/')
win_sound = load_sound_safe('audio/won.mp3', 0.7)
lose_sound = load_sound_safe('audio/lose.mp3', 0.7)

background_music_loaded = load_music_safe('audio/bg_music.mp3', 0.1)
music_playing = False

# === ЗАВАНТАЖЕННЯ ЗОБРАЖЕНЬ ===
def load_image_safe(path, size=None):
    try:
        img = image.load(path)
        if size:
            img = transform.scale(img, size)
        return img.convert_alpha()
    except:
        print(f"⚠️ Не вдалося завантажити {path}")
        return None

print("🎨 Завантажую зображення...")

game_bg = load_image_safe('images/backgrounds/BG.png', (WIDTH, HEIGHT))
win_bg = load_image_safe('images/backgrounds/win bg.png', (WIDTH, HEIGHT))
menu_bg = load_image_safe('images/backgrounds/menu_bg.png', (WIDTH, HEIGHT))
settings_bg = load_image_safe('images/backgrounds/menu.png', (WIDTH, HEIGHT))

if game_bg is None:
    try:
        game_bg = image.load('bg.jpg')
        game_bg = transform.scale(game_bg, (WIDTH, HEIGHT))
    except:
        print("⚠️ Фонове зображення не знайдено")
        game_bg = None

ball_img = load_image_safe('images/game_elements/ping-ball.png', (50, 50))
paddle1_img = load_image_safe('images/game_elements/paddle.png', (70, 130))
paddle2_img = load_image_safe('images/game_elements/shield.png', (70, 130))

print("✅ Завантаження зображень завершено!")

# === ФУНКЦІЇ ДЛЯ РОБОТИ З МУЗИКОЮ ===
def start_background_music():
    global music_playing
    if background_music_loaded and sound_enabled and not music_playing:
        try:
            mixer.music.play(-1)
            music_playing = True
            print("🎵 Фонова музика запущена")
        except Exception as e:
            print(f"⚠️ Помилка запуску фонової музики: {e}")

def stop_background_music():
    global music_playing
    if music_playing:
        mixer.music.stop()
        music_playing = False
        print("🎵 Фонова музика зупинена")

def play_sound_effect(sound):
    if sound and sound_enabled:
        try:
            sound.play()
        except Exception as e:
            print(f"⚠️ Помилка відтворення звуку: {e}")

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect=Rect(x, y, width, height)
        self.text=text
        self.action=action
        self.hovered=False

    def draw(self, screen):
        if self.hovered:
            color=(70,130,180)
            text_color=(255,255,255)
        else:
            color=(50,50,100)
            text_color=(200,200,200)

        draw.rect(screen,color,self.rect)
        draw.rect(screen, (255,255,255), self.rect, 2)
# === НАЛАШТУВАННЯ ГРИ ===
SERVER_IP = "localhost"
SERVER_PORT = 8080
sound_enabled = True

# === МЕРЕЖЕВІ ФУНКЦІЇ ===
def connect_to_server():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        buffer = ""
        game_state = {}
        my_id = int(client.recv(24).decode())
        return my_id, game_state, buffer, client
    except Exception as e:
        print(f"❌ Помилка підключення: {e}")
        return None

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# === ОСНОВНИЙ ІГРОВИЙ ЦИКЛ ===
game_over = False
you_winner = None
my_id = None
game_state = {}
buffer = ""
client = None
connecting = True
connection_attempts = 0

# Запуск фонової музики
start_background_music()

print("🎮 Підключення до сервера...")

while True:
    for e in event.get():
        if e.type == QUIT:
            stop_background_music()
            exit()

    # === ЕКРАН ПІДКЛЮЧЕННЯ ===
    if connecting:
        if game_bg:
            screen.blit(game_bg, (0, 0))
        else:
            screen.fill((30, 30, 30))

        connecting_text = font.Font(None, 64).render("Підключення...", True, (255, 255, 255))
        connecting_rect = connecting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(connecting_text, connecting_rect)

        hint_text = font_main.render("Очікування з'єднання з сервером", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(hint_text, hint_rect)

        display.update()

        # Спроба підключення
        connection_attempts += 1
        if connection_attempts > 60:
            connection_attempts = 0
            result = connect_to_server()
            if result:
                my_id, game_state, buffer, client = result
                connecting = False
                game_over = False
                you_winner = None
                Thread(target=receive, daemon=True).start()
                print("✅ Успішно підключено до сервера!")

    # === ІГРОВА ЛОГІКА ===
    else:
        if game_bg:
            screen.blit(game_bg, (0, 0))
        else:
            screen.fill((30, 30, 30))

        # Екран відліку
        if "countdown" in game_state and game_state["countdown"] > 0:
            countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
            screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
            display.update()
            clock.tick(60)
            continue

        # Екран перемоги
        if "winner" in game_state and game_state["winner"] is not None:
            if win_bg:
                screen.blit(win_bg, (0, 0))
            else:
                screen.fill((20, 20, 20))

            if you_winner is None:
                if game_state["winner"] == my_id:
                    you_winner = True
                    play_sound_effect(win_sound)
                else:
                    you_winner = False
                    play_sound_effect(lose_sound)

            if you_winner:
                text = "Ти переміг!"
            else:
                text = "Пощастить наступним разом!"

            win_text = font_win.render(text, True, (255, 215, 0))
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, text_rect)

            display.update()
            clock.tick(60)
            continue

        # Основна гра
        if game_state:
            # Ракетки
            if paddle1_img:
                screen.blit(paddle1_img, (20, game_state['paddles']['0']))
            else:
                draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))

            if paddle2_img:
                screen.blit(paddle2_img, (WIDTH - 40, game_state['paddles']['1']))
            else:
                draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))

            # М'яч
            if ball_img:
                screen.blit(ball_img, (game_state['ball']['x'] - 10, game_state['ball']['y'] - 10))
            else:
                draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)

            # Рахунок
            score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True,
                                          (255, 255, 255))
            screen.blit(score_text, (WIDTH // 2 - 25, 20))

            # Звукові події
            if game_state.get('sound_event') and sound_enabled:
                if game_state['sound_event'] == 'wall_hit':
                    play_sound_effect(wall_hit_sound)
                if game_state['sound_event'] == 'platform_hit':
                    play_sound_effect(paddle_hit_sound)
        else:
            # Екран очікування
            waiting_text = font_main.render("Очікування гравців...", True, (255, 255, 255))
            screen.blit(waiting_text, (WIDTH // 2 - 125, HEIGHT // 2))

        # Управління
        keys = key.get_pressed()
        if keys[K_w] and client:
            try:
                client.send(b"UP")
            except:
                print("❌ З'єднання втрачено")
                stop_background_music()
                exit()
        elif keys[K_s] and client:
            try:
                client.send(b"DOWN")
            except:
                print("❌ З'єднання втрачено")
                stop_background_music()
                exit()

    display.update()
    clock.tick(60)