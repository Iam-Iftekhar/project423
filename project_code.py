from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time

# ==================== GAME STATE VARIABLES ====================
camera_pos = [0, 300, 500]
player_pos = [0, 100, 0]
oxygen = 100
stamina = 100  # NEW: Stamina system
score = 0
game_over = False
win = False
difficulty = 1.0
game_duration = 0
animation_time = 0
active_keys = set()
cheat_mode = False
camera_mode = "follow"
light_on = True
last_shark_attack_time = 0
shark_attack_cooldown = 10

# Power-up timers (NEW)
speed_boost_timer = 0
invincibility_timer = 0

# Game objects
treasures = []
powerups = []  # NEW: Power-ups list
sharks = []
seaweeds = []
bubbles = []
corals = []
jellyfishes = []

# ==================== INITIALIZATION FUNCTIONS ====================
def reset_game():
    global camera_pos, player_pos, oxygen, stamina, score, game_over, win
    global difficulty, game_duration, animation_time, cheat_mode, camera_mode, light_on
    global treasures, powerups, sharks, seaweeds, bubbles, corals, jellyfishes
    global last_shark_attack_time, speed_boost_timer, invincibility_timer
    
    camera_pos = [0, 300, 500]
    player_pos = [0, 100, 0]
    oxygen = 100
    stamina = 100
    score = 0
    game_over = False
    win = False
    difficulty = 1.0
    game_duration = 0
    animation_time = 0
    cheat_mode = False
    camera_mode = "follow"
    light_on = True
    last_shark_attack_time = 0
    speed_boost_timer = 0
    invincibility_timer = 0
    
    treasures = generate_treasures(25)
    powerups = generate_powerups(8)  # NEW: Generate power-ups
    sharks = generate_sharks(3)
    seaweeds = generate_seaweeds(30)
    bubbles = []
    corals = generate_corals(15)
    jellyfishes = generate_jellyfishes(8)

def generate_treasures(count):
    return [[random.randint(-450, 450),
             random.randint(20, 180),
             random.randint(-450, -50),
             random.choice(['pearl', 'coin', 'chest']),
             random.uniform(0, 360)] for _ in range(count)]

# NEW: Generate power-ups
def generate_powerups(count):
    powerups_list = []
    for _ in range(count):
        powerups_list.append([
            random.randint(-450, 450),
            random.randint(30, 180),
            random.randint(-450, -50),
            random.choice(['speed', 'invincibility', 'oxygen']),
            random.uniform(0, 360)
        ])
    return powerups_list

def generate_sharks(count):
    return [[random.randint(-480, 480),
             random.randint(30, 150),
             random.randint(-480, 0),
             random.uniform(0, 2*math.pi),
             random.uniform(0.3, 0.8)] for _ in range(count)]

def generate_seaweeds(count):
    seaweeds_list = []
    for _ in range(count):
        seaweeds_list.append([
            random.randint(-480, 480),
            random.randint(50, 200),
            random.randint(-480, -50),
            random.uniform(0.5, 1.5),
            random.uniform(10, 20)  # Pre-generated width
        ])
    return seaweeds_list

def generate_corals(count):
    return [[random.randint(-450, 450),
             random.randint(0, 10),
             random.randint(-450, -50),
             random.uniform(0.5, 2.0),
             random.choice(['red', 'orange', 'purple'])] for _ in range(count)]

def generate_jellyfishes(count):
    return [[random.randint(-450, 450),
             random.randint(50, 200),
             random.randint(-450, -50),
             random.uniform(0.5, 1.5),
             random.uniform(0, 360)] for _ in range(count)]

# ==================== SHARK ATTACK SYSTEM ====================
def trigger_shark_attack():
    global sharks, player_pos
    if not sharks or cheat_mode:
        return
    
    attacking_shark = random.choice(sharks)
    dx = player_pos[0] - attacking_shark[0]
    dz = player_pos[2] - attacking_shark[2]
    distance = math.sqrt(dx*dx + dz*dz)
    
    if distance > 200:
        attacking_shark[3] = math.atan2(dz, dx)
        attacking_shark[4] = 2.0
        attacking_shark[1] = min(attacking_shark[1] + 20, 180)

# ==================== RENDERING HELPERS ====================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def calculate_lighting(x, y, z, color):
    if not light_on:
        return color
    
    light_color = [1.0, 1.0, 1.0]
    ambient_intensity = 0.3
    diffuse_intensity = 0.7
    
    light_dir = [light_pos[0] - x, light_pos[1] - y, light_pos[2] - z]
    light_dist = math.sqrt(light_dir[0]**2 + light_dir[1]**2 + light_dir[2]**2)
    
    if light_dist > 0:
        light_dir = [d/light_dist for d in light_dir]
    else:
        light_dir = [0, 1, 0]
    
    normal = [0, 1, 0]
    
    ambient = [ambient_intensity * color[i] for i in range(3)]
    
    dot = max(0, sum(normal[i]*light_dir[i] for i in range(3)))
    diffuse = [diffuse_intensity * dot * color[i] * light_color[i] for i in range(3)]
    
    final_color = [min(1.0, ambient[i] + diffuse[i]) for i in range(3)]
    return final_color

# ==================== DRAWING FUNCTIONS ====================
def draw_seaweed(x, h, z, sway, base_width):
    glPushMatrix()
    glTranslatef(x, 0, z)
    sway_amount = math.sin(animation_time * sway) * 15
    
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(0, int(h), 5):
        width = base_width * (1 - i/h)
        green = 0.3 + 0.4 * (i/h)
        base_color = [0.1, green, 0.1]
        lit_color = calculate_lighting(x, i, z, base_color)
        glColor3f(*lit_color)
        glVertex3f(-width + sway_amount*(i/h), i, 0)
        glVertex3f(width + sway_amount*(i/h), i, 0)
    glEnd()
    glPopMatrix()

def draw_treasure(x, y, z, t, rotation):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rotation, 0, 1, 0)
    
    if t == 'pearl':
        base_color = [0.95, 0.95, 0.99]
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glutSolidSphere(12, 16, 16)
    elif t == 'coin':
        base_color = [0.9, 0.8, 0.1]
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(10, 2, 16, 4)
    else:  # chest
        base_color = [0.7, 0.5, 0.2]
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glScalef(1.5, 0.8, 1)
        glutSolidCube(20)
    glPopMatrix()

# NEW: Draw power-ups
def draw_powerup(x, y, z, powerup_type, rotation):
    glPushMatrix()
    glTranslatef(x, y + math.sin(animation_time * 2) * 5, z)
    glRotatef(rotation, 0, 1, 0)
    
    if powerup_type == 'speed':
        base_color = [0.1, 0.9, 1.0]  # Cyan
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glutSolidCone(8, 20, 16, 4)
    elif powerup_type == 'invincibility':
        base_color = [1.0, 0.8, 0.1]  # Gold
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glutSolidSphere(10, 16, 16)
    else:  # oxygen
        base_color = [0.2, 1.0, 0.2]  # Green
        lit_color = calculate_lighting(x, y, z, base_color)
        glColor3f(*lit_color)
        glutSolidTorus(3, 10, 16, 16)
    glPopMatrix()

def draw_shark(x, y, z, angle, speed):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle * 180 / math.pi, 0, 1, 0)
    
    if speed > 1.5:
        base_color = [0.8, 0.2, 0.2]
    else:
        base_color = [0.4, 0.4, 0.5]
    
    lit_color = calculate_lighting(x, y, z, base_color)
    glColor3f(*lit_color)
    
    # Body
    glPushMatrix()
    glScalef(2.5, 1.0, 1.0)
    glutSolidSphere(15, 20, 20)
    glPopMatrix()
    
    # Tail
    glPushMatrix()
    glTranslatef(-35, 0, 0)
    glRotatef(math.sin(animation_time * 5) * 15, 0, 1, 0)
    glScalef(0.5, 1.0, 1.5)
    glutSolidCone(10, 20, 10, 2)
    glPopMatrix()
    
    # Dorsal fin
    glPushMatrix()
    glTranslatef(0, 15, 0)
    glRotatef(-90, 1, 0, 0)
    glutSolidCone(5, 10, 8, 1)
    glPopMatrix()
    
    # Pectoral fins
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(5, -5, 8 * side)
        glRotatef(30 * side, 1, 0, 0)
        glScalef(1.0, 0.3, 0.6)
        glutSolidSphere(5, 10, 10)
        glPopMatrix()
    
    glPopMatrix()

def draw_coral(x, y, z, size, color_type):
    glPushMatrix()
    glTranslatef(x, y, z)
    
    if color_type == 'red':
        base_color = [0.8, 0.2, 0.2]
    elif color_type == 'orange':
        base_color = [0.9, 0.5, 0.1]
    else:
        base_color = [0.6, 0.2, 0.6]
    
    lit_color = calculate_lighting(x, y, z, base_color)
    glColor3f(*lit_color)
    
    glutSolidSphere(size * 5, 10, 10)
    
    for i in range(3):
        glPushMatrix()
        glRotatef(i * 120 + animation_time * 10, 0, 1, 0)
        glRotatef(30, 1, 0, 0)
        glutSolidCone(size * 2, size * 10, 8, 3)
        glPopMatrix()
    
    glPopMatrix()

def draw_jellyfish(x, y, z, size, rotation):
    glPushMatrix()
    glTranslatef(x, y + math.sin(animation_time * size) * 10, z)
    glRotatef(rotation, 0, 1, 0)
    
    base_color = [0.8, 0.6, 0.9]
    lit_color = calculate_lighting(x, y, z, base_color)
    glColor4f(lit_color[0], lit_color[1], lit_color[2], 0.7)
    glutSolidSphere(size * 8, 16, 16)
    
    glBegin(GL_LINES)
    for i in range(8):
        angle = i * 45
        tx = math.cos(math.radians(angle)) * size * 5
        tz = math.sin(math.radians(angle)) * size * 5
        ty = -size * 15 - math.sin(animation_time * 2 + i) * size * 5
        glVertex3f(tx, 0, tz)
        glVertex3f(tx, ty, tz)
    glEnd()
    glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(*player_pos)
    
    # Invincibility shield effect
    if invincibility_timer > 0:
        glPushMatrix()
        glColor4f(1.0, 0.8, 0.0, 0.3)
        glutSolidSphere(25, 20, 20)
        glPopMatrix()
    
    # Body
    base_color = [0.2, 0.8, 0.2]
    lit_color = calculate_lighting(player_pos[0], player_pos[1], player_pos[2], base_color)
    glColor3f(*lit_color)
    glutSolidSphere(15, 20, 20)
    
    # Eyes
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(10, 5, 5 * side)
        glColor3f(1, 1, 1)
        glutSolidSphere(3, 10, 10)
        glTranslatef(1, 0, 0)
        glColor3f(0, 0, 0)
        glutSolidSphere(1.5, 10, 10)
        glPopMatrix()
    
    # Air tank
    glPushMatrix()
    glTranslatef(-10, 0, 0)
    glRotatef(90, 0, 1, 0)
    base_color = [0.3, 0.3, 0.3]
    lit_color = calculate_lighting(player_pos[0]-10, player_pos[1], player_pos[2], base_color)
    glColor3f(*lit_color)
    gluCylinder(gluNewQuadric(), 5, 5, 20, 10, 2)
    glPopMatrix()
    
    glPopMatrix()

def draw_bubble(x, y, z, size, speed):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor4f(0.7, 0.8, 1.0, 0.5)
    glutSolidSphere(size, 16, 16)
    glPopMatrix()

def draw_objects():
    # Ocean floor
    glBegin(GL_QUADS)
    base_color = [0.3, 0.25, 0.2]
    lit_color = calculate_lighting(0, 0, 0, base_color)
    glColor3f(*lit_color)
    glVertex3f(-500, 0, -500)
    glVertex3f(500, 0, -500)
    glVertex3f(500, 0, 500)
    glVertex3f(-500, 0, 500)
    glEnd()
    
    # Water surface
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glColor4f(0.0, 0.3, 0.6, 0.7)
    glVertex3f(-1000, 300, -1000)
    glVertex3f(1000, 300, -1000)
    glVertex3f(1000, 300, 1000)
    glVertex3f(-1000, 300, 1000)
    glEnd()
    glDisable(GL_BLEND)
    
    for coral in corals:
        draw_coral(*coral)
    for seaweed in seaweeds:
        draw_seaweed(*seaweed)
    for treasure in treasures:
        draw_treasure(*treasure)
    for powerup in powerups:
        draw_powerup(*powerup)
    for shark in sharks:
        draw_shark(*shark)
    for jellyfish in jellyfishes:
        draw_jellyfish(*jellyfish)
    for bubble in bubbles:
        draw_bubble(*bubble)
    
    draw_player()

# ==================== GAME LOGIC ====================
def update_game():
    global oxygen, stamina, score, game_over, win, difficulty, game_duration, animation_time
    global camera_pos, player_pos, treasures, powerups, sharks, bubbles, jellyfishes
    global last_shark_attack_time, speed_boost_timer, invincibility_timer
    
    current_time = time.time()
    delta_time = current_time - last_time[0]
    last_time[0] = current_time
    
    game_duration += delta_time
    animation_time += delta_time
    
    if game_over or win:
        return
    
    # Update power-up timers
    if speed_boost_timer > 0:
        speed_boost_timer -= delta_time
    if invincibility_timer > 0:
        invincibility_timer -= delta_time
    
    # Stamina regeneration
    is_moving = any(key in active_keys for key in ['w', 'a', 's', 'd', ' ', 'c'])
    if is_moving:
        stamina = max(0, stamina - delta_time * 15)
    else:
        stamina = min(100, stamina + delta_time * 10)
    
    # Random shark attacks
    if not cheat_mode:
        if current_time - last_shark_attack_time > shark_attack_cooldown / difficulty:
            if random.random() < 0.05 * difficulty:
                trigger_shark_attack()
                last_shark_attack_time = current_time
    
    # Update sharks
    for shark in sharks:
        speed = shark[4] * delta_time * 20 * difficulty
        
        if shark[4] > 0.8:
            shark[4] = max(0.8, shark[4] - delta_time * 0.2)
        
        shark[0] += math.cos(shark[3]) * speed
        shark[2] += math.sin(shark[3]) * speed
        
        if shark[4] <= 0.8:
            shark[3] += random.uniform(-0.03, 0.03) * difficulty
        
        if abs(shark[0]) > 480 or abs(shark[2]) > 480:
            shark[3] += math.pi/2 + random.uniform(-0.3, 0.3)
    
    # Update jellyfish
    for jellyfish in jellyfishes:
        jellyfish[4] = (jellyfish[4] + delta_time * 10) % 360
    
    # Generate bubbles
    if random.random() < 0.03:
        bubbles.append([
            player_pos[0] + random.uniform(-50, 50),
            player_pos[1] - 30,
            player_pos[2] + random.uniform(-50, 50),
            random.uniform(5, 15),
            random.uniform(0.3, 1.0)
        ])
    
    # Update bubbles
    for bubble in bubbles[:]:
        bubble[1] += bubble[4] * delta_time * 30
        bubble[3] *= 1.005
        if bubble[1] > 300 or bubble[3] > 30:
            bubbles.remove(bubble)
    
    # Oxygen consumption (disabled in cheat mode)
    if not cheat_mode:
        move_penalty = 1.3 if is_moving else 1.0
        oxygen -= delta_time * 5 * move_penalty * difficulty
        if oxygen <= 0:
            game_over = True
    
    # Treasure collection
    px, py, pz = player_pos
    for treasure in treasures[:]:
        tx, ty, tz, tt, _ = treasure
        dist = math.sqrt((px-tx)**2 + (py-ty)**2 + (pz-tz)**2)
        if dist < 25:
            treasures.remove(treasure)
            if tt == 'pearl':
                score += 10
                oxygen = min(100, oxygen + 20)
            elif tt == 'coin':
                score += 15
            elif tt == 'chest':
                score += 30
            difficulty = min(2.0, difficulty + 0.05)
    
    # Power-up collection (NEW)
    for powerup in powerups[:]:
        px_x, px_y, px_z, p_type, _ = powerup
        dist = math.sqrt((px-px_x)**2 + (py-px_y)**2 + (pz-px_z)**2)
        if dist < 25:
            powerups.remove(powerup)
            if p_type == 'speed':
                speed_boost_timer = 5.0
            elif p_type == 'invincibility':
                invincibility_timer = 8.0
            elif p_type == 'oxygen':
                oxygen = min(100, oxygen + 30)
    
    # Win condition
    if not treasures:
        win = True
    
    # Shark collision (disabled in cheat mode or with invincibility)
    if not cheat_mode and invincibility_timer <= 0:
        for shark in sharks:
            sx, sy, sz, _, speed = shark
            dist = math.sqrt((px-sx)**2 + (py-sy)**2 + (pz-sz)**2)
            if dist < 35:
                damage = 15 if speed > 1.5 else 5
                oxygen -= damage * delta_time
                
                # Push player away
                if dist > 0:
                    push_dir = [(px - sx)/dist, (py - sy)/dist, (pz - sz)/dist]
                    player_pos[0] += push_dir[0] * 20 * delta_time
                    player_pos[1] += push_dir[1] * 20 * delta_time
                    player_pos[2] += push_dir[2] * 20 * delta_time
                
                if oxygen <= 0:
                    game_over = True
    
    # Update camera
    if camera_mode == "follow":
        camera_pos[0] += (player_pos[0] - camera_pos[0]) * 0.1
        camera_pos[1] += (player_pos[1] + 200 - camera_pos[1]) * 0.1
        camera_pos[2] += (player_pos[2] + 300 - camera_pos[2]) * 0.1

def update_movement():
    global stamina
    if game_over or win:
        return
    
    # Base speed affected by stamina and speed boost
    base_speed = 40.0 * (1.0 / 60.0)
    
    # Stamina affects speed
    stamina_multiplier = 0.5 if stamina < 10 else 1.0
    
    # Speed boost multiplier
    speed_multiplier = 2.0 if speed_boost_timer > 0 else 1.0
    
    move_speed = base_speed * stamina_multiplier * speed_multiplier
    
    px, py, pz = player_pos
    
    if 'w' in active_keys: pz -= move_speed
    if 's' in active_keys: pz += move_speed
    if 'a' in active_keys: px -= move_speed
    if 'd' in active_keys: px += move_speed
    if ' ' in active_keys: py += move_speed
    if 'c' in active_keys: py -= move_speed
    
    # Boundary checks
    px = max(-450, min(450, px))
    py = max(20, min(280, py))
    pz = max(-450, min(50, pz))
    
    player_pos[0], player_pos[1], player_pos[2] = px, py, pz
    
    # Rotate treasures and power-ups
    for treasure in treasures:
        treasure[4] = (treasure[4] + 0.5) % 360
    for powerup in powerups:
        powerup[4] = (powerup[4] + 1.0) % 360

# ==================== INPUT HANDLERS ====================
def keyboardListener(key, x, y):
    key = key.decode('utf-8').lower()
    if key == 'r' and (game_over or win):
        reset_game()
    elif key in ['w', 'a', 's', 'd', ' ', 'c']:
        active_keys.add(key)
    elif key == 'v':
        global cheat_mode
        cheat_mode = not cheat_mode
    elif key == 'l':
        global light_on
        light_on = not light_on

def keyboardUpListener(key, x, y):
    key = key.decode('utf-8').lower()
    if key in active_keys:
        active_keys.remove(key)

def specialKeyListener(key, x, y):
    global camera_pos, camera_mode
    if camera_mode == "free":
        if key == GLUT_KEY_UP: camera_pos[1] += 10
        elif key == GLUT_KEY_DOWN: camera_pos[1] -= 10
        elif key == GLUT_KEY_LEFT: camera_pos[0] -= 10
        elif key == GLUT_KEY_RIGHT: camera_pos[0] += 10

def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = "free" if camera_mode == "follow" else "follow"

# ==================== RENDERING ====================
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.25, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    px, py, pz = player_pos
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              px, py, pz,
              0, 1, 0)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    # Fog effect
    if not cheat_mode:
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, [0.0, 0.1, 0.2, 1.0])
        glFogf(GL_FOG_START, 100.0)
        glFogf(GL_FOG_END, 400.0)
    else:
        glDisable(GL_FOG)
    
    setupCamera()
    
    # Ocean background
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.1, 0.3)
    glVertex3f(-1000, 0, -1000)
    glVertex3f(1000, 0, -1000)
    glColor3f(0.0, 0.3, 0.6)
    glVertex3f(1000, 1000, -1000)
    glVertex3f(-1000, 1000, -1000)
    glEnd()
    
    draw_objects()
    
    # UI Display
    if game_over:
        draw_text(300, 400, "GAME OVER! Press R to restart", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.2, 0.2))
        draw_text(350, 360, f"Final Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text(350, 330, f"Time: {int(game_duration)} seconds", GLUT_BITMAP_HELVETICA_18)
    elif win:
        draw_text(320, 400, "YOU WIN! Press R to play again", GLUT_BITMAP_TIMES_ROMAN_24, (0.2, 1, 0.2))
        draw_text(380, 360, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text(350, 330, f"Time: {int(game_duration)} seconds", GLUT_BITMAP_HELVETICA_18)
    else:
        # Check if shark attacking
        is_attacking = any(shark[4] > 1.5 for shark in sharks)
        
        # Oxygen bar
        oxygen_color = (0.2, 0.8, 0.2) if oxygen > 50 else (0.8, 0.8, 0.2) if oxygen > 20 else (0.8, 0.2, 0.2)
        draw_text(20, 750, f"Oxygen: {int(oxygen)}%", GLUT_BITMAP_HELVETICA_18, oxygen_color)
        
        # Stamina bar (NEW)
        stamina_color = (0.3, 0.6, 1.0) if stamina > 30 else (1.0, 0.5, 0.0)
        draw_text(20, 720, f"Stamina: {int(stamina)}%", GLUT_BITMAP_HELVETICA_18, stamina_color)
        
        draw_text(20, 690, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text(650, 750, f"Treasures: {len(treasures)}", GLUT_BITMAP_HELVETICA_18, (1, 1, 0.5))
        draw_text(650, 720, f"Power-ups: {len(powerups)}", GLUT_BITMAP_HELVETICA_18, (0.5, 1, 1))
        draw_text(650, 690, f"Time: {int(game_duration)}", GLUT_BITMAP_HELVETICA_18)
        
        # Active effects
        if speed_boost_timer > 0:
            draw_text(350, 750, f"SPEED BOOST: {int(speed_boost_timer)}s", GLUT_BITMAP_HELVETICA_18, (0, 1, 1))
        if invincibility_timer > 0:
            draw_text(350, 720, f"INVINCIBLE: {int(invincibility_timer)}s", GLUT_BITMAP_HELVETICA_18, (1, 0.8, 0))
        
        if is_attacking:
            draw_text(400, 650, "SHARK ATTACK!", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0, 0))
        
        if cheat_mode:
            draw_text(20, 660, "CHEAT MODE ACTIVE", GLUT_BITMAP_HELVETICA_18, (1, 0, 0))
        
        if stamina < 10:
            draw_text(350, 690, "LOW STAMINA - SLOW MOVEMENT!", GLUT_BITMAP_HELVETICA_18, (1, 0.5, 0))
        
        draw_text(20, 30, "Controls: WASD=Move | Space=Up | C=Down | V=Cheat | L=Light | R=Restart",
                  GLUT_BITMAP_9_BY_15, (0.8, 0.8, 0.8))
    
    glutSwapBuffers()

def idle():
    update_movement()
    update_game()
    glutPostRedisplay()

# ==================== MAIN ====================
light_pos = [0, 300, 0]
last_time = [time.time()]

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Abyssal Dive: Oxygen Rush")
    
    glClearColor(0.0, 0.1, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)  # FIXED: Added depth test
    
    reset_game()
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
