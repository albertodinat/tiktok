import os
import shutil
import math
import random
from pathlib import Path
import glob
import numpy as np
from PIL import Image
import pygame
import moviepy.editor as mpy
from moviepy.audio.AudioClip import AudioClip
import requests
import cv2
import matplotlib.pyplot as plt

# =========================
# Configuration centralisée
# =========================
class Config:
    WIDTH, HEIGHT = 720, 1280
    FPS = 50
    DURATION = 10
    TITLE_DURATION = 2
    OUTPUT_FILE = "speed_vs_messi_viral.mp4"
    FRAMES_DIR = Path("frames_tmp")
    COLORS = {
        'background': (15, 15, 35),
        'p1': (255, 100, 100),
        'p2': (100, 100, 255),
        'text': (255, 255, 255),
        'accent': (255, 215, 0)
    }
    # Effets visuels
    HALO = True
    ZOOM = True
    SHAKE = True
    FLASH = True
    PARTICLE_BOOST = True
    COLORFUL_PARTICLES = True
    SCORE_PULSE = True
    ULTRA_FAST = True
    SHAKE_INTENSITY = 18
    FLASH_INTENSITY = 180
    SCORE_FLASH_DURATION = 12
    WIN_SCORE = 10

CFG = Config()

# =========================
# Utilitaires images et polices
# =========================
def find_two_images():
    imgs = sorted(glob.glob("*.png"))
    if len(imgs) < 2:
        raise FileNotFoundError("Il faut au moins deux images PNG dans le dossier !")
    return imgs[:2]

def download_wikimedia_image(query, filename):
    """Essaye plusieurs variantes de recherche sur Wikimedia Commons pour maximiser les chances de trouver une image."""
    variants = [query, query + " portrait", query + " football", query + " face", query.split()[0]]
    for v in variants:
        url = (
            "https://commons.wikimedia.org/w/api.php?"
            "action=query&format=json&prop=imageinfo&generator=search&gsrsearch="
            + requests.utils.quote(v) +
            "&gsrlimit=1&iiprop=url"
        )
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            pages = data.get('query', {}).get('pages', {})
            for page in pages.values():
                if 'imageinfo' in page:
                    img_url = page['imageinfo'][0]['url']
                    img_data = requests.get(img_url, timeout=10).content
                    with open(filename, 'wb') as f:
                        f.write(img_data)
                    return True
        except Exception as e:
            continue
    return False

def download_unsplash_image(query, filename):
    """Télécharge une image portrait depuis Unsplash (requête simple, pas besoin de clé)."""
    try:
        url = f"https://source.unsplash.com/400x400/?{requests.utils.quote(query + ',portrait,face') }"
        img_data = requests.get(url, timeout=10).content
        with open(filename, 'wb') as f:
            f.write(img_data)
        return True
    except Exception as e:
        return False

# --- LISTES SÉPARÉES HOMMES/FEMMES ---
HOMMES = [
    "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappe", "Neymar Jr", "Erling Haaland", "Karim Benzema", "Luka Modric", "Vinicius Junior", "Robert Lewandowski", "Mohamed Salah", "Antoine Griezmann", "Paulo Dybala", "Sergio Ramos", "Kevin De Bruyne", "Harry Kane", "LeBron James", "Stephen Curry", "Giannis Antetokounmpo", "Novak Djokovic", "Rafael Nadal", "Roger Federer", "Conor McGregor", "Khabib Nurmagomedov", "Mike Tyson", "Floyd Mayweather", "Usain Bolt", "Lewis Hamilton", "Michael Jordan", "IShowSpeed", "Ninja gamer", "xQc", "PewDiePie", "Squeezie", "MrBeast", "Dream Minecraft", "Markiplier", "Ludwig Ahgren", "SypherPK", "TimTheTatman", "TommyInnit", "Drake", "Travis Scott", "The Weeknd", "Eminem", "Kanye West", "Justin Bieber", "Ed Sheeran", "Post Malone", "Logan Paul", "Jake Paul", "Elon Musk", "Jeff Bezos", "Mark Zuckerberg", "Donald Trump", "Vladimir Putin", "Jordan Peterson", "Joe Rogan", "Ben Shapiro", "Spider Man", "Iron Man", "Captain America", "Batman", "Superman", "Deadpool", "Thanos", "Black Panther", "Naruto Uzumaki", "Sasuke Uchiha", "Son Goku", "Vegeta", "Monkey D Luffy", "Roronoa Zoro", "Eren Yeager", "Levi Ackerman", "Saitama One Punch Man", "Gojo Satoru", "Tanjiro Kamado", "Light Yagami", "L Death Note", "Shinji Ikari", "Noah Beck", "Brent Rivera", "Mr Fresh Asian", "Brent Faiyaz", "Harry Styles", "BTS Jungkook", "BTS Jimin", "BTS V Taehyung", "Maluma", "Cristiano Ronaldo Jr", "Lionel Messi Jr", "Barack Obama", "Prince Harry", "Zayn Malik", "Mario Nintendo", "Luigi Nintendo", "Sonic the Hedgehog", "Knuckles Sonic", "Tails Sonic", "Lara Croft", "Master Chief Halo", "Kratos God of War", "Atreus God of War", "Link Legend of Zelda", "Ganondorf Zelda", "Will Smith", "Chris Rock", "Keanu Reeves", "Jason Momoa", "David Schwimmer", "Zlatan Ibrahimovic", "Andrea Pirlo", "Francesco Totti", "Ronaldinho", "David Beckham", "Eden Hazard", "Mesut Ozil", "Alexis Sanchez", "Canelo Alvarez", "Tyson Fury"
]
FEMMES = [
    "Serena Williams", "Naomi Osaka", "Pokimane", "Amouranth", "Valkyrae", "Taylor Swift", "Beyonce", "Rihanna", "Billie Eilish", "Doja Cat", "Dua Lipa", "Olivia Rodrigo", "Zendaya", "Scarlett Johansson", "Margot Robbie", "Jennifer Lawrence", "Anne Hathaway", "Greta Thunberg", "Amber Heard", "Wonder Woman", "Nezuko Kamado", "Charli DAmelio", "Addison Rae", "Bella Poarch", "Khaby Lame", "Loren Gray", "Avani Gregg", "Dixie DAmelio", "Nikkie Tutorials", "James Charles", "Shakira", "Adele", "Ariana Grande", "Cardi B", "Nicki Minaj", "Lisa Blackpink", "Jennie Blackpink", "Rose Blackpink", "Jisoo Blackpink", "Anitta", "Oprah Winfrey", "Michelle Obama", "Meghan Markle", "Kim Kardashian", "Kylie Jenner", "Kendall Jenner", "Gigi Hadid", "Bella Hadid", "Paris Hilton", "Selena Gomez", "Princess Peach", "Zelda Princess", "Samus Aran", "Jada Pinkett Smith", "Gal Gadot", "Millie Bobby Brown", "Sadie Sink", "Courteney Cox", "Lisa Kudrow", "Matt LeBlanc", "Naomi Scott", "Emma Watson", "Emma Stone", "Florence Pugh", "Natalie Portman", "Jessica Alba", "Eva Mendes", "Mila Kunis", "Kate Winslet", "Angelina Jolie", "Reese Witherspoon", "Julia Roberts", "Sandra Bullock", "Anne Curtis", "Priyanka Chopra", "Deepika Padukone", "Alia Bhatt", "Kriti Sanon", "Anushka Sharma", "Halle Berry", "Monica Bellucci", "Salma Hayek", "Penelope Cruz", "Cameron Diaz", "Kristen Stewart", "Kirsten Dunst", "Dakota Johnson", "Lily Collins", "Sofia Vergara", "Megan Fox", "Halsey", "Katy Perry", "Ellie Goulding", "Charli XCX", "Camila Cabello", "Lauren Jauregui", "Normani", "Becky G", "Tini Stoessel", "Madison Beer", "Hailee Steinfeld", "Lana Del Rey", "Kacey Musgraves", "Sabrina Carpenter"
]

# --- DEMANDE DES NOMS ET TÉLÉCHARGEMENT AUTOMATIQUE ---
def get_or_download_images():
    img1, img2 = 'img1.png', 'img2.png'
    tried = set()
    for attempt in range(15):
        n1, n2 = random.sample(PERSONNALITIES, 2)
        if (n1, n2) in tried or (n2, n1) in tried:
            continue
        tried.add((n1, n2))
        ok1 = download_wikimedia_image(n1, img1)
        if not ok1:
            ok1 = download_unsplash_image(n1, img1)
        ok2 = download_wikimedia_image(n2, img2)
        if not ok2:
            ok2 = download_unsplash_image(n2, img2)
        # Si toujours rien, fallback avatar coloré
        if not ok1:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n1[0], fill=(255,255,255,255))
            im.save(img1)
            ok1 = True
        if not ok2:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n2[0], fill=(255,255,255,255))
            im.save(img2)
            ok2 = True
        if ok1 and ok2:
            return img1, img2, n1.upper(), n2.upper()
        else:
            print(f"⚠️  Impossible de trouver des images pour {n1} ou {n2}, nouvelle tentative...")
    raise RuntimeError("Aucune paire de personnalités avec images trouvée après 15 essais. Modifiez la liste ou vérifiez la connexion internet.")

# --- UTILISATION DES IMAGES AUTOMATIQUES ---
IMG1_PATH, IMG2_PATH, IMG1_NAME, IMG2_NAME = get_or_download_images()

pygame.init()
screen = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
clock = pygame.time.Clock()
FONT_LARGE  = pygame.font.SysFont(None, 120)
FONT_MEDIUM = pygame.font.SysFont(None, 80)
FONT_SMALL  = pygame.font.SysFont(None, 60)

def load_or_fallback(name, color):
    try:
        img = pygame.image.load(name).convert_alpha()
    except:
        img = pygame.Surface((80, 80), pygame.SRCALPHA)
        img.fill(color)
    return pygame.transform.smoothscale(img, (80, 80))

img1 = load_or_fallback(IMG1_PATH, CFG.COLORS['p1'])
img2 = load_or_fallback(IMG2_PATH, CFG.COLORS['p2'])

# =========================
# Système de particules
# =========================
class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.color = color
        self.life = 32
        self.max_life = 32
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.vy += 0.12
    def draw(self, surface):
        if self.life <= 0:
            return
        size = max(1, int(6 * (self.life / self.max_life)))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

# =========================
# Entités du jeu
# =========================
class Player:
    def __init__(self, x, y, img, color, name, cfg):
        self.cfg = cfg
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.img = img
        self.color = color
        self.name = name
        self.radius = 40
        self.score = 0
        self.particles = []
        self.special_ready = True
        self.special_cooldown = 0
        self.anim = 0
        self.power_boost = 1.0
    def auto_control(self, tick_mod):
        if tick_mod % 10 == 0:
            self.vel.x += random.uniform(-6, 6)
            self.vel.y += random.uniform(-6, 6)
            self.vel.x = max(-12, min(12, self.vel.x))
            self.vel.y = max(-12, min(12, self.vel.y))
        if tick_mod % 40 == 0 and random.random() < 0.18:
            self.special_attack()
    def special_attack(self):
        if self.special_ready and self.special_cooldown <= 0:
            self.special_ready = False
            self.special_cooldown = 40
            self.power_boost = 3.0
            for _ in range(32 if self.cfg.COLORFUL_PARTICLES else 20):
                color = tuple(random.randint(100,255) for _ in range(3)) if self.cfg.COLORFUL_PARTICLES else self.color
                self.particles.append(Particle(self.pos.x, self.pos.y, color))
            return True
        return False
    def update(self):
        self.vel *= 0.87
        self.pos += self.vel * self.power_boost * (1.7 if self.cfg.ULTRA_FAST else 1)
        self.pos.x = max(self.radius, min(self.cfg.WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(self.cfg.HEIGHT - self.radius, self.pos.y))
        if abs(self.vel.x) > 2 or abs(self.vel.y) > 2:
            color = tuple(random.randint(100,255) for _ in range(3)) if self.cfg.COLORFUL_PARTICLES else self.color
            for _ in range(2 if self.cfg.ULTRA_FAST else 1):
                self.particles.append(Particle(self.pos.x, self.pos.y, color))
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        elif not self.special_ready:
            self.special_ready = True
            self.power_boost = 1.0
        self.anim += 1
    def draw(self, surface, score_flash=False):
        for p in self.particles:
            p.draw(surface)
        # Halo lumineux
        if self.cfg.HALO:
            for i in range(6, 0, -1):
                alpha = max(10, 40 - i * 6)
                halo = pygame.Surface((self.radius*2.5, self.radius*2.5), pygame.SRCALPHA)
                pygame.draw.circle(halo, (*self.color, alpha), (self.radius, self.radius), int(self.radius*1.1 + i*2))
                surface.blit(halo, (self.pos.x - self.radius, self.pos.y - self.radius), special_flags=pygame.BLEND_RGBA_ADD)
        # Zoom/impulsion
        pulse = 1 + 0.22 * math.sin(self.anim * 0.5) if self.cfg.ZOOM else 1 + 0.08 * math.sin(self.anim * 0.25)
        scaled = pygame.transform.smoothscale(
            self.img, (int(80 * pulse), int(80 * pulse))
        )
        if self.special_cooldown > 30:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius + 10, 3)
        surface.blit(
            scaled,
            (self.pos.x - scaled.get_width() // 2, self.pos.y - scaled.get_height() // 2)
        )

class Ball:
    def __init__(self, x, y, cfg):
        self.cfg = cfg
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-8, 8), random.uniform(-8, 8))
        self.radius = 14
        self.color = cfg.COLORS['accent']
        self.trail = []
    def update(self):
        self.pos += self.vel * (1.6 if self.cfg.ULTRA_FAST else 1)
        if self.pos.x < self.radius or self.pos.x > self.cfg.WIDTH - self.radius:
            self.vel.x *= -1.18 if self.cfg.ULTRA_FAST else -1
        if self.pos.y < self.radius or self.pos.y > self.cfg.HEIGHT - self.radius:
            self.vel.y *= -1.18 if self.cfg.ULTRA_FAST else -1
        self.trail.append(self.pos.copy())
        if len(self.trail) > (22 if self.cfg.ULTRA_FAST else 10):
            self.trail.pop(0)
    def draw(self, surface):
        for i, p in enumerate(self.trail):
            size = max(2, int(self.radius * (i / len(self.trail)) * (1.7 if self.cfg.PARTICLE_BOOST else 1)))
            pygame.draw.circle(surface, self.color, (int(p.x), int(p.y)), size)
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

# =========================
# Jeu principal
# =========================
class Game:
    def __init__(self, cfg):
        self.cfg = cfg
        self.p1 = Player(cfg.WIDTH // 4, cfg.HEIGHT // 2, img1, cfg.COLORS['p1'], IMG1_NAME, cfg)
        self.p2 = Player(3 * cfg.WIDTH // 4, cfg.HEIGHT // 2, img2, cfg.COLORS['p2'], IMG2_NAME, cfg)
        self.ball = Ball(cfg.WIDTH // 2, cfg.HEIGHT // 2, cfg)
        self.frame_index = 0
        self.state = "playing"
        self.winner = None
        # Effets visuels
        self.shake_offset = [0, 0]
        self.flash_alpha = 0
        self.score_flash_timer = 0
        self.score_flash_color = (255,255,255)
    def check_collisions(self):
        for pl in [self.p1, self.p2]:
            if (self.ball.pos - pl.pos).length() < (pl.radius + self.ball.radius):
                direction = (self.ball.pos - pl.pos)
                if direction.length() == 0:
                    direction = pygame.Vector2(1, 0)
                direction = direction.normalize()
                self.ball.vel = direction * (28 if self.cfg.ULTRA_FAST else 15)
                pl.score += 1
                for _ in range(36 if self.cfg.COLORFUL_PARTICLES else 18):
                    color = tuple(random.randint(100,255) for _ in range(3)) if self.cfg.COLORFUL_PARTICLES else pl.color
                    pl.particles.append(Particle(self.ball.pos.x, self.ball.pos.y, color))
                pl.anim += 18
                if self.cfg.FLASH:
                    self.flash_alpha = self.cfg.FLASH_INTENSITY
                if self.cfg.SHAKE:
                    self.shake_offset[0] = random.randint(-self.cfg.SHAKE_INTENSITY,self.cfg.SHAKE_INTENSITY)
                    self.shake_offset[1] = random.randint(-self.cfg.SHAKE_INTENSITY,self.cfg.SHAKE_INTENSITY)
                self.score_flash_timer = self.cfg.SCORE_FLASH_DURATION
                self.score_flash_color = tuple(random.randint(180,255) for _ in range(3))
                # Effet sonore (si pygame.mixer dispo)
                try:
                    pygame.mixer.init()
                    beep = pygame.mixer.Sound(pygame.sndarray.make_sound(np.array([4096*math.sin(2.0*math.pi*440*x/44100) for x in range(0,4410)]).astype(np.int16)))
                    beep.play()
                except:
                    pass
    def update(self):
        self.frame_index += 1
        self.p1.auto_control(self.frame_index)
        self.p2.auto_control(self.frame_index)
        self.p1.update()
        self.p2.update()
        self.ball.update()
        self.check_collisions()
        if self.shake_offset[0] != 0 or self.shake_offset[1] != 0:
            self.shake_offset[0] = int(self.shake_offset[0]*0.7)
            self.shake_offset[1] = int(self.shake_offset[1]*0.7)
            if abs(self.shake_offset[0]) < 2: self.shake_offset[0]=0
            if abs(self.shake_offset[1]) < 2: self.shake_offset[1]=0
        if self.flash_alpha > 0:
            self.flash_alpha = int(self.flash_alpha*0.85)
        if self.score_flash_timer > 0:
            self.score_flash_timer -= 1
        if self.p1.score >= self.cfg.WIN_SCORE or self.p2.score >= self.cfg.WIN_SCORE:
            self.state = "game_over"
            self.winner = self.p1.name if self.p1.score >= self.cfg.WIN_SCORE else self.p2.name
    def draw_background(self, surface):
        for y in range(0, self.cfg.HEIGHT, 4):
            ratio = y / self.cfg.HEIGHT
            r = int(15 + 20 * ratio)
            g = int(15 + 30 * ratio)
            b = int(35 + 40 * ratio)
            pygame.draw.rect(surface, (r, g, b), (0, y, self.cfg.WIDTH, 4))
        for x in range(0, self.cfg.WIDTH, 50):
            pygame.draw.line(surface, (50, 50, 70), (x, 0), (x, self.cfg.HEIGHT), 1)
        for y in range(0, self.cfg.HEIGHT, 50):
            pygame.draw.line(surface, (50, 50, 70), (0, y), (self.cfg.WIDTH, y), 1)
    def draw_ui(self, surface):
        # Scores (pulse animé + flash couleur)
        s_pulse = 1.3 if self.cfg.SCORE_PULSE and self.p1.anim > 0 else 1.0
        m_pulse = 1.3 if self.cfg.SCORE_PULSE and self.p2.anim > 0 else 1.0
        s_col = self.score_flash_color if self.score_flash_timer > 0 else self.cfg.COLORS['p1']
        m_col = self.score_flash_color if self.score_flash_timer > 0 else self.cfg.COLORS['p2']
        s_score = pygame.transform.smoothscale(FONT_LARGE.render(f"{self.p1.score}", True, s_col), (int(120*s_pulse), int(120*s_pulse)))
        m_score = pygame.transform.smoothscale(FONT_LARGE.render(f"{self.p2.score}", True, m_col), (int(120*m_pulse), int(120*m_pulse)))
        surface.blit(s_score, (self.cfg.WIDTH // 4 - s_score.get_width() // 2, 100))
        surface.blit(m_score, (3 * self.cfg.WIDTH // 4 - m_score.get_width() // 2, 100))
        # Noms dynamiques
        s_name = FONT_MEDIUM.render(self.p1.name, True, self.cfg.COLORS['text'])
        m_name = FONT_MEDIUM.render(self.p2.name, True, self.cfg.COLORS['text'])
        surface.blit(s_name, (self.cfg.WIDTH // 4 - s_name.get_width() // 2, 50))
        surface.blit(m_name, (3 * self.cfg.WIDTH // 4 - m_name.get_width() // 2, 50))
        pygame.draw.line(surface, self.cfg.COLORS['text'], (self.cfg.WIDTH // 2, 0), (self.cfg.WIDTH // 2, self.cfg.HEIGHT), 3)
        # Titre overlay au début
        if self.frame_index < self.cfg.TITLE_DURATION * self.cfg.FPS:
            title1 = FONT_LARGE.render(f"{self.p1.name} vs {self.p2.name}", True, self.cfg.COLORS['accent'])
            title2 = FONT_MEDIUM.render("DUEL HYPNOTIQUE !", True, self.cfg.COLORS['text'])
            cx = self.cfg.WIDTH // 2
            cy = self.cfg.HEIGHT // 2
            surface.blit(title1, (cx - title1.get_width() // 2, cy - 100))
            surface.blit(title2, (cx - title2.get_width() // 2, cy - 10))
        # Game over overlay
        if self.state == "game_over":
            overlay = pygame.Surface((self.cfg.WIDTH, self.cfg.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))
            winner = FONT_LARGE.render(f"{self.winner} WINS!", True, self.cfg.COLORS['accent'])
            surface.blit(winner, (self.cfg.WIDTH // 2 - winner.get_width() // 2, self.cfg.HEIGHT // 2 - 80))
    def render_frame(self, surface):
        # Décalage shake
        if self.cfg.SHAKE and (self.shake_offset[0] or self.shake_offset[1]):
            temp = pygame.Surface((self.cfg.WIDTH, self.cfg.HEIGHT))
            self.draw_background(temp)
            self.ball.draw(temp)
            self.p1.draw(temp)
            self.p2.draw(temp)
            self.draw_ui(temp)
            surface.blit(temp, (self.shake_offset[0], self.shake_offset[1]))
        else:
            self.draw_background(surface)
            self.ball.draw(surface)
            self.p1.draw(surface)
            self.p2.draw(surface)
            self.draw_ui(surface)
        # Flash d'écran
        if self.cfg.FLASH and self.flash_alpha > 0:
            flash = pygame.Surface((self.cfg.WIDTH, self.cfg.HEIGHT), pygame.SRCALPHA)
            flash.fill((255,255,255,self.flash_alpha))
            surface.blit(flash, (0,0))

# =========================
# Audio : musique auto (beat synthé)
# =========================
def make_music(t_array):
    bpm = 120.0
    beat_t = 60.0 / bpm
    t = t_array
    kick_env = np.exp(-t % beat_t * 12.0)
    kick = np.sin(2 * np.pi * 50 * t) * kick_env
    beat_idx = np.floor((t / beat_t) % 4)
    snare_gate = ((beat_idx == 1) | (beat_idx == 3)).astype(float)
    snare = snare_gate * (np.random.uniform(-1, 1, size=t.shape) * np.exp(-((t % beat_t) * 20)))
    hat_gate = ((np.floor((t / (beat_t / 2)) % 2)) == 0).astype(float)
    hat = hat_gate * (np.random.uniform(-1, 1, size=t.shape) * 0.3) * np.exp(-((t % (beat_t / 2)) * 40))
    note_period = 2.0
    note_idx = np.floor(t / note_period) % 4
    freqs = np.array([55, 65.4, 73.4, 82.4])
    f = freqs[note_idx.astype(int)]
    bass = 0.2 * np.sin(2 * np.pi * f * t) * np.exp(-((t % note_period) * 0.6))
    mix = kick * 0.8 + snare * 0.5 + hat * 0.3 + bass * 0.9
    mix = np.tanh(mix * 1.5).astype(np.float32)
    return mix

def music_frame(t):
    if np.isscalar(t):
        t = np.array([t], dtype=np.float32)
    return make_music(t)

# =========================
# Pipeline rendu (frames -> PNG -> vidéo)
# =========================
def render_video():
    if CFG.FRAMES_DIR.exists():
        shutil.rmtree(CFG.FRAMES_DIR)
    CFG.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    game = Game(CFG)
    total_frames = int(CFG.DURATION * CFG.FPS)
    print("🎮 Génération en cours...")
    for i in range(total_frames):
        game.update()
        game.render_frame(screen)
        frame_array = pygame.surfarray.array3d(screen)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        frame_path = CFG.FRAMES_DIR / f"frame_{i:05d}.png"
        Image.fromarray(frame_array).save(frame_path, "PNG")
        if i % max(1, total_frames // 10) == 0:
            pct = (i / total_frames) * 100
            print(f"📊 Progression: {pct:.0f}%")
    print("🎬 Assemblage de la vidéo...")
    frame_files = [str(p) for p in sorted(CFG.FRAMES_DIR.iterdir()) if p.suffix.lower() == ".png"]
    clip = mpy.ImageSequenceClip(frame_files, fps=CFG.FPS)
    audio = AudioClip(lambda t: music_frame(t), duration=CFG.DURATION, fps=44100)
    clip = clip.set_audio(audio)
    clip.write_videofile(
        CFG.OUTPUT_FILE,
        codec="libx264",
        audio_codec="aac",
        fps=CFG.FPS,
        threads=4
    )
    try:
        shutil.rmtree(CFG.FRAMES_DIR)
    except Exception:
        pass
    print(f"✅ Vidéo créée : {CFG.OUTPUT_FILE}")
    print("🚀 Prêt pour TikTok / Shorts / Reels.")

def blend_images(img_path1, img_path2, out_path):
    from PIL import Image
    im1 = Image.open(img_path1).convert('RGBA').resize((400,400))
    im2 = Image.open(img_path2).convert('RGBA').resize((400,400))
    blended = Image.blend(im1, im2, alpha=0.5)
    blended.save(out_path)
    return blended

def fusion_children_mode():
    couples = []
    used = set()
    while len(couples) < 10:
        h = random.choice(HOMMES)
        f = random.choice(FEMMES)
        if (h, f) in used:
            continue
        used.add((h, f))
        couples.append((h, f))
    children_paths = []
    for idx, (n1, n2) in enumerate(couples, 1):
        print(f"\n👩‍❤️‍👨 Couple {idx}: {n1} + {n2}")
        img1, img2 = f"parent1_{idx}.png", f"parent2_{idx}.png"
        ok1 = download_wikimedia_image(n1, img1) or download_unsplash_image(n1, img1)
        ok2 = download_wikimedia_image(n2, img2) or download_unsplash_image(n2, img2)
        if not ok1:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n1[0], fill=(255,255,255,255))
            im.save(img1)
        if not ok2:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n2[0], fill=(255,255,255,255))
            im.save(img2)
        child_path = f"child_{idx}.png"
        blend_images(img1, img2, child_path)
        children_paths.append((child_path, n1, n2))
    # Affichage et choix du plus beau
    from PIL import Image
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 5, figsize=(20,8))
    for i, (child_path, n1, n2) in enumerate(children_paths):
        ax = axs[i//5, i%5]
        ax.imshow(Image.open(child_path))
        ax.set_title(f"{n1} + {n2}")
        ax.axis('off')
    winner = random.choice(children_paths)
    plt.suptitle(f"L'enfant le plus beau : {winner[1]} + {winner[2]} !", fontsize=24, color='gold')
    plt.tight_layout()
    plt.show()

def cartoon_fusion_video():
    WIDTH, HEIGHT = CFG.WIDTH, CFG.HEIGHT
    FPS = 50
    DURATION = 63
    FRAMES_PER_COUPLE = int(FPS * (DURATION/5))
    couples = []
    used = set()
    while len(couples) < 5:
        h = random.choice(HOMMES)
        f = random.choice(FEMMES)
        if (h, f) in used:
            continue
        used.add((h, f))
        couples.append((h, f))
    all_frames = []
    baby_imgs = []
    for idx, (n1, n2) in enumerate(couples, 1):
        print(f"\n🎬 Cartoon couple {idx}: {n1} + {n2}")
        img1, img2 = f"parent1_{idx}.png", f"parent2_{idx}.png"
        ok1 = download_wikimedia_image(n1, img1) or download_unsplash_image(n1, img1)
        ok2 = download_wikimedia_image(n2, img2) or download_unsplash_image(n2, img2)
        if not ok1:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n1[0], fill=(255,255,255,255))
            im.save(img1)
        if not ok2:
            from PIL import Image, ImageDraw
            im = Image.new('RGBA', (400,400), (random.randint(100,255),random.randint(100,255),random.randint(100,255),255))
            d = ImageDraw.Draw(im)
            d.text((100,180), n2[0], fill=(255,255,255,255))
            im.save(img2)
        # Génère le bébé fusionné
        child_path = f"child_{idx}.png"
        blend_images(img1, img2, child_path)
        baby_imgs.append((child_path, n1, n2))
        # Animation cartoon (frames)
        frames = []
        avatar1 = cv2.cvtColor(cv2.imread(img1, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        avatar2 = cv2.cvtColor(cv2.imread(img2, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        baby = cv2.cvtColor(cv2.imread(child_path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        for t in range(FRAMES_PER_COUPLE):
            frame = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
            # Entrée rapide (0-0.7s)
            if t < FPS*0.7:
                x1 = int(-200 + (WIDTH//2-120+30)*(t/(FPS*0.7)))
                x2 = int(WIDTH+200 - (WIDTH//2-120+30)*(t/(FPS*0.7)))
                y = HEIGHT//2-100
                frame[y:y+400, x1:x1+400] = avatar1
                frame[y:y+400, x2:x2+400] = avatar2
            # Poursuite (0.7-1.5s)
            elif t < FPS*1.5:
                x1 = int(WIDTH//2-220 + 60*math.sin(t/8))
                x2 = int(WIDTH//2+20 - 60*math.sin(t/8))
                y = HEIGHT//2-100
                frame[y:y+400, x1:x1+400] = avatar1
                frame[y:y+400, x2:x2+400] = avatar2
            # Collision (1.5-2s)
            elif t < FPS*2:
                x = WIDTH//2-200
                y = HEIGHT//2-100
                frame[y:y+400, x:x+400] = avatar1
                frame[y:y+400, x+80:x+480] = avatar2
                # Effet BOING
                cv2.putText(frame, "BOING!", (WIDTH//2-100, HEIGHT//2-120), cv2.FONT_HERSHEY_TRIPLEX, 2, (255,255,0,255), 6)
            # Explosion paillettes/nuage (2-2.5s)
            elif t < FPS*2.5:
                for _ in range(80):
                    px = random.randint(WIDTH//2-80, WIDTH//2+80)
                    py = random.randint(HEIGHT//2-40, HEIGHT//2+120)
                    color = tuple(np.random.randint(150,255,3).tolist())+(255,)
                    cv2.circle(frame, (px,py), random.randint(8,18), color, -1)
                cv2.ellipse(frame, (WIDTH//2, HEIGHT//2+100), (120,60), 0, 0, 360, (255,255,255,180), -1)
                cv2.putText(frame, "POUF!", (WIDTH//2-80, HEIGHT//2-60), cv2.FONT_HERSHEY_TRIPLEX, 2, (255,0,255,255), 6)
            # Bébé sort du nuage (2.5-4s)
            elif t < FPS*4:
                alpha = min(1, (t-FPS*2.5)/(FPS*1.5))
                y = HEIGHT//2-40 + int(80*(1-alpha))
                frame[ y:y+400, WIDTH//2-200:WIDTH//2+200 ] = baby
                cv2.ellipse(frame, (WIDTH//2, HEIGHT//2+100), (120,60), 0, 0, 360, (255,255,255,int(180*(1-alpha))), -1)
                if alpha>0.7:
                    cv2.putText(frame, "TCHAK!", (WIDTH//2-100, HEIGHT//2-120), cv2.FONT_HERSHEY_TRIPLEX, 2, (0,255,255,255), 6)
            # Pause bébé (4-6s)
            else:
                frame[ HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200 ] = baby
                cv2.putText(frame, f"{n1} + {n2}", (WIDTH//2-180, HEIGHT-120), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255,255,255,255), 3)
            # Convert RGBA to RGB for video
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            all_frames.append(frame_rgb)
    # Affichage final des 5 bébés
    for idx, (child_path, n1, n2) in enumerate(baby_imgs, 1):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        baby = cv2.cvtColor(cv2.imread(child_path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGB)
        frame[ HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200 ] = baby
        cv2.putText(frame, f"{n1} + {n2}", (WIDTH//2-180, HEIGHT-120), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255,255,255), 3)
        all_frames.extend([frame]*int(FPS*2))
    # Annonce du plus beau
    winner = random.choice(baby_imgs)
    for t in range(int(FPS*3)):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        baby = cv2.cvtColor(cv2.imread(winner[0], cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGB)
        frame[ HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200 ] = baby
        cv2.putText(frame, f"Le plus beau : {winner[1]} + {winner[2]} !", (WIDTH//2-260, HEIGHT//2+220), cv2.FONT_HERSHEY_TRIPLEX, 1.3, (255,215,0), 4)
        all_frames.append(frame)
    # Export vidéo MP4
    out = cv2.VideoWriter('cartoon_fusion_tiktok.mp4', cv2.VideoWriter_fourcc(*'mp4v'), FPS, (WIDTH, HEIGHT))
    for f in all_frames:
        out.write(f)
    out.release()
    print("✅ Vidéo cartoon Looney Tunes générée : cartoon_fusion_tiktok.mp4")

# --- Pour activer ce mode, décommente la ligne suivante et commente le render_video() ---
if __name__ == "__main__":
    cartoon_fusion_video()
    pygame.quit()
