from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import sys
import time

# =============================================================================
# CONFIGURATION
# =============================================================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
MOUSE_SENSITIVITY = 0.1
MOVE_SPEED = 1.5
SPRINT_MULTIPLIER = 2.5
FOG_DENSITY = 0.005

# =============================================================================
# GAME STATE CLASS
# =============================================================================
class GameState:
    PLAYING = 0
    WON = 1
    LOST = 2

class Game:
    def __init__(self):
        # Initialize rendering-specific things once
        self.quadric = None
        self.keys = {}
        self.modifiers = 0 
        self.center_x = int(WINDOW_WIDTH / 2)
        self.center_y = int(WINDOW_HEIGHT / 2)
        self.ignore_next_mouse = False
        
        # Start the game
        self.reset_game()

    def reset_game(self):
        """Resets all game variables to start fresh."""
        self.state = GameState.PLAYING
        
        # Camera / Player
        self.pos = [0, 10, 50]    # X, Y, Z
        self.yaw = -90.0
        self.pitch = 0.0
        
        # Stats
        self.oxygen = 100.0
        self.health = 100.0
        self.score = 0
        self.stamina = 100.0
        
        # Flags
        self.sprinting = False
        self.invincible = False
        self.invincible_timer = 0
        self.last_time = time.time()
        
        # Medkit Logic Flags
        self.medkits_spawned_for_low_health = False
        
        # Entities
        self.sharks = []
        self.treasures = []
        self.bubbles = []
        self.seaweeds = [] 
        self.medkits = []
        
        self.generate_world()

    def generate_world(self):
        # Tutorial Chest
        self.treasures = []
        self.treasures.append({'pos': [0, 5, -40], 'active': True, 'rot': 0})

        # Random Chests
        for _ in range(15):
            self.treasures.append({
                'pos': [random.uniform(-400, 400), 5, random.uniform(-400, 400)],
                'active': True,
                'rot': random.uniform(0, 360)
            })

        # Sharks
        self.sharks = []
        self.sharks.append({'pos': [60, 40, -60], 'yaw': 0, 'speed': 0.6, 'anim_offset': 0})
        for _ in range(10):
            self.sharks.append({
                'pos': [random.uniform(-400, 400), random.uniform(10, 250), random.uniform(-400, 400)],
                'yaw': random.uniform(0, 360),
                'speed': random.uniform(0.5, 1.2),
                'anim_offset': random.uniform(0, 10)
            })
            
        # Bubbles & Seaweed
        self.bubbles = []
        for _ in range(200):
            self.bubbles.append({
                'pos': [random.uniform(-500, 500), random.uniform(0, 400), random.uniform(-500, 500)],
                'size': random.uniform(0.5, 2.0)
            })
        self.seaweeds = []
        for _ in range(350): 
            self.seaweeds.append({
                'pos': [random.uniform(-450, 450), random.uniform(-450, 450)],
                'height': random.randint(4, 8), 
                'rot': random.uniform(0, 360),  
                'scale': random.uniform(0.8, 1.2) 
            })
            
    def spawn_medkits(self):
        """Spawns 3 medkits around the map."""
        self.medkits = []
        for _ in range(3):
            # Spawn somewhat near the player but random
            mx = self.pos[0] + random.uniform(-100, 100)
            mz = self.pos[2] + random.uniform(-100, 100)
            my = max(10, min(self.pos[1] + random.uniform(-50, 50), 200))
            self.medkits.append({
                'pos': [mx, my, mz],
                'rot': random.uniform(0, 360)
            })

game = Game()

# =============================================================================
# HELPER MATH & DRAWING
# =============================================================================
def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

def draw_text_string(x, y, text, color=(1, 1, 1)):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def draw_cube():
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1); glVertex3f(-0.5, -0.5, 0.5); glVertex3f(0.5, -0.5, 0.5); glVertex3f(0.5, 0.5, 0.5); glVertex3f(-0.5, 0.5, 0.5)
    glNormal3f(0, 0, -1); glVertex3f(-0.5, -0.5, -0.5); glVertex3f(-0.5, 0.5, -0.5); glVertex3f(0.5, 0.5, -0.5); glVertex3f(0.5, -0.5, -0.5)
    glNormal3f(-1, 0, 0); glVertex3f(-0.5, -0.5, -0.5); glVertex3f(-0.5, -0.5, 0.5); glVertex3f(-0.5, 0.5, 0.5); glVertex3f(-0.5, 0.5, -0.5)
    glNormal3f(1, 0, 0); glVertex3f(0.5, -0.5, -0.5); glVertex3f(0.5, 0.5, -0.5); glVertex3f(0.5, 0.5, 0.5); glVertex3f(0.5, -0.5, 0.5)
    glNormal3f(0, 1, 0); glVertex3f(-0.5, 0.5, -0.5); glVertex3f(-0.5, 0.5, 0.5); glVertex3f(0.5, 0.5, 0.5); glVertex3f(0.5, 0.5, -0.5)
    glNormal3f(0, -1, 0); glVertex3f(-0.5, -0.5, -0.5); glVertex3f(0.5, -0.5, -0.5); glVertex3f(0.5, -0.5, 0.5); glVertex3f(-0.5, -0.5, 0.5)
    glEnd()

def draw_seaweed(x, z, height, rot, scale):
    glPushMatrix()
    glTranslatef(x, 0, z) 
    glRotatef(rot, 0, 1, 0) 
    glScalef(scale, scale, scale) 
    glColor3f(0.1, 0.4, 0.1)
    for i in range(height):
        glPushMatrix()
        glTranslatef(0, 0.5 + i, 0) 
        glRotatef(i * 15 + math.sin(time.time() + x)*5, 0, 1, 0)
        glScalef(0.3, 1.0, 0.3)
        draw_cube()
        glPopMatrix()
    glPopMatrix()

def draw_shark(x, y, z, yaw, anim_time):
    if game.quadric is None: game.quadric = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(yaw, 0, 1, 0) 
    # Body
    glColor3f(0.4, 0.5, 0.6)
    glPushMatrix(); glScalef(1, 1, 2.5); gluSphere(game.quadric, 6, 10, 10); glPopMatrix()
    # Tail
    tail_wag = math.sin(anim_time * 8) * 20
    glPushMatrix(); glTranslatef(0, 0, -5); glRotatef(tail_wag, 0, 1, 0); glRotatef(180, 0, 1, 0); gluCylinder(game.quadric, 3, 0, 8, 10, 10); glPopMatrix()
    # Fin
    glPushMatrix(); glTranslatef(0, 4, 1); glScalef(0.5, 4, 2); gluSphere(game.quadric, 2, 5, 5); glPopMatrix()
    # Eyes
    glColor3f(0, 0, 0)
    glPushMatrix(); glTranslatef(2.5, 1, 3); gluSphere(game.quadric, 0.5, 5, 5); glTranslatef(-5, 0, 0); gluSphere(game.quadric, 0.5, 5, 5); glPopMatrix()
    glPopMatrix()

def draw_chest(x, y, z, rot):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rot, 0, 1, 0)
    glColor3f(0.8, 0.6, 0.1)
    glPushMatrix(); glScalef(8, 4, 5); draw_cube(); glPopMatrix()
    glColor3f(0.9, 0.7, 0.2)
    glPushMatrix(); glTranslatef(0, 2.5, 0); glScalef(8.5, 1.5, 5.5); draw_cube(); glPopMatrix()
    glPopMatrix()

def draw_medkit(x, y, z, rot):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rot, 0, 1, 0)
    
    # White Box
    glColor3f(1, 1, 1)
    glPushMatrix()
    glScalef(3, 2, 3)
    draw_cube()
    glPopMatrix()
    
    # Red Cross (Horizontal)
    glColor3f(1, 0, 0)
    glPushMatrix()
    glTranslatef(0, 1.1, 0) # Slightly above
    glScalef(2.5, 0.2, 0.8)
    draw_cube()
    glPopMatrix()
    
    # Red Cross (Vertical)
    glPushMatrix()
    glTranslatef(0, 1.1, 0)
    glScalef(0.8, 0.2, 2.5)
    draw_cube()
    glPopMatrix()
    
    glPopMatrix()

# =============================================================================
# UPDATE LOGIC
# =============================================================================
def update():
    current_time = time.time()
    dt = current_time - game.last_time
    game.last_time = current_time
    if dt > 0.1: dt = 0.1

    if game.state != GameState.PLAYING: return

    # --- MOVEMENT MATH ---
    yaw_rad = math.radians(game.yaw)
    pitch_rad = math.radians(game.pitch)
    
    front_x = math.cos(yaw_rad) * math.cos(pitch_rad)
    front_y = math.sin(pitch_rad)
    front_z = math.sin(yaw_rad) * math.cos(pitch_rad)
    right_x = -math.sin(yaw_rad)
    right_z = math.cos(yaw_rad)
    
    # Check Shift/Ctrl from stored modifier state
    is_shifting = (game.modifiers & GLUT_ACTIVE_SHIFT)
    is_ctrl = (game.modifiers & GLUT_ACTIVE_CTRL)
    
    speed = MOVE_SPEED
    if is_shifting and game.stamina > 0:
        speed *= SPRINT_MULTIPLIER
        game.stamina -= 30 * dt
        game.oxygen -= 5 * dt 
    else:
        if game.stamina < 100: game.stamina += 10 * dt

    speed *= dt * 60 

    # Keys
    if game.keys.get(b'w'):
        game.pos[0] += front_x * speed
        game.pos[1] += front_y * speed
        game.pos[2] += front_z * speed
    if game.keys.get(b's'):
        game.pos[0] -= front_x * speed
        game.pos[1] -= front_y * speed
        game.pos[2] -= front_z * speed
    if game.keys.get(b'a'):
        game.pos[0] -= right_x * speed
        game.pos[2] -= right_z * speed
    if game.keys.get(b'd'):
        game.pos[0] += right_x * speed
        game.pos[2] += right_z * speed
        
    # Up/Down Logic
    if game.keys.get(b' '): # Space = Up
        game.pos[1] += speed
    # Ctrl OR 'c' = Down
    if is_ctrl or game.keys.get(b'c'): 
        game.pos[1] -= speed

    game.pos[1] = max(6, min(game.pos[1], 500)) 
    
    game.oxygen -= 1.5 * dt
    if game.oxygen <= 0:
        game.oxygen = 0
        game.state = GameState.LOST

    # --- MEDKIT SPAWN/DESPAWN LOGIC ---
    # 1. Spawn if health < 50% and haven't spawned for this drop event yet
    if game.health < 50.0 and not game.medkits_spawned_for_low_health:
        game.spawn_medkits()
        game.medkits_spawned_for_low_health = True
    
    # 2. Despawn if health recovers to 100%
    if game.health >= 100.0 and game.medkits_spawned_for_low_health:
        game.medkits = [] # Clear medkits
        game.medkits_spawned_for_low_health = False

    # --- ENTITIES ---
    for s in game.sharks:
        dist_to_player = dist(game.pos, s['pos'])
        if dist_to_player < 250: 
            dx, dz = game.pos[0] - s['pos'][0], game.pos[2] - s['pos'][2]
            s['yaw'] = math.degrees(math.atan2(dx, dz))
            s['pos'][1] += math.copysign(s['speed']*0.6, game.pos[1] - s['pos'][1]) if abs(game.pos[1] - s['pos'][1]) > 2 else 0
            
        s_rad = math.radians(s['yaw'])
        s['pos'][0] += math.sin(s_rad) * s['speed']
        s['pos'][2] += math.cos(s_rad) * s['speed']

        if dist_to_player < 18 and not game.invincible: 
            game.health -= 25
            game.invincible = True
            game.invincible_timer = 2.0
            game.pos[0] += math.sin(s_rad) * 25
            game.pos[2] += math.cos(s_rad) * 25
            if game.health <= 0: game.state = GameState.LOST

    # Treasure Collision
    active_count = 0
    for t in game.treasures:
        if t['active']:
            active_count += 1
            if dist(game.pos, t['pos']) < 22: 
                t['active'] = False
                game.score += 100
                game.oxygen = min(100, game.oxygen + 30)
    if active_count == 0: game.state = GameState.WON

    # Medkit Collision
    for m in game.medkits[:]: # Iterate copy to remove safely
        if dist(game.pos, m['pos']) < 15:
            game.health = min(100, game.health + 50) # Heal 50
            game.medkits.remove(m)

    if game.invincible:
        game.invincible_timer -= dt
        if game.invincible_timer <= 0: game.invincible = False
    
    glutPostRedisplay()

# =============================================================================
# RENDERING
# =============================================================================
def draw_hud():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    def draw_bar(x, y, w, h, val, max_val, color, label):
        # Draw Label
        draw_text_string(x, y + h + 5, label, (1,1,1))
        # Draw Background
        glColor3f(0.2, 0.2, 0.2); glRectf(x, y, x+w, y+h)
        # Draw Bar
        glColor3f(*color); glRectf(x, y, x+(val/max_val)*w, y+h)

    if game.state == GameState.PLAYING:
        # Crosshair
        glColor3f(1,1,1); cx, cy = WINDOW_WIDTH/2, WINDOW_HEIGHT/2
        glRectf(cx-2, cy-10, cx+2, cy+10); glRectf(cx-10, cy-2, cx+10, cy+2)
        
        # Bars with Labels
        draw_bar(20, 100, 200, 20, game.oxygen, 100, (0, 1, 1), "OXYGEN") 
        draw_bar(20, 60, 200, 20, game.health, 100, (1, 0, 0), "HEALTH") 
        draw_bar(20, 25, 200, 10, game.stamina, 100, (1, 1, 0), "STAMINA") 
        
        # Medkit Warning
        if game.medkits_spawned_for_low_health and len(game.medkits) > 0:
             draw_text_string(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT - 100, "MEDKITS SPAWNED!", (1, 0, 0))

        # Score
        draw_text_string(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 40, f"SCORE: {game.score}", (1, 1, 0))

    elif game.state == GameState.WON:
        glColor3f(0, 1, 0)
        draw_text_string(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 + 20, "MISSION COMPLETE!", (0,1,0))
        draw_text_string(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 - 20, f"FINAL SCORE: {game.score}", (1,1,1))
        draw_text_string(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 - 60, "PRESS 'R' TO RESTART", (1,1,0))
        
    elif game.state == GameState.LOST:
        glColor3f(1, 0, 0)
        draw_text_string(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 + 20, "GAME OVER", (1,0,0))
        draw_text_string(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 - 20, f"FINAL SCORE: {game.score}", (1,1,1))
        draw_text_string(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 - 60, "PRESS 'R' TO RESTART", (1,1,0))

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glEnable(GL_DEPTH_TEST)

def display():
    if game.quadric is None: game.quadric = gluNewQuadric()
    glClearColor(0.02, 0.05, 0.1, 1.0) 
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    
    yaw_rad = math.radians(game.yaw)
    pitch_rad = math.radians(game.pitch)
    look_x = game.pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad)
    look_y = game.pos[1] + math.sin(pitch_rad)
    look_z = game.pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad)
    gluLookAt(game.pos[0], game.pos[1], game.pos[2], look_x, look_y, look_z, 0, 1, 0)

    glEnable(GL_LIGHTING); glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHT0); glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.2, 1.0]); glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.2, 0.2, 0.3, 1.0])
    
    glEnable(GL_LIGHT1); glLightfv(GL_LIGHT1, GL_POSITION, [game.pos[0], game.pos[1], game.pos[2], 1.0])
    dir_x = look_x - game.pos[0]; dir_y = look_y - game.pos[1]; dir_z = look_z - game.pos[2]
    glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, [dir_x, dir_y, dir_z])
    glLightf(GL_LIGHT1, GL_SPOT_CUTOFF, 50.0); glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0, 1.0, 0.9, 1.0])
    
    glEnable(GL_FOG); glFogfv(GL_FOG_COLOR, [0.02, 0.05, 0.1, 1.0]); glFogf(GL_FOG_DENSITY, FOG_DENSITY)

    # Floor
    glColor3f(0.7, 0.6, 0.4); glBegin(GL_QUADS); glNormal3f(0, 1, 0)
    s = 600
    for x in range(-s, s, 100):
        for z in range(-s, s, 100):
            if (x*z)%3 == 0: glColor3f(0.65, 0.55, 0.35)
            else: glColor3f(0.7, 0.6, 0.4)
            glVertex3f(x, 0, z); glVertex3f(x+100, 0, z); glVertex3f(x+100, 0, z+100); glVertex3f(x, 0, z+100)
    glEnd()

    for sw in game.seaweeds: draw_seaweed(sw['pos'][0], sw['pos'][1], sw['height'], sw['rot'], sw['scale'])
    for t in game.treasures:
        if t['active']:
            bob = math.sin(time.time() * 2) * 1.5
            draw_chest(t['pos'][0], t['pos'][1] + bob, t['pos'][2], t['rot'])
            
    # Draw Medkits
    for m in game.medkits:
        bob = math.sin(time.time() * 3) * 0.5
        draw_medkit(m['pos'][0], m['pos'][1] + bob, m['pos'][2], m['rot'] + time.time()*20)

    for s in game.sharks: draw_shark(s['pos'][0], s['pos'][1], s['pos'][2], s['yaw'], time.time() + s['anim_offset'])
        
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.7, 0.8, 1.0, 0.3)
    for b in game.bubbles:
        glPushMatrix()
        rise = (time.time() * 10) % 400
        curr_y = (b['pos'][1] + rise) % 400
        glTranslatef(b['pos'][0], curr_y, b['pos'][2]); gluSphere(game.quadric, b['size'], 5, 5); glPopMatrix()
    glDisable(GL_BLEND)
    draw_hud()
    glutSwapBuffers()

# =============================================================================
# GLUT CALLBACKS
# =============================================================================
def keyboard_down(key, x, y):
    if key == b'\x1b': sys.exit()
    # RESTART LOGIC
    if key == b'r' or key == b'R':
        game.reset_game()
        
    game.keys[key] = True
    game.modifiers = glutGetModifiers()

def keyboard_up(key, x, y):
    game.keys[key] = False
    game.modifiers = glutGetModifiers()

def mouse_motion(x, y):
    game.modifiers = glutGetModifiers()
    if game.ignore_next_mouse:
        game.ignore_next_mouse = False
        return

    if game.state != GameState.PLAYING: return

    cx, cy = game.center_x, game.center_y
    dx = x - cx
    dy = cy - y 

    game.yaw += dx * MOUSE_SENSITIVITY
    game.pitch += dy * MOUSE_SENSITIVITY
    
    if game.pitch > 89.0: game.pitch = 89.0
    if game.pitch < -89.0: game.pitch = -89.0

    if dx != 0 or dy != 0:
        game.ignore_next_mouse = True
        glutWarpPointer(cx, cy)

# =============================================================================
# MAIN
# =============================================================================
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Abyssal Dive: Oxygen Rush")
    
    glEnable(GL_DEPTH_TEST)
    glutSetCursor(GLUT_CURSOR_NONE) 
    
    glutDisplayFunc(display)
    glutIdleFunc(update)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    
    glutWarpPointer(int(WINDOW_WIDTH/2), int(WINDOW_HEIGHT/2))
    glutMainLoop()

if __name__ == "__main__":
    main()
