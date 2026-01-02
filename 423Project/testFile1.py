import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import sys
import time


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
MOUSE_SENSITIVITY = 0.1
MOVE_SPEED = 1.5
SPRINT_MULTIPLIER = 2.5
FOG_DENSITY = 0.005


class GameState:
    PLAYING = 0
    WON = 1
    LOST = 2

class Game:
    def __init__(self):
        self.state = GameState.PLAYING
        
        # Camera / Player
        self.pos = [0, 10, 50]    # X, Y, Z (Start slightly higher)
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
        
        # Input State
        self.keys = {}
        self.first_mouse = True
        self.last_x = WINDOW_WIDTH / 2
        self.last_y = WINDOW_HEIGHT / 2

        # Entities
        self.sharks = []
        self.treasures = []
        self.bubbles = []
        self.seaweeds = [] 
        
        # Rendering
        self.quadric = None 

        self.generate_world()

    def generate_world(self):
        # Tutorial Chest (Raised Y to 5)
        self.treasures = []
        self.treasures.append({
            'pos': [0, 5, -40],
            'active': True,
            'rot': 0
        })

        # Random Chests (Raised Y to 5 to prevent clipping during bob animation)
        for _ in range(15):
            self.treasures.append({
                'pos': [random.uniform(-400, 400), 5, random.uniform(-400, 400)],
                'active': True,
                'rot': random.uniform(0, 360)
            })

        # Tutorial Shark
        self.sharks = []
        self.sharks.append({
            'pos': [60, 40, -60],
            'yaw': 0,
            'speed': 0.6,
            'anim_offset': 0
        })

        # Random Sharks
        for _ in range(10):
            self.sharks.append({
                'pos': [random.uniform(-400, 400), random.uniform(10, 250), random.uniform(-400, 400)],
                'yaw': random.uniform(0, 360),
                'speed': random.uniform(0.5, 1.2),
                'anim_offset': random.uniform(0, 10)
            })
            
        # Ambient Bubbles
        self.bubbles = []
        for _ in range(200):
            self.bubbles.append({
                'pos': [random.uniform(-500, 500), random.uniform(0, 400), random.uniform(-500, 500)],
                'size': random.uniform(0.5, 2.0),
                'speed': random.uniform(0.1, 0.5)
            })

        # --- Generate DENSER Seaweed ---
        self.seaweeds = []
        # Increased from 80 to 350 for denser look
        for _ in range(350): 
            self.seaweeds.append({
                'pos': [random.uniform(-450, 450), random.uniform(-450, 450)],
                'height': random.randint(4, 8), 
                'rot': random.uniform(0, 360),  
                'scale': random.uniform(0.8, 1.2) 
            })

game = Game()

# =============================================================================
# HELPER MATH
# =============================================================================
def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

# =============================================================================
# 3D DRAWING FUNCTIONS
# =============================================================================
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
        # Slight twist animation
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
    glPushMatrix()
    glScalef(1, 1, 2.5) 
    gluSphere(game.quadric, 6, 10, 10) 
    glPopMatrix()
    
    # Tail
    tail_wag = math.sin(anim_time * 8) * 20
    glPushMatrix()
    glTranslatef(0, 0, -5)
    glRotatef(tail_wag, 0, 1, 0)
    glRotatef(180, 0, 1, 0) 
    gluCylinder(game.quadric, 3, 0, 8, 10, 10) 
    glPopMatrix()
    
    # Fin
    glPushMatrix()
    glTranslatef(0, 4, 1)
    glScalef(0.5, 4, 2)
    gluSphere(game.quadric, 2, 5, 5) 
    glPopMatrix()

    # Eyes
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(2.5, 1, 3); gluSphere(game.quadric, 0.5, 5, 5) 
    glTranslatef(-2.5, 1, 3); gluSphere(game.quadric, 0.5, 5, 5) 
    glPopMatrix()
    glPopMatrix()

def draw_chest(x, y, z, rot):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rot, 0, 1, 0)
    
    # Gold Base
    glColor3f(0.8, 0.6, 0.1)
    glPushMatrix()
    glScalef(8, 4, 5) # Height is 4, so extends 2 down from center
    draw_cube()
    glPopMatrix()
    
    # Lid
    glColor3f(0.9, 0.7, 0.2)
    glPushMatrix()
    glTranslatef(0, 2.5, 0)
    glScalef(8.5, 1.5, 5.5)
    draw_cube()
    glPopMatrix()
    glPopMatrix()

# =============================================================================
# UPDATE LOGIC
# =============================================================================
def update(dt):
    if game.state != GameState.PLAYING: return

    # --- MOVEMENT ---
    yaw_rad = math.radians(game.yaw)
    pitch_rad = math.radians(game.pitch)
    
    front_x = math.cos(yaw_rad) * math.cos(pitch_rad)
    front_y = math.sin(pitch_rad)
    front_z = math.sin(yaw_rad) * math.cos(pitch_rad)
    
    right_x = math.sin(yaw_rad - 3.14159/2.0)
    right_z = -math.cos(yaw_rad - 3.14159/2.0)
    
    speed = MOVE_SPEED
    if game.keys.get(glfw.KEY_LEFT_SHIFT) and game.stamina > 0:
        speed *= SPRINT_MULTIPLIER
        game.stamina -= 30 * dt
        game.oxygen -= 5 * dt 
        game.sprinting = True
    else:
        game.sprinting = False
        if game.stamina < 100: game.stamina += 10 * dt

    speed *= dt * 60 

    if game.keys.get(glfw.KEY_W):
        game.pos[0] += front_x * speed
        game.pos[1] += front_y * speed
        game.pos[2] += front_z * speed
    if game.keys.get(glfw.KEY_S):
        game.pos[0] -= front_x * speed
        game.pos[1] -= front_y * speed
        game.pos[2] -= front_z * speed
    if game.keys.get(glfw.KEY_A):
        game.pos[0] -= right_x * speed
        game.pos[2] -= right_z * speed
    if game.keys.get(glfw.KEY_D):
        game.pos[0] += right_x * speed
        game.pos[2] += right_z * speed
    if game.keys.get(glfw.KEY_SPACE): 
        game.pos[1] += speed
    if game.keys.get(glfw.KEY_LEFT_CONTROL): 
        game.pos[1] -= speed

    # Floor Collision
    game.pos[1] = max(6, min(game.pos[1], 500)) 
    
    game.oxygen -= 1.5 * dt
    if game.oxygen <= 0:
        game.oxygen = 0
        game.state = GameState.LOST

    # --- SHARK AI (Vertical movement included) ---
    for s in game.sharks:
        dist_to_player = dist(game.pos, s['pos'])
        current_speed = s['speed']
        
        # Chase Logic
        if dist_to_player < 250: 
            dx = game.pos[0] - s['pos'][0]
            dz = game.pos[2] - s['pos'][2]
            target_angle = math.degrees(math.atan2(dx, dz))
            s['yaw'] = target_angle
            current_speed *= 1.6 

            # Vertical movement
            dy = game.pos[1] - s['pos'][1]
            vert_speed = current_speed * 0.4 
            if abs(dy) > 2.0: 
                 s['pos'][1] += math.copysign(vert_speed, dy)
        else:
            # Patrol Logic
            if abs(s['pos'][0]) > 450 or abs(s['pos'][2]) > 450:
                s['yaw'] += 180
            
            if s['pos'][1] < 30: s['pos'][1] += 0.1
            if s['pos'][1] > 150: s['pos'][1] -= 0.1

        # Apply Horizontal Movement
        s_rad = math.radians(s['yaw'])
        move_x = math.sin(s_rad) * current_speed
        move_z = math.cos(s_rad) * current_speed
        
        s['pos'][0] += move_x
        s['pos'][2] += move_z

        # Collision Damage
        if dist_to_player < 18 and not game.invincible: 
            game.health -= 25
            game.invincible = True
            game.invincible_timer = 2.0
            game.pos[0] += move_x * 25
            game.pos[2] += move_z * 25
            game.pos[1] += 5 
            if game.health <= 0: game.state = GameState.LOST

    # --- TREASURE LOGIC ---
    active_count = 0
    for t in game.treasures:
        if t['active']:
            active_count += 1
            if dist(game.pos, t['pos']) < 22: 
                t['active'] = False
                game.score += 100
                game.oxygen = min(100, game.oxygen + 30)
    
    if active_count == 0:
        game.state = GameState.WON

    if game.invincible:
        game.invincible_timer -= dt
        if game.invincible_timer <= 0: game.invincible = False

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
    
    def draw_bar(x, y, w, h, val, max_val, color):
        glColor3f(0.2, 0.2, 0.2)
        glRectf(x, y, x+w, y+h)
        glColor3f(*color)
        curr_w = (val / max_val) * w
        glRectf(x, y, x+curr_w, y+h)

    if game.state == GameState.PLAYING:
        glColor3f(1,1,1)
        cx, cy = WINDOW_WIDTH/2, WINDOW_HEIGHT/2
        glRectf(cx-2, cy-10, cx+2, cy+10)
        glRectf(cx-10, cy-2, cx+10, cy+2)

        draw_bar(20, WINDOW_HEIGHT-40, 200, 20, game.oxygen, 100, (0, 1, 1)) 
        draw_bar(20, WINDOW_HEIGHT-70, 200, 20, game.health, 100, (1, 0, 0)) 
        draw_bar(20, WINDOW_HEIGHT-100, 200, 10, game.stamina, 100, (1, 1, 0)) 

    elif game.state == GameState.WON:
        glColor3f(0, 1, 0)
        glBegin(GL_POLYGON)
        glVertex2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2)
        glVertex2f(WINDOW_WIDTH/2 - 20, WINDOW_HEIGHT/2 - 50)
        glVertex2f(WINDOW_WIDTH/2 + 80, WINDOW_HEIGHT/2 + 80)
        glVertex2f(WINDOW_WIDTH/2 + 50, WINDOW_HEIGHT/2 + 100)
        glVertex2f(WINDOW_WIDTH/2 - 20, WINDOW_HEIGHT/2 - 10)
        glVertex2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2 + 40)
        glEnd()

    elif game.state == GameState.LOST:
        glColor3f(1, 0, 0)
        cx, cy = WINDOW_WIDTH/2, WINDOW_HEIGHT/2
        s = 100
        glBegin(GL_QUADS)
        glVertex2f(cx-s, cy-s+20); glVertex2f(cx-s+20, cy-s); glVertex2f(cx+s, cy+s-20); glVertex2f(cx+s-20, cy+s)
        glVertex2f(cx-s, cy+s-20); glVertex2f(cx-s+20, cy+s); glVertex2f(cx+s, cy-s+20); glVertex2f(cx+s-20, cy-s)
        glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)

def display():
    if game.quadric is None: game.quadric = gluNewQuadric()

    glClearColor(0.02, 0.05, 0.1, 1.0) 
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    yaw_rad = math.radians(game.yaw)
    pitch_rad = math.radians(game.pitch)
    
    look_x = game.pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad)
    look_y = game.pos[1] + math.sin(pitch_rad)
    look_z = game.pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad)
    
    gluLookAt(game.pos[0], game.pos[1], game.pos[2],
              look_x, look_y, look_z,
              0, 1, 0)

    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.2, 0.2, 0.3, 1.0])
    
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_POSITION, [game.pos[0], game.pos[1], game.pos[2], 1.0])
    dir_x = look_x - game.pos[0]
    dir_y = look_y - game.pos[1]
    dir_z = look_z - game.pos[2]
    glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, [dir_x, dir_y, dir_z])
    glLightf(GL_LIGHT1, GL_SPOT_CUTOFF, 50.0) 
    glLightf(GL_LIGHT1, GL_SPOT_EXPONENT, 2.0)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0, 1.0, 0.9, 1.0])
    
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, [0.02, 0.05, 0.1, 1.0])
    glFogf(GL_FOG_DENSITY, FOG_DENSITY)

    # Floor
    glColor3f(0.7, 0.6, 0.4) 
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    s = 600
    for x in range(-s, s, 100):
        for z in range(-s, s, 100):
            if (x*z)%3 == 0: glColor3f(0.65, 0.55, 0.35)
            else: glColor3f(0.7, 0.6, 0.4)
            glVertex3f(x, 0, z)
            glVertex3f(x+100, 0, z)
            glVertex3f(x+100, 0, z+100)
            glVertex3f(x, 0, z+100)
    glEnd()

    # Draw Seaweed
    for sw in game.seaweeds:
        draw_seaweed(sw['pos'][0], sw['pos'][1], sw['height'], sw['rot'], sw['scale'])

    for t in game.treasures:
        if t['active']:
            # Bobbing animation (sin wave from -1.5 to +1.5)
            bob = math.sin(time.time() * 2) * 1.5
            # Base Y is 5. Lowest point is 5 - 1.5 = 3.5. Safe above ground.
            draw_chest(t['pos'][0], t['pos'][1] + bob, t['pos'][2], t['rot'])
            
    for s in game.sharks:
        draw_shark(s['pos'][0], s['pos'][1], s['pos'][2], s['yaw'], time.time() + s['anim_offset'])
        
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Bubbles
    glColor4f(0.7, 0.8, 1.0, 0.3)
    for b in game.bubbles:
        glPushMatrix()
        rise = (time.time() * 10) % 400
        curr_y = (b['pos'][1] + rise) % 400
        glTranslatef(b['pos'][0], curr_y, b['pos'][2])
        gluSphere(game.quadric, b['size'], 5, 5) 
        glPopMatrix()
    glDisable(GL_BLEND)
    
    draw_hud()

# =============================================================================
# INPUT CALLBACKS
# =============================================================================
def mouse_callback(window, xpos, ypos):
    if game.state != GameState.PLAYING: return
    
    if game.first_mouse:
        game.last_x = xpos
        game.last_y = ypos
        game.first_mouse = False

    xoffset = xpos - game.last_x
    yoffset = game.last_y - ypos 
    game.last_x = xpos
    game.last_y = ypos

    xoffset *= MOUSE_SENSITIVITY
    yoffset *= MOUSE_SENSITIVITY

    game.yaw += xoffset
    game.pitch += yoffset

    if game.pitch > 89.0: game.pitch = 89.0
    if game.pitch < -89.0: game.pitch = -89.0

def key_callback(window, key, scancode, action, mods):
    if action == glfw.PRESS:
        game.keys[key] = True
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
    elif action == glfw.RELEASE:
        game.keys[key] = False

# =============================================================================
# MAIN LOOP
# =============================================================================
def main():
    if not glfw.init(): return
    
    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Abyssal Dive: Oxygen Rush", None, None)
    if not window: glfw.terminate(); return

    glfw.make_context_current(window)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_key_callback(window, key_callback)
    
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    
    glEnable(GL_DEPTH_TEST)
    
    last_frame = time.time()
    
    while not glfw.window_should_close(window):
        current_frame = time.time()
        dt = current_frame - last_frame
        last_frame = current_frame
        
        glfw.poll_events()
        update(dt)
        display()
        glfw.swap_buffers(window)
        
    glfw.terminate()

if __name__ == "__main__":
    main()
