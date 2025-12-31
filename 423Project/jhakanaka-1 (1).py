from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time

# Game state variables
camera_pos = [0, 300, 500]
player_pos = [0, 100, 0]
oxygen = 100
score = 0
game_over = False
win = False
difficulty = 1.0
game_duration = 0
animation_time = 0
active_keys = set()
cheat_mode = False
camera_mode = "follow"  # "follow" or "free"
light_pos = [0, 300, 0]
light_on = True
last_shark_attack_time = 0
shark_attack_cooldown = 10  # seconds between possible attacks

# Game objects
treasures = []
sharks = []
seaweeds = []
bubbles = []
corals = []
jellyfishes = []

def reset_game():
    global camera_pos, player_pos, oxygen, score, game_over, win, difficulty, game_duration, animation_time
    global treasures, sharks, seaweeds, bubbles, corals, jellyfishes, cheat_mode, camera_mode, light_on
    global last_shark_attack_time

    camera_pos = [0, 300, 500]
    player_pos = [0, 100, 0]
    oxygen = 100
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

    treasures = generate_treasures(25)
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

def generate_sharks(count):
    return [[random.randint(-480, 480),
             random.randint(30, 150),
             random.randint(-480, 0),
             random.uniform(0, 2*math.pi),
             random.uniform(0.3, 0.8)] for _ in range(count)]

def generate_seaweeds(count):
    return [[random.randint(-480, 480),
             random.randint(50, 200),
             random.randint(-480, -50),
             random.uniform(0.5, 1.5)] for _ in range(count)]

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

def trigger_shark_attack():
    global sharks, player_pos
    
    if not sharks or cheat_mode:  # No attacks in cheat mode
        return
        
    # Choose a random shark to attack
    attacking_shark = random.choice(sharks)
    
    # Calculate direction to player
    dx = player_pos[0] - attacking_shark[0]
    dz = player_pos[2] - attacking_shark[2]
    distance = math.sqrt(dx*dx + dz*dz)
    
    if distance > 200:  # Only attack if not too close already
        # Set shark to charge towards player
        attacking_shark[3] = math.atan2(dz, dx)  # Face player
        attacking_shark[4] = 2.0  # Faster speed during attack
        
        # Make shark rise up a bit for dramatic effect
        attacking_shark[1] = min(attacking_shark[1] + 20, 180)

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

def calculate_lighting(x, y, z, color, shininess=0.5):
    if not light_on:
        return color
    
    # Light properties
    light_color = [1.0, 1.0, 1.0]
    ambient_intensity = 0.2
    diffuse_intensity = 0.8
    
    # Calculate vector from surface to light
    light_dir = [light_pos[0] - x, light_pos[1] - y, light_pos[2] - z]
    light_dist = math.sqrt(light_dir[0]**2 + light_dir[1]**2 + light_dir[2]**2)
    light_dir = [d/light_dist for d in light_dir] if light_dist > 0 else [0, 0, 0]
    
    # Calculate normal (simplified - assumes sphere-like objects)
    normal = [x, y, z]
    normal_len = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
    normal = [n/normal_len for n in normal] if normal_len > 0 else [0, 1, 0]
    
    # Ambient component
    ambient = [ambient_intensity * color[0], 
               ambient_intensity * color[1], 
               ambient_intensity * color[2]]
    
    # Diffuse component
    dot = max(0, normal[0]*light_dir[0] + normal[1]*light_dir[1] + normal[2]*light_dir[2])
    diffuse = [diffuse_intensity * dot * color[0] * light_color[0],
               diffuse_intensity * dot * color[1] * light_color[1],
               diffuse_intensity * dot * color[2] * light_color[2]]
    
    # Combine components
    final_color = [
        min(1.0, ambient[0] + diffuse[0]),
        min(1.0, ambient[1] + diffuse[1]),
        min(1.0, ambient[2] + diffuse[2])
    ]
    
    return final_color

def draw_seaweed(x, h, z, sway):
    glPushMatrix()
    glTranslatef(x, 0, z)
    sway_amount = math.sin(animation_time * sway) * 15
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(0, int(h), 5):
        width = (3 + random.random()*2) * (1 - i/h)
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
        lit_color = calculate_lighting(x, y, z, base_color, 0.8)
        glColor3f(*lit_color)
        glutSolidSphere(12, 16, 16)
    elif t == 'coin':
        base_color = [0.9, 0.8, 0.1]
        lit_color = calculate_lighting(x, y, z, base_color, 0.6)
        glColor3f(*lit_color)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(10, 2, 16, 4)
    else:
        base_color = [0.7, 0.5, 0.2]
        lit_color = calculate_lighting(x, y, z, base_color, 0.4)
        glColor3f(*lit_color)
        glScalef(1.5, 0.8, 1)
        glutSolidCube(20)
    glPopMatrix()

def draw_shark(x, y, z, angle, speed):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle * 180 / math.pi, 0, 1, 0)

    # Body color changes during attack (faster speed = attacking)
    if speed > 1.5:  # Attacking speed
        base_color = [0.6, 0.2, 0.2]  # Reddish when attacking
    else:
        base_color = [0.4, 0.4, 0.5]  # Normal color
        
    lit_color = calculate_lighting(x, y, z, base_color, 0.3)
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
    else:  # purple
        base_color = [0.6, 0.2, 0.6]
    
    lit_color = calculate_lighting(x, y, z, base_color, 0.2)
    glColor3f(*lit_color)
    
    # Base
    glutSolidSphere(size * 5, 10, 10)
    
    # Branches
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
    
    # Bell
    base_color = [0.8, 0.6, 0.9]
    lit_color = calculate_lighting(x, y, z, base_color, 0.7)
    glColor4f(lit_color[0], lit_color[1], lit_color[2], 0.7)
    glutSolidSphere(size * 8, 16, 16)
    
    # Tentacles
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
    
    # Body
    base_color = [0.2, 0.8, 0.2]
    lit_color = calculate_lighting(player_pos[0], player_pos[1], player_pos[2], base_color, 0.5)
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
    lit_color = calculate_lighting(player_pos[0]-10, player_pos[1], player_pos[2], base_color, 0.2)
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
    for x in [-500, 500]:
        for z in [500, -500]:
            lit_color = calculate_lighting(x, 0, z, base_color, 0.1)
            glColor3f(*lit_color)
            glVertex3f(x, 0, z)
    glEnd()
    
    # Water surface effect
    glBegin(GL_QUADS)
    glColor4f(0.0, 0.3, 0.6, 0.7)
    glVertex3f(-1000, 300, -1000)
    glVertex3f(1000, 300, -1000)
    glVertex3f(1000, 300, 1000)
    glVertex3f(-1000, 300, 1000)
    glEnd()
    
    for coral in corals:
        draw_coral(*coral)
    for seaweed in seaweeds:
        draw_seaweed(*seaweed)
    for treasure in treasures:
        draw_treasure(*treasure)
    for shark in sharks:
        draw_shark(*shark)
    for jellyfish in jellyfishes:
        draw_jellyfish(*jellyfish)
    for bubble in bubbles:
        draw_bubble(*bubble)
    draw_player()

def update_game():
    global oxygen, score, game_over, win, difficulty, game_duration, animation_time
    global camera_pos, player_pos, treasures, sharks, bubbles, jellyfishes
    global last_shark_attack_time

    current_time = time.time()
    delta_time = current_time - last_time[0]
    last_time[0] = current_time
    game_duration += delta_time
    animation_time += delta_time

    if game_over or win:
        return

    # Random shark attacks
    if current_time - last_shark_attack_time > shark_attack_cooldown / difficulty:
        if random.random() < 0.05 * difficulty:  # Higher difficulty = more frequent attacks
            trigger_shark_attack()
            last_shark_attack_time = current_time

    # Update sharks
    for shark in sharks:
        speed = shark[4] * delta_time * 20 * difficulty
        
        # If attacking (high speed), gradually return to normal speed
        if shark[4] > 0.8:
            shark[4] = max(0.8, shark[4] - delta_time * 0.2)
            
        shark[0] += math.cos(shark[3]) * speed
        shark[2] += math.sin(shark[3]) * speed
        
        # Random direction changes when not attacking
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

    # Oxygen consumption
    move_penalty = 1.0
    if any(key in active_keys for key in ['w', 'a', 's', 'd', ' ', 'c']):
        move_penalty = 1.3
    oxygen -= delta_time * 0.2 * move_penalty * difficulty
    if oxygen <= 0:
        game_over = True

    # Treasure collection
    px, py, pz = player_pos
    for treasure in treasures[:]:
        tx, ty, tz, tt, _ = treasure
        dist = math.sqrt((px-tx)**2 + (py-ty)**2 + (pz-tz)**2)
        if dist < 25:
            treasures.remove(treasure)
            score += 10
            if tt == 'pearl': oxygen = min(100, oxygen + 20)
            elif tt == 'coin': score += 5
            elif tt == 'chest': score += 20
            difficulty = min(2.0, difficulty + 0.01)

    # Win condition
    if not treasures:
        win = True

    # Enhanced shark collision during attacks
    for shark in sharks:
        sx, sy, sz, _, speed = shark
        dist = math.sqrt((px-sx)**2 + (py-sy)**2 + (pz-sz)**2)
        
        # More damage if shark is attacking (moving fast)
        if dist < 35:
            damage_multiplier = 1.0
            if speed > 1.5:  # Attacking
                damage_multiplier = 3.0
                # Push player away during attack
                push_dir = [px - sx, py - sy, pz - sz]
                push_dist = math.sqrt(push_dir[0]**2 + push_dir[1]**2 + push_dir[2]**2)
                if push_dist > 0:
                    push_dir = [d/push_dist for d in push_dir]
                    player_pos[0] += push_dir[0] * 20
                    player_pos[1] += push_dir[1] * 20
                    player_pos[2] += push_dir[2] * 20
            
            oxygen -= 20 * delta_time * 60 * damage_multiplier
            if oxygen <= 0:
                game_over = True

    # Update camera based on mode
    if camera_mode == "follow":
        camera_pos[0] += (player_pos[0] - camera_pos[0]) * 0.1
        camera_pos[1] += (player_pos[1] + 200 - camera_pos[1]) * 0.1
        camera_pos[2] += (player_pos[2] + 300 - camera_pos[2]) * 0.1

def keyboardListener(key, x, y):
    key = key.decode('utf-8').lower()
    if key == 'r' and (game_over or win):
        reset_game()
    elif key in ['w', 'a', 's', 'd', ' ', 'c']:
        active_keys.add(key)
    elif key == 'v':  # Toggle cheat vision
        global cheat_mode
        cheat_mode = not cheat_mode
    elif key == 'l':  # Toggle light
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

def idle():
    update_movement()
    update_game()
    glutPostRedisplay()

def update_movement():
    if game_over or win: return
    move_speed = 40.0 * (1.0 / 60.0)
    px, py, pz = player_pos
    
    # Movement with cheat mode check
    if not cheat_mode:
        if 'w' in active_keys: pz -= move_speed
        if 's' in active_keys: pz += move_speed
        if 'a' in active_keys: px -= move_speed
        if 'd' in active_keys: px += move_speed
        if ' ' in active_keys: py += move_speed
        if 'c' in active_keys: py -= move_speed
    else:  # Cheat mode - faster movement
        if 'w' in active_keys: pz -= move_speed * 2
        if 's' in active_keys: pz += move_speed * 2
        if 'a' in active_keys: px -= move_speed * 2
        if 'd' in active_keys: px += move_speed * 2
        if ' ' in active_keys: py += move_speed * 2
        if 'c' in active_keys: py -= move_speed * 2
    
    # Boundary checks
    px = max(-450, min(450, px))
    py = max(20, min(200, py))
    pz = max(-450, min(50, pz))
    
    player_pos[0], player_pos[1], player_pos[2] = px, py, pz
    
    # Rotate treasures
    for treasure in treasures:
        treasure[4] = (treasure[4] + 0.5) % 360

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    # Underwater fog effect (manual implementation)
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
    
    # Game status display
    if game_over:
        draw_text(300, 300, "GAME OVER! Press R to restart", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.2, 0.2))
        draw_text(320, 270, f"Final Score: {score}", GLUT_BITMAP_HELVETICA_18)
    elif win:
        draw_text(320, 300, "YOU WIN! Press R to play again", GLUT_BITMAP_TIMES_ROMAN_24, (0.2, 1, 0.2))
        draw_text(350, 270, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text(330, 240, f"Time: {int(game_duration)} seconds", GLUT_BITMAP_HELVETICA_18)
    else:
        # Check if any shark is attacking
        is_attacking = any(shark[4] > 1.5 for shark in sharks)
        
        oxygen_color = (0.2, 0.8, 0.2) if oxygen > 50 else (0.8, 0.8, 0.2) if oxygen > 20 else (0.8, 0.2, 0.2)
        draw_text(20, 580, f"Oxygen: {int(oxygen)}%", GLUT_BITMAP_HELVETICA_18, oxygen_color)
        draw_text(20, 550, f"Score: {score}", GLUT_BITMAP_HELVETICA_18)
        draw_text(650, 580, f"Treasures: {len(treasures)}", GLUT_BITMAP_HELVETICA_18, (1, 1, 0.5))
        draw_text(650, 550, f"Time: {int(game_duration)}", GLUT_BITMAP_HELVETICA_18)
        
        if is_attacking:
            draw_text(400, 500, "SHARK ATTACK!", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0, 0))
        
        if cheat_mode:
            draw_text(20, 520, "CHEAT MODE ACTIVE", GLUT_BITMAP_HELVETICA_18, (1, 0, 0))
        
        draw_text(400, 20, "Right click to toggle camera | L to toggle light | V for cheat vision", 
                GLUT_BITMAP_9_BY_15, (1, 1, 1))
    
    glutSwapBuffers()

last_time = [time.time()]

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Underwater Adventure")
    glClearColor(0.0, 0.1, 0.2, 1.0)
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