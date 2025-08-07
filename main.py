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

def generate_viral_filename():
    """Génère un nom de fichier accrocheur et aléatoire pour la vidéo."""
    prefixes = [
        "🔥", "⚡", "💥", "🎯", "🚀", "💎", "👑", "🎪", "🎭", "🎨", "🎬", "🎤", "🎧", "🎮", "🏆", "🥇", "💫", "⭐", "🌟", "✨"
    ]
    
    adjectives = [
        "VIRAL", "EPIC", "LEGENDARY", "INSANE", "CRAZY", "AMAZING", "INCREDIBLE", "MIND_BLOWING", 
        "HYPERTROPHIC", "MEGA", "ULTRA", "SUPER", "EXTREME", "WILD", "SICK", "LIT", "FIRE", 
        "BOMBASTIC", "PHENOMENAL", "SPECTACULAR", "MAGNIFICENT", "ASTRONOMICAL", "COSMIC", 
        "INTERGALACTIC", "QUANTUM", "NUCLEAR", "ATOMIC", "EXPLOSIVE", "DYNAMITE", "THUNDER"
    ]
    
    nouns = [
        "BATTLE", "SHOWDOWN", "CLASH", "DUEL", "WAR", "FIGHT", "COMBAT", "CONFLICT", "RIVALRY",
        "CHALLENGE", "COMPETITION", "TOURNAMENT", "CHAMPIONSHIP", "MATCH", "GAME", "PLAYOFF",
        "FINALS", "SEMIFINALS", "QUARTERFINALS", "ELIMINATION", "SURVIVAL", "DESTINY", "FATE",
        "LEGACY", "DESTINY", "JOURNEY", "ADVENTURE", "QUEST", "MISSION", "EXPEDITION"
    ]
    
    suffixes = [
        "2024", "2025", "V2", "PRO", "MAX", "PLUS", "ULTIMATE", "DEFINITIVE", "FINAL", "REMASTERED",
        "ENHANCED", "UPGRADED", "PREMIUM", "DELUXE", "COLLECTOR", "SPECIAL", "EXCLUSIVE", "LIMITED",
        "RARE", "LEGENDARY", "MYTHICAL", "DIVINE", "CELESTIAL", "ETERNAL", "INFINITE", "ABSOLUTE"
    ]
    
    prefix = random.choice(prefixes)
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    suffix = random.choice(suffixes)
    
    # Ajouter un timestamp pour garantir l'unicité
    timestamp = f"{random.randint(1000, 9999)}"
    
    return f"{prefix}_{adjective}_{noun}_{suffix}_{timestamp}.mp4"

class Config:
    WIDTH, HEIGHT = 720, 1280
    FPS = 50
    DURATION = 10
    TITLE_DURATION = 2
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
    
    @property
    def OUTPUT_FILE(self):
        return generate_viral_filename()

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
    variants = [
        query, 
        query + " portrait", 
        query + " face", 
        query + " headshot",
        query.split()[0] + " " + query.split()[-1] if len(query.split()) > 1 else query.split()[0],
        query.split()[0]
    ]
    
    for v in variants:
        url = (
            "https://commons.wikimedia.org/w/api.php?"
            "action=query&format=json&prop=imageinfo&generator=search&gsrsearch="
            + requests.utils.quote(v) +
            "&gsrlimit=3&iiprop=url|size|mime"
        )
        try:
            print(f"    🔍 Recherche Wikimedia: {v}")
            r = requests.get(url, timeout=10)
            data = r.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page in pages.values():
                if 'imageinfo' in page:
                    img_info = page['imageinfo'][0]
                    img_url = img_info['url']
                    
                    # Vérifier que c'est une image de taille raisonnable
                    if 'size' in img_info and img_info['size'] > 10000:  # Au moins 10KB
                        print(f"    📥 Téléchargement depuis: {img_url}")
                        img_data = requests.get(img_url, timeout=10).content
                        
                        # Convertir en PNG avec PIL pour s'assurer du bon format
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                        img = img.resize((400, 400), Image.Resampling.LANCZOS)
                        img.save(filename, 'PNG')
                        print(f"    ✅ Image sauvegardée: {filename}")
                        return True
        except Exception as e:
            print(f"    ❌ Erreur Wikimedia {v}: {e}")
            continue
    return False

def download_unsplash_image(query, filename):
    """Télécharge une image portrait depuis Unsplash (requête simple, pas besoin de clé)."""
    try:
        print(f"    🔍 Recherche Unsplash: {query}")
        
        # Utiliser la nouvelle approche robuste
        if download_image_robust(query, filename):
            return True
        
        # Si la recherche robuste échoue, essayer l'ancienne méthode
        url = f"https://source.unsplash.com/400x400/?{requests.utils.quote(query + ',portrait,face')}"
        print(f"    📥 Téléchargement depuis: {url}")
        
        # Ajouter des headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=10, headers=headers)
        
        # Vérifier si la réponse contient une image
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
            img_data = response.content
            
            # Convertir en PNG avec PIL pour s'assurer du bon format
            from PIL import Image
            import io
            
            try:
                img = Image.open(io.BytesIO(img_data))
                # Vérifier si c'est une image valide
                img.verify()
                img.close()
                
                # Recharger l'image pour la traiter
                img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                img = img.resize((400, 400), Image.Resampling.LANCZOS)
                img.save(filename, 'PNG')
                print(f"    ✅ Image sauvegardée: {filename}")
                return True
            except Exception as e:
                print(f"    ⚠️  Format d'image non reconnu: {e}")
                return False
        else:
            print(f"    ⚠️  Réponse non-image reçue (status: {response.status_code}, content-type: {response.headers.get('content-type')})")
            return False
            
    except Exception as e:
        print(f"    ❌ Erreur Unsplash: {e}")
        return False

def download_pixabay_image(query, filename):
    """Télécharge une image depuis Pixabay (sans clé API, utilisation directe)."""
    try:
        print(f"    🔍 Recherche Pixabay: {query}")
        
        # Utiliser la nouvelle approche robuste
        if download_image_robust(query, filename):
            return True
        
        # Si la recherche robuste échoue, essayer l'ancienne méthode
        try:
            print(f"    📥 Tentative de téléchargement depuis Pixabay...")
            
            # Utiliser une approche alternative - essayer de télécharger depuis Unsplash
            # car Pixabay nécessite une clé API pour l'accès programmatique
            unsplash_url = f"https://source.unsplash.com/400x400/?{requests.utils.quote(query + ',portrait,face')}"
            print(f"    📥 Téléchargement depuis Unsplash (alternative Pixabay): {unsplash_url}")
            
            # Ajouter des headers pour simuler un navigateur
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(unsplash_url, timeout=10, headers=headers)
            
            # Vérifier si la réponse contient une image
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                img_data = response.content
                
                # Convertir en PNG avec PIL pour s'assurer du bon format
                from PIL import Image
                import io
                
                try:
                    img = Image.open(io.BytesIO(img_data))
                    # Vérifier si c'est une image valide
                    img.verify()
                    img.close()
                    
                    # Recharger l'image pour la traiter
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(filename, 'PNG')
                    print(f"    ✅ Image téléchargée via alternative Pixabay: {filename}")
                    return True
                except Exception as e:
                    print(f"    ⚠️  Format d'image non reconnu: {e}")
            else:
                print(f"    ⚠️  Réponse non-image reçue (status: {response.status_code}, content-type: {response.headers.get('content-type')})")
                
        except Exception as e:
            print(f"    ⚠️  Échec du téléchargement Pixabay: {e}")
        
        # Si le téléchargement échoue, créer un avatar de fallback plus réaliste
        print(f"    🎨 Création d'un avatar de fallback pour Pixabay...")
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Créer un avatar plus réaliste au lieu d'un simple cercle
        # Couleur de peau réaliste
        skin_colors = [
            (255, 224, 189), (255, 205, 148), (234, 192, 134), (255, 173, 96),
            (234, 153, 153), (255, 198, 140), (255, 218, 185), (255, 228, 196)
        ]
        skin_color = random.choice(skin_colors)
        
        # Dessiner la tête (ovale)
        head_width, head_height = 200, 250
        head_x = (400 - head_width) // 2
        head_y = (400 - head_height) // 2
        draw.ellipse([head_x, head_y, head_x + head_width, head_y + head_height], fill=skin_color + (255,))
        
        # Dessiner les yeux
        eye_color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        eye_size = 25
        left_eye = (head_x + 60, head_y + 80)
        right_eye = (head_x + 140, head_y + 80)
        draw.ellipse([left_eye[0]-eye_size, left_eye[1]-eye_size, left_eye[0]+eye_size, left_eye[1]+eye_size], 
                     fill=eye_color + (255,))
        draw.ellipse([right_eye[0]-eye_size, right_eye[1]-eye_size, right_eye[0]+eye_size, right_eye[1]+eye_size], 
                     fill=eye_color + (255,))
        
        # Pupilles
        draw.ellipse([left_eye[0]-8, left_eye[1]-8, left_eye[0]+8, left_eye[1]+8], fill=(0, 0, 0, 255))
        draw.ellipse([right_eye[0]-8, right_eye[1]-8, right_eye[0]+8, right_eye[1]+8], fill=(0, 0, 0, 255))
        
        # Nez
        nose_color = tuple(int(c * 0.8) for c in skin_color) + (255,)
        draw.ellipse([head_x + 85, head_y + 120, head_x + 115, head_y + 150], fill=nose_color)
        
        # Bouche
        mouth_color = (220, 20, 60, 255)
        draw.ellipse([head_x + 70, head_y + 160, head_x + 130, head_y + 180], fill=mouth_color)
        
        # Ajouter le nom en bas
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        text_color = (255, 255, 255, 255)
        text_bbox = draw.textbbox((0, 0), query.split()[0], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (400 - text_width) // 2
        y = 350
        draw.text((x, y), query.split()[0], fill=text_color, font=font)
        
        img.save(filename, 'PNG')
        print(f"    ✅ Avatar Pixabay créé: {filename}")
        return True
    except Exception as e:
        print(f"    ❌ Erreur Pixabay: {e}")
        return False

def download_pexels_image(query, filename):
    """Télécharge une image depuis Pexels (sans clé API, création d'avatar)."""
    try:
        print(f"    🔍 Recherche Pexels: {query}")
        
        # Utiliser la nouvelle approche robuste
        if download_image_robust(query, filename):
            return True
        
        # Si la recherche robuste échoue, essayer l'ancienne méthode
        try:
            print(f"    📥 Tentative de téléchargement depuis Pexels...")
            # Utiliser Unsplash comme alternative pour Pexels
            unsplash_url = f"https://source.unsplash.com/400x400/?{requests.utils.quote(query + ',portrait,face')}"
            print(f"    📥 Téléchargement depuis Unsplash (alternative Pexels): {unsplash_url}")
            
            # Ajouter des headers pour simuler un navigateur
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(unsplash_url, timeout=10, headers=headers)
            
            # Vérifier si la réponse contient une image
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                img_data = response.content
                
                # Convertir en PNG avec PIL pour s'assurer du bon format
                from PIL import Image
                import io
                
                try:
                    img = Image.open(io.BytesIO(img_data))
                    # Vérifier si c'est une image valide
                    img.verify()
                    img.close()
                    
                    # Recharger l'image pour la traiter
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(filename, 'PNG')
                    print(f"    ✅ Image téléchargée via alternative Pexels: {filename}")
                    return True
                except Exception as e:
                    print(f"    ⚠️  Format d'image non reconnu: {e}")
            else:
                print(f"    ⚠️  Réponse non-image reçue (status: {response.status_code}, content-type: {response.headers.get('content-type')})")
                
        except Exception as e:
            print(f"    ⚠️  Échec du téléchargement Pexels: {e}")
        
        # Si le téléchargement échoue, créer un avatar de fallback plus réaliste
        print(f"    🎨 Création d'un avatar de fallback pour Pexels...")
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Créer un avatar plus réaliste au lieu d'un simple cercle
        # Couleur de peau réaliste
        skin_colors = [
            (255, 224, 189), (255, 205, 148), (234, 192, 134), (255, 173, 96),
            (234, 153, 153), (255, 198, 140), (255, 218, 185), (255, 228, 196)
        ]
        skin_color = random.choice(skin_colors)
        
        # Dessiner la tête (ovale)
        head_width, head_height = 200, 250
        head_x = (400 - head_width) // 2
        head_y = (400 - head_height) // 2
        draw.ellipse([head_x, head_y, head_x + head_width, head_y + head_height], fill=skin_color + (255,))
        
        # Dessiner les yeux
        eye_color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        eye_size = 25
        left_eye = (head_x + 60, head_y + 80)
        right_eye = (head_x + 140, head_y + 80)
        draw.ellipse([left_eye[0]-eye_size, left_eye[1]-eye_size, left_eye[0]+eye_size, left_eye[1]+eye_size], 
                     fill=eye_color + (255,))
        draw.ellipse([right_eye[0]-eye_size, right_eye[1]-eye_size, right_eye[0]+eye_size, right_eye[1]+eye_size], 
                     fill=eye_color + (255,))
        
        # Pupilles
        draw.ellipse([left_eye[0]-8, left_eye[1]-8, left_eye[0]+8, left_eye[1]+8], fill=(0, 0, 0, 255))
        draw.ellipse([right_eye[0]-8, right_eye[1]-8, right_eye[0]+8, right_eye[1]+8], fill=(0, 0, 0, 255))
        
        # Nez
        nose_color = tuple(int(c * 0.8) for c in skin_color) + (255,)
        draw.ellipse([head_x + 85, head_y + 120, head_x + 115, head_y + 150], fill=nose_color)
        
        # Bouche
        mouth_color = (220, 20, 60, 255)
        draw.ellipse([head_x + 70, head_y + 160, head_x + 130, head_y + 180], fill=mouth_color)
        
        # Ajouter le nom en bas
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        text_color = (255, 255, 255, 255)
        text_bbox = draw.textbbox((0, 0), query.split()[0], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (400 - text_width) // 2
        y = 350
        draw.text((x, y), query.split()[0], fill=text_color, font=font)
        
        img.save(filename, 'PNG')
        print(f"    ✅ Avatar Pexels créé: {filename}")
        return True
    except Exception as e:
        print(f"    ❌ Erreur Pexels: {e}")
        return False

def create_realistic_avatar(name, filename, is_male=True):
    """Crée un avatar réaliste avec un visage généré."""
    from PIL import Image, ImageDraw, ImageFont
    import random
    
    # Couleurs de peau réalistes
    skin_colors = [
        (255, 224, 189), (255, 205, 148), (234, 192, 134), (255, 173, 96),
        (234, 153, 153), (255, 198, 140), (255, 218, 185), (255, 228, 196),
        (255, 235, 205), (255, 245, 238), (245, 245, 220), (255, 250, 240)
    ]
    
    # Créer une image 400x400 avec transparence
    img = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Couleur de peau aléatoire
    skin_color = random.choice(skin_colors)
    
    # Dessiner la tête (ovale)
    head_width, head_height = 200, 250
    head_x = (400 - head_width) // 2
    head_y = (400 - head_height) // 2
    draw.ellipse([head_x, head_y, head_x + head_width, head_y + head_height], fill=skin_color)
    
    # Dessiner les yeux
    eye_color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
    eye_size = 25
    left_eye_x = head_x + 60
    right_eye_x = head_x + 140
    eye_y = head_y + 100
    draw.ellipse([left_eye_x, eye_y, left_eye_x + eye_size, eye_y + eye_size], fill=eye_color)
    draw.ellipse([right_eye_x, eye_y, right_eye_x + eye_size, eye_y + eye_size], fill=eye_color)
    
    # Dessiner le nez
    nose_x = head_x + head_width // 2
    nose_y = eye_y + 40
    draw.ellipse([nose_x - 10, nose_y, nose_x + 10, nose_y + 20], fill=skin_color)
    
    # Dessiner la bouche
    mouth_x = nose_x
    mouth_y = nose_y + 40
    draw.arc([mouth_x - 20, mouth_y, mouth_x + 20, mouth_y + 15], 0, 180, fill=(139, 69, 19), width=3)
    
    # Dessiner les cheveux
    hair_colors = [
        (139, 69, 19), (160, 82, 45), (210, 105, 30), (244, 164, 96),
        (255, 215, 0), (255, 255, 0), (255, 165, 0), (255, 0, 0),
        (128, 0, 128), (0, 0, 255), (0, 255, 0), (255, 192, 203)
    ]
    hair_color = random.choice(hair_colors)
    
    # Style de cheveux selon le genre
    if is_male:
        # Cheveux courts pour les hommes
        hair_points = [
            (head_x - 20, head_y - 20),
            (head_x + head_width + 20, head_y - 20),
            (head_x + head_width + 30, head_y + 50),
            (head_x - 30, head_y + 50)
        ]
    else:
        # Cheveux longs pour les femmes
        hair_points = [
            (head_x - 30, head_y - 40),
            (head_x + head_width + 30, head_y - 40),
            (head_x + head_width + 40, head_y + 100),
            (head_x - 40, head_y + 100)
        ]
    
    draw.polygon(hair_points, fill=hair_color)
    
    # Ajouter le nom
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text = name[0].upper()
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (400 - text_width) // 2
    text_y = head_y + head_height + 20
    
    # Ombre du texte
    draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 128), font=font)
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    
    # Sauvegarder en PNG avec transparence
    img.save(filename, 'PNG')
    print(f"🎨 Avatar réaliste créé pour {name}: {filename}")
    return True

# --- LISTES SÉPARÉES HOMMES/FEMMES ---
HOMMES = [
    "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappe", "Neymar Jr", "Erling Haaland", "Karim Benzema", "Luka Modric", "Vinicius Junior", "Robert Lewandowski", "Mohamed Salah", "Antoine Griezmann", "Paulo Dybala", "Sergio Ramos", "Kevin De Bruyne", "Harry Kane", "LeBron James", "Stephen Curry", "Giannis Antetokounmpo", "Novak Djokovic", "Rafael Nadal", "Roger Federer", "Conor McGregor", "Khabib Nurmagomedov", "Mike Tyson", "Floyd Mayweather", "Usain Bolt", "Lewis Hamilton", "Michael Jordan", "IShowSpeed", "Ninja gamer", "xQc", "PewDiePie", "Squeezie", "MrBeast", "Dream Minecraft", "Markiplier", "Ludwig Ahgren", "SypherPK", "TimTheTatman", "TommyInnit", "Drake", "Travis Scott", "The Weeknd", "Eminem", "Kanye West", "Justin Bieber", "Ed Sheeran", "Post Malone", "Logan Paul", "Jake Paul", "Elon Musk", "Jeff Bezos", "Mark Zuckerberg", "Donald Trump", "Vladimir Putin", "Jordan Peterson", "Joe Rogan", "Ben Shapiro", "Spider Man", "Iron Man", "Captain America", "Batman", "Superman", "Deadpool", "Thanos", "Black Panther", "Naruto Uzumaki", "Sasuke Uchiha", "Son Goku", "Vegeta", "Monkey D Luffy", "Roronoa Zoro", "Eren Yeager", "Levi Ackerman", "Saitama One Punch Man", "Gojo Satoru", "Tanjiro Kamado", "Light Yagami", "L Death Note", "Shinji Ikari", "Noah Beck", "Brent Rivera", "Mr Fresh Asian", "Brent Faiyaz", "Harry Styles", "BTS Jungkook", "BTS Jimin", "BTS V Taehyung", "Maluma", "Cristiano Ronaldo Jr", "Lionel Messi Jr", "Barack Obama", "Prince Harry", "Zayn Malik", "Mario Nintendo", "Luigi Nintendo", "Sonic the Hedgehog", "Knuckles Sonic", "Tails Sonic", "Lara Croft", "Master Chief Halo", "Kratos God of War", "Atreus God of War", "Link Legend of Zelda", "Ganondorf Zelda", "Will Smith", "Chris Rock", "Keanu Reeves", "Jason Momoa", "David Schwimmer", "Zlatan Ibrahimovic", "Andrea Pirlo", "Francesco Totti", "Ronaldinho", "David Beckham", "Eden Hazard", "Mesut Ozil", "Alexis Sanchez", "Canelo Alvarez", "Tyson Fury"
]
FEMMES = [
    "Serena Williams", "Naomi Osaka", "Pokimane", "Amouranth", "Valkyrae", "Taylor Swift", "Beyonce", "Rihanna", "Billie Eilish", "Doja Cat", "Dua Lipa", "Olivia Rodrigo", "Zendaya", "Scarlett Johansson", "Margot Robbie", "Jennifer Lawrence", "Anne Hathaway", "Greta Thunberg", "Amber Heard", "Wonder Woman", "Nezuko Kamado", "Charli DAmelio", "Addison Rae", "Bella Poarch", "Khaby Lame", "Loren Gray", "Avani Gregg", "Dixie DAmelio", "Nikkie Tutorials", "James Charles", "Shakira", "Adele", "Ariana Grande", "Cardi B", "Nicki Minaj", "Lisa Blackpink", "Jennie Blackpink", "Rose Blackpink", "Jisoo Blackpink", "Anitta", "Oprah Winfrey", "Michelle Obama", "Meghan Markle", "Kim Kardashian", "Kylie Jenner", "Kendall Jenner", "Gigi Hadid", "Bella Hadid", "Paris Hilton", "Selena Gomez", "Princess Peach", "Zelda Princess", "Samus Aran", "Jada Pinkett Smith", "Gal Gadot", "Millie Bobby Brown", "Sadie Sink", "Courteney Cox", "Lisa Kudrow", "Matt LeBlanc", "Naomi Scott", "Emma Watson", "Emma Stone", "Florence Pugh", "Natalie Portman", "Jessica Alba", "Eva Mendes", "Mila Kunis", "Kate Winslet", "Angelina Jolie", "Reese Witherspoon", "Julia Roberts", "Sandra Bullock", "Anne Curtis", "Priyanka Chopra", "Deepika Padukone", "Alia Bhatt", "Kriti Sanon", "Anushka Sharma", "Halle Berry", "Monica Bellucci", "Salma Hayek", "Penelope Cruz", "Cameron Diaz", "Kristen Stewart", "Kirsten Dunst", "Dakota Johnson", "Lily Collins", "Sofia Vergara", "Megan Fox", "Halsey", "Katy Perry", "Ellie Goulding", "Charli XCX", "Camila Cabello", "Lauren Jauregui", "Normani", "Becky G", "Tini Stoessel", "Madison Beer", "Hailee Steinfeld", "Lana Del Rey", "Kacey Musgraves", "Sabrina Carpenter"
]

# --- LISTE COMBINÉE POUR LA SÉLECTION ALÉATOIRE ---
PERSONNALITIES = HOMMES + FEMMES

# --- DEMANDE DES NOMS ET TÉLÉCHARGEMENT AUTOMATIQUE ---
def get_or_download_images():
    img1, img2 = 'img1.png', 'img2.png'
    tried = set()
    for attempt in range(15):
        # Sélectionner un homme et une femme au lieu de deux personnes aléatoires
        n1 = random.choice(HOMMES)
        n2 = random.choice(FEMMES)
        if (n1, n2) in tried or (n2, n1) in tried:
            continue
        tried.add((n1, n2))
        
        print(f"🔍 Tentative {attempt + 1}/15: Recherche d'images pour {n1} et {n2}")
        
        # Essayer plusieurs sources pour l'homme
        ok1 = False
        if not ok1:
            print(f"  📥 Téléchargement Wikimedia pour {n1}...")
            ok1 = download_wikimedia_image(n1, img1)
        if not ok1:
            print(f"  📥 Téléchargement Unsplash pour {n1}...")
            ok1 = download_unsplash_image(n1, img1)
        if not ok1:
            print(f"  📥 Téléchargement Pixabay pour {n1}...")
            ok1 = download_pixabay_image(n1, img1)
        if not ok1:
            print(f"  📥 Téléchargement Pexels pour {n1}...")
            ok1 = download_pexels_image(n1, img1)
        
        # Essayer plusieurs sources pour la femme
        ok2 = False
        if not ok2:
            print(f"  📥 Téléchargement Wikimedia pour {n2}...")
            ok2 = download_wikimedia_image(n2, img2)
        if not ok2:
            print(f"  📥 Téléchargement Unsplash pour {n2}...")
            ok2 = download_unsplash_image(n2, img2)
        if not ok2:
            print(f"  📥 Téléchargement Pixabay pour {n2}...")
            ok2 = download_pixabay_image(n2, img2)
        if not ok2:
            print(f"  📥 Téléchargement Pexels pour {n2}...")
            ok2 = download_pexels_image(n2, img2)
        
        # Si toujours rien, créer des avatars réalistes
        if not ok1:
            print(f"  🎨 Création d'un avatar réaliste pour {n1}...")
            ok1 = create_realistic_avatar(n1, img1, is_male=True)
        if not ok2:
            print(f"  🎨 Création d'un avatar réaliste pour {n2}...")
            ok2 = create_realistic_avatar(n2, img2, is_male=False)
        
        if ok1 and ok2:
            print(f"✅ Images trouvées/créées pour {n1} et {n2}")
            return img1, img2, n1.upper(), n2.upper()
        else:
            print(f"⚠️  Impossible de trouver/créer des images pour {n1} ou {n2}, nouvelle tentative...")
    
    # Dernière tentative avec des avatars réalistes
    print("🔄 Dernière tentative avec des avatars réalistes...")
    n1 = random.choice(HOMMES)
    n2 = random.choice(FEMMES)
    create_realistic_avatar(n1, img1, is_male=True)
    create_realistic_avatar(n2, img2, is_male=False)
    return img1, img2, n1.upper(), n2.upper()

# --- UTILISATION DES IMAGES AUTOMATIQUES ---
IMG1_PATH, IMG2_PATH, IMG1_NAME, IMG2_NAME = get_or_download_images()

# Initialiser pygame correctement
pygame.init()
# Créer une surface virtuelle pour éviter l'erreur "No video mode has been set"
pygame.display.set_mode((1, 1), pygame.NOFRAME)
screen = pygame.Surface((CFG.WIDTH, CFG.HEIGHT))
clock = pygame.time.Clock()
FONT_LARGE  = pygame.font.SysFont(None, 120)
FONT_MEDIUM = pygame.font.SysFont(None, 80)
FONT_SMALL  = pygame.font.SysFont(None, 60)

def load_or_fallback(name, color):
    """Charge une image avec gestion robuste des erreurs et conversion automatique."""
    try:
        # Essayer de charger l'image avec pygame
        img = pygame.image.load(name).convert_alpha()
        print(f"✅ Image chargée avec succès: {name}")
        return pygame.transform.smoothscale(img, (80, 80))
    except Exception as e:
        print(f"⚠️  Erreur lors du chargement de {name}: {e}")
        # Créer un avatar de fallback
        img = pygame.Surface((80, 80), pygame.SRCALPHA)
        img.fill(color)
        # Ajouter la première lettre du nom
        try:
            font = pygame.font.SysFont(None, 40)
            text = font.render(name.split('/')[-1].split('.')[0][0].upper(), True, (255, 255, 255))
            text_rect = text.get_rect(center=(40, 40))
            img.blit(text, text_rect)
        except:
            pass
        return img

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
    
    # Utiliser OpenCV au lieu de MoviePy
    output_filename = CFG.OUTPUT_FILE
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, CFG.FPS, (CFG.WIDTH, CFG.HEIGHT))
    
    for i in range(total_frames):
        game.update()
        game.render_frame(screen)
        
        # Convertir pygame surface en array OpenCV
        frame_array = pygame.surfarray.array3d(screen)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
        
        out.write(frame_array)
        
        if i % max(1, total_frames // 10) == 0:
            pct = (i / total_frames) * 100
            print(f"📊 Progression: {pct:.0f}%")
    
    out.release()
    
    try:
        shutil.rmtree(CFG.FRAMES_DIR)
    except Exception:
        pass
    
    print(f"✅ Vidéo créée : {output_filename}")
    print("🚀 Prêt pour TikTok / Shorts / Reels.")

def blend_images(img_path1, img_path2, out_path):
    from PIL import Image, ImageDraw
    
    # Fonction pour créer un avatar de fallback
    def create_fallback_avatar(name, color):
        im = Image.new('RGBA', (400, 400), color)
        d = ImageDraw.Draw(im)
        # Dessiner un cercle pour la tête
        d.ellipse([50, 50, 350, 350], fill=(255, 255, 255, 100))
        # Ajouter la première lettre du nom
        try:
            # Essayer d'utiliser une police plus grande
            font_size = 120
            d.text((200, 180), name[0].upper(), fill=(255, 255, 255, 255), anchor="mm")
        except:
            # Fallback si la police échoue
            d.text((150, 150), name[0].upper(), fill=(255, 255, 255, 255))
        return im
    
    # Charger ou créer les images
    try:
        im1 = Image.open(img_path1).convert('RGBA').resize((400, 400))
    except:
        # Créer un avatar de fallback pour l'homme
        color1 = (random.randint(100, 200), random.randint(50, 150), random.randint(50, 150), 255)
        im1 = create_fallback_avatar("H", color1)
    
    try:
        im2 = Image.open(img_path2).convert('RGBA').resize((400, 400))
    except:
        # Créer un avatar de fallback pour la femme
        color2 = (random.randint(150, 255), random.randint(100, 200), random.randint(150, 255), 255)
        im2 = create_fallback_avatar("F", color2)
    
    # Fusionner les images
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
        
        # Télécharger ou créer des avatars réalistes
        print(f"  📥 Téléchargement des images pour {n1} et {n2}...")
        
        ok1 = False
        if not ok1:
            print(f"  🔍 Essai Wikimedia pour {n1}...")
            ok1 = download_wikimedia_image(n1, img1)
        if not ok1:
            print(f"  🔍 Essai Unsplash pour {n1}...")
            ok1 = download_unsplash_image(n1, img1)
        if not ok1:
            print(f"  🔍 Essai Pixabay pour {n1}...")
            ok1 = download_pixabay_image(n1, img1)
        if not ok1:
            print(f"  🔍 Essai Pexels pour {n1}...")
            ok1 = download_pexels_image(n1, img1)
        if not ok1:
            print(f"  🎨 Création d'un avatar réaliste pour {n1}...")
            ok1 = create_realistic_avatar(n1, img1, is_male=True)
        
        ok2 = False
        if not ok2:
            print(f"  🔍 Essai Wikimedia pour {n2}...")
            ok2 = download_wikimedia_image(n2, img2)
        if not ok2:
            print(f"  🔍 Essai Unsplash pour {n2}...")
            ok2 = download_unsplash_image(n2, img2)
        if not ok2:
            print(f"  🔍 Essai Pixabay pour {n2}...")
            ok2 = download_pixabay_image(n2, img2)
        if not ok2:
            print(f"  🔍 Essai Pexels pour {n2}...")
            ok2 = download_pexels_image(n2, img2)
        if not ok2:
            print(f"  🎨 Création d'un avatar réaliste pour {n2}...")
            ok2 = create_realistic_avatar(n2, img2, is_male=False)
        
        # Génère le bébé fusionné
        child_path = f"child_{idx}.png"
        blend_images(img1, img2, child_path)
        baby_imgs.append((child_path, n1, n2))
        
        # Animation cartoon (frames)
        frames = []
        try:
            # Charger les images avec PIL puis convertir en numpy array
            from PIL import Image
            import numpy as np
            
            # Charger l'avatar 1
            pil_img1 = Image.open(img1).convert('RGBA')
            pil_img1 = pil_img1.resize((400, 400), Image.Resampling.LANCZOS)
            avatar1 = np.array(pil_img1)
            print(f"  ✅ Avatar 1 chargé: {avatar1.shape}")
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement de {img1}: {e}")
            # Créer un avatar de fallback pour l'homme
            avatar1 = np.zeros((400, 400, 4), dtype=np.uint8)
            color1 = (random.randint(100, 200), random.randint(50, 150), random.randint(50, 150), 255)
            cv2.circle(avatar1, (200, 200), 150, color1, -1)
            cv2.putText(avatar1, n1[0].upper(), (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255, 255), 5)
        
        try:
            # Charger l'avatar 2
            pil_img2 = Image.open(img2).convert('RGBA')
            pil_img2 = pil_img2.resize((400, 400), Image.Resampling.LANCZOS)
            avatar2 = np.array(pil_img2)
            print(f"  ✅ Avatar 2 chargé: {avatar2.shape}")
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement de {img2}: {e}")
            # Créer un avatar de fallback pour la femme
            avatar2 = np.zeros((400, 400, 4), dtype=np.uint8)
            color2 = (random.randint(150, 255), random.randint(100, 200), random.randint(150, 255), 255)
            cv2.circle(avatar2, (200, 200), 150, color2, -1)
            cv2.putText(avatar2, n2[0].upper(), (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255, 255), 5)
        
        try:
            # Charger le bébé
            pil_baby = Image.open(child_path).convert('RGBA')
            pil_baby = pil_baby.resize((400, 400), Image.Resampling.LANCZOS)
            baby = np.array(pil_baby)
            print(f"  ✅ Bébé chargé: {baby.shape}")
        except Exception as e:
            print(f"  ⚠️  Erreur lors du chargement de {child_path}: {e}")
            # Créer un bébé de fallback
            baby = np.zeros((400, 400, 4), dtype=np.uint8)
            color_baby = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255), 255)
            cv2.circle(baby, (200, 200), 150, color_baby, -1)
            cv2.putText(baby, "B", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255, 255), 5)
        
        for t in range(FRAMES_PER_COUPLE):
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            
            # Entrée rapide (0-0.7s)
            if t < FPS*0.7:
                x1 = int(-200 + (WIDTH//2-120+30)*(t/(FPS*0.7)))
                x2 = int(WIDTH+200 - (WIDTH//2-120+30)*(t/(FPS*0.7)))
                y = HEIGHT//2-100
                # Vérifier que les coordonnées sont valides
                if 0 <= x1 < WIDTH-400 and 0 <= y < HEIGHT-400:
                    # Convertir RGBA en RGB pour l'affichage
                    if avatar1.shape[2] == 4:
                        # Créer un masque alpha
                        alpha = avatar1[:, :, 3:4] / 255.0
                        rgb = avatar1[:, :, :3]
                        # Appliquer l'alpha sur le frame
                        frame[y:y+400, x1:x1+400] = (1 - alpha) * frame[y:y+400, x1:x1+400] + alpha * rgb
                    else:
                        frame[y:y+400, x1:x1+400] = avatar1[:, :, :3]
                if 0 <= x2 < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if avatar2.shape[2] == 4:
                        alpha = avatar2[:, :, 3:4] / 255.0
                        rgb = avatar2[:, :, :3]
                        frame[y:y+400, x2:x2+400] = (1 - alpha) * frame[y:y+400, x2:x2+400] + alpha * rgb
                    else:
                        frame[y:y+400, x2:x2+400] = avatar2[:, :, :3]
            # Poursuite (0.7-1.5s)
            elif t < FPS*1.5:
                x1 = int(WIDTH//2-220 + 60*math.sin(t/8))
                x2 = int(WIDTH//2+20 - 60*math.sin(t/8))
                y = HEIGHT//2-100
                # Vérifier que les coordonnées sont valides
                if 0 <= x1 < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if avatar1.shape[2] == 4:
                        alpha = avatar1[:, :, 3:4] / 255.0
                        rgb = avatar1[:, :, :3]
                        frame[y:y+400, x1:x1+400] = (1 - alpha) * frame[y:y+400, x1:x1+400] + alpha * rgb
                    else:
                        frame[y:y+400, x1:x1+400] = avatar1[:, :, :3]
                if 0 <= x2 < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if avatar2.shape[2] == 4:
                        alpha = avatar2[:, :, 3:4] / 255.0
                        rgb = avatar2[:, :, :3]
                        frame[y:y+400, x2:x2+400] = (1 - alpha) * frame[y:y+400, x2:x2+400] + alpha * rgb
                    else:
                        frame[y:y+400, x2:x2+400] = avatar2[:, :, :3]
            # Collision (1.5-2s)
            elif t < FPS*2:
                x = WIDTH//2-200
                y = HEIGHT//2-100
                # Vérifier que les coordonnées sont valides
                if 0 <= x < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if avatar1.shape[2] == 4:
                        alpha = avatar1[:, :, 3:4] / 255.0
                        rgb = avatar1[:, :, :3]
                        frame[y:y+400, x:x+400] = (1 - alpha) * frame[y:y+400, x:x+400] + alpha * rgb
                    else:
                        frame[y:y+400, x:x+400] = avatar1[:, :, :3]
                if 0 <= x+80 < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if avatar2.shape[2] == 4:
                        alpha = avatar2[:, :, 3:4] / 255.0
                        rgb = avatar2[:, :, :3]
                        frame[y:y+400, x+80:x+480] = (1 - alpha) * frame[y:y+400, x+80:x+480] + alpha * rgb
                    else:
                        frame[y:y+400, x+80:x+480] = avatar2[:, :, :3]
                # Effet BOING
                cv2.putText(frame, "BOING!", (WIDTH//2-100, HEIGHT//2-120), cv2.FONT_HERSHEY_TRIPLEX, 2, (255,255,0), 6)
            # Explosion paillettes/nuage (2-2.5s)
            elif t < FPS*2.5:
                for _ in range(80):
                    px = random.randint(WIDTH//2-80, WIDTH//2+80)
                    py = random.randint(HEIGHT//2-40, HEIGHT//2+120)
                    color = tuple(np.random.randint(150,255,3).tolist())
                    cv2.circle(frame, (px,py), random.randint(8,18), color, -1)
                cv2.ellipse(frame, (WIDTH//2, HEIGHT//2+100), (120,60), 0, 0, 360, (255,255,255), -1)
                cv2.putText(frame, "POUF!", (WIDTH//2-80, HEIGHT//2-60), cv2.FONT_HERSHEY_TRIPLEX, 2, (255,0,255), 6)
            # Bébé sort du nuage (2.5-4s)
            elif t < FPS*4:
                alpha = min(1, (t-FPS*2.5)/(FPS*1.5))
                y = HEIGHT//2-40 + int(80*(1-alpha))
                x = WIDTH//2-200
                # Vérifier que les coordonnées sont valides
                if 0 <= x < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if baby.shape[2] == 4:
                        baby_alpha = baby[:, :, 3:4] / 255.0
                        baby_rgb = baby[:, :, :3]
                        frame[y:y+400, x:x+400] = (1 - baby_alpha) * frame[y:y+400, x:x+400] + baby_alpha * baby_rgb
                    else:
                        frame[y:y+400, x:x+400] = baby[:, :, :3]
                cv2.ellipse(frame, (WIDTH//2, HEIGHT//2+100), (120,60), 0, 0, 360, (255,255,255), -1)
                if alpha>0.7:
                    cv2.putText(frame, "TCHAK!", (WIDTH//2-100, HEIGHT//2-120), cv2.FONT_HERSHEY_TRIPLEX, 2, (0,255,255), 6)
            # Pause bébé (4-6s)
            else:
                y = HEIGHT//2-40
                x = WIDTH//2-200
                # Vérifier que les coordonnées sont valides
                if 0 <= x < WIDTH-400 and 0 <= y < HEIGHT-400:
                    if baby.shape[2] == 4:
                        baby_alpha = baby[:, :, 3:4] / 255.0
                        baby_rgb = baby[:, :, :3]
                        frame[y:y+400, x:x+400] = (1 - baby_alpha) * frame[y:y+400, x:x+400] + baby_alpha * baby_rgb
                    else:
                        frame[y:y+400, x:x+400] = baby[:, :, :3]
                cv2.putText(frame, f"{n1} + {n2}", (WIDTH//2-180, HEIGHT-120), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255,255,255), 3)
            
            all_frames.append(frame)
    # Affichage final des 5 bébés
    for idx, (child_path, n1, n2) in enumerate(baby_imgs, 1):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        try:
            # Charger le bébé avec PIL pour gérer la transparence
            pil_baby = Image.open(child_path).convert('RGBA')
            pil_baby = pil_baby.resize((400, 400), Image.Resampling.LANCZOS)
            baby = np.array(pil_baby)
            
            # Appliquer la transparence
            if baby.shape[2] == 4:
                alpha = baby[:, :, 3:4] / 255.0
                rgb = baby[:, :, :3]
                frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = (1 - alpha) * frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] + alpha * rgb
            else:
                frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = baby[:, :, :3]
        except:
            # Créer un bébé de fallback
            baby = np.zeros((400, 400, 3), dtype=np.uint8)
            color_baby = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
            cv2.circle(baby, (200, 200), 150, color_baby, -1)
            cv2.putText(baby, "B", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
            frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = baby
        cv2.putText(frame, f"{n1} + {n2}", (WIDTH//2-180, HEIGHT-120), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255,255,255), 3)
        all_frames.extend([frame]*int(FPS*2))
    # Annonce du plus beau
    winner = random.choice(baby_imgs)
    for t in range(int(FPS*3)):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        try:
            # Charger le bébé gagnant avec PIL
            pil_baby = Image.open(winner[0]).convert('RGBA')
            pil_baby = pil_baby.resize((400, 400), Image.Resampling.LANCZOS)
            baby = np.array(pil_baby)
            
            # Appliquer la transparence
            if baby.shape[2] == 4:
                alpha = baby[:, :, 3:4] / 255.0
                rgb = baby[:, :, :3]
                frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = (1 - alpha) * frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] + alpha * rgb
            else:
                frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = baby[:, :, :3]
        except:
            # Créer un bébé de fallback
            baby = np.zeros((400, 400, 3), dtype=np.uint8)
            color_baby = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
            cv2.circle(baby, (200, 200), 150, color_baby, -1)
            cv2.putText(baby, "B", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
            frame[HEIGHT//2-40:HEIGHT//2-40+400, WIDTH//2-200:WIDTH//2+200] = baby
        cv2.putText(frame, f"Le plus beau : {winner[1]} + {winner[2]} !", (WIDTH//2-260, HEIGHT//2+220), cv2.FONT_HERSHEY_TRIPLEX, 1.3, (255,215,0), 4)
        all_frames.append(frame)
    # Export vidéo MP4
    cartoon_filename = generate_viral_filename()
    out = cv2.VideoWriter(cartoon_filename, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (WIDTH, HEIGHT))
    for f in all_frames:
        out.write(f)
    out.release()
    print(f"✅ Vidéo cartoon Looney Tunes générée : {cartoon_filename}")

# --- Pour activer ce mode, décommente la ligne suivante et commente le render_video() ---
if __name__ == "__main__":
    cartoon_fusion_video()
    pygame.quit()

def download_image_robust(query, filename):
    """Télécharge une image avec plusieurs sources et méthodes robustes."""
    try:
        print(f"    🔍 Recherche robuste pour: {query}")
        
        # 1. Essayer Wikimedia Commons (le plus fiable)
        if download_wikimedia_image(query, filename):
            return True
        
        # 2. Essayer avec une approche alternative pour Unsplash
        try:
            print(f"    📥 Tentative Unsplash alternative...")
            # Utiliser une URL différente pour Unsplash
            unsplash_url = f"https://source.unsplash.com/featured/400x400/?{requests.utils.quote(query + ' person face portrait')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(unsplash_url, timeout=15, headers=headers, allow_redirects=True)
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                img_data = response.content
                
                # Vérifier si c'est une image valide
                from PIL import Image
                import io
                
                try:
                    img = Image.open(io.BytesIO(img_data))
                    img.verify()
                    img.close()
                    
                    # Recharger et traiter l'image
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(filename, 'PNG')
                    print(f"    ✅ Image téléchargée avec succès: {filename}")
                    return True
                except Exception as e:
                    print(f"    ⚠️  Format d'image non reconnu: {e}")
            else:
                print(f"    ⚠️  Réponse non-image (status: {response.status_code})")
                
        except Exception as e:
            print(f"    ⚠️  Échec Unsplash: {e}")
        
        # 3. Essayer avec une recherche Google Images alternative
        try:
            print(f"    📥 Tentative recherche alternative...")
            # Utiliser une approche différente - essayer de télécharger depuis un service d'images gratuit
            alternative_url = f"https://picsum.photos/400/400?random={hash(query) % 1000}"
            
            response = requests.get(alternative_url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                img_data = response.content
                
                try:
                    img = Image.open(io.BytesIO(img_data))
                    img.verify()
                    img.close()
                    
                    img = Image.open(io.BytesIO(img_data)).convert('RGBA')
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(filename, 'PNG')
                    print(f"    ✅ Image alternative téléchargée: {filename}")
                    return True
                except Exception as e:
                    print(f"    ⚠️  Format d'image alternative non reconnu: {e}")
                    
        except Exception as e:
            print(f"    ⚠️  Échec recherche alternative: {e}")
        
        return False
        
    except Exception as e:
        print(f"    ❌ Erreur dans download_image_robust: {e}")
        return False
