import pygame
import psutil
import math
import random

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NeoBench: Live Hardware Storage Mapper")
clock = pygame.time.Clock()

# Color Palette
BG_COLOR = (10, 10, 18)
TEXT_COLOR = (0, 255, 255) # Cyan
NODE_COLOR = (255, 0, 128) # Pink
PARTICLE_COLOR = (0, 255, 128) # Neon Green

class NodeParticle:
    """Particles that shoot out when a hardware state changes."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.alpha = 255
        self.color = PARTICLE_COLOR

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 8 # Fade out over time

    def draw(self, surface):
        if self.alpha > 0:
            p_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            p_surface.fill((*self.color, self.alpha))
            surface.blit(p_surface, (int(self.x), int(self.y)))

def get_current_drives():
    """Scan OS mount points dynamically."""
    try:
        return [d.device for d in psutil.disk_partitions()]
    except:
        return ["C:\\"] # Fallback

# Initial state scanning
tracked_drives = get_current_drives()
particles = []
pulse_angle = 0

# Font Configuration
font = pygame.font.SysFont("monospace", 16)
title_font = pygame.font.SysFont("monospace", 22, bold=True)

running = True
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Hardware Diagnostic Scan
    current_scanned = get_current_drives()
    
    # Check if a drive was plugged in or pulled out
    if len(current_scanned) != len(tracked_drives):
        # Trigger visual explosion effect in the center
        for _ in range(100):
            particles.append(NodeParticle(WIDTH // 2, HEIGHT // 2 + 50))
        tracked_drives = current_scanned

    # 3. Physics & Visual Updates
    pulse_angle += 0.05
    pulse_scale = 1.0 + math.sin(pulse_angle) * 0.1 # Pulsing glow multiplier

    for p in particles[:]:
        p.update()
        if p.alpha <= 0:
            particles.remove(p)

    # 4. Rendering Grid
    screen.fill(BG_COLOR)

    # Draw Status Header Dashboard
    title_text = title_font.render("// DIAGNOSTIC BENCH: STORAGE MATRIX", True, TEXT_COLOR)
    status_sub = font.render(f"ACTIVE MOUNTS DETECTED: {len(tracked_drives)} | STATUS: MONITORING...", True, (255, 255, 255))
    screen.blit(title_text, (30, 30))
    screen.blit(status_sub, (30, 65))
    pygame.draw.line(screen, TEXT_COLOR, (30, 95), (WIDTH - 30, 95), 2)

    # Render Drive Nodes Layout
    start_x = 120
    spacing = 180
    node_y = HEIGHT // 2 + 50

    for i, drive_name in enumerate(tracked_drives):
        current_node_x = start_x + (i * spacing)

        # Draw connecting wiring bus trace line
        pygame.draw.line(screen, (30, 40, 60), (current_node_x, 95), (current_node_x, node_y - 40), 1)

        # Calculate dynamic pulsing size for the node framework
        radius = int(35 * pulse_scale)
        
        # Draw glowing geometry rings
        pygame.draw.circle(screen, (40, 15, 45), (current_node_x, node_y), radius + 10)
        pygame.draw.circle(screen, NODE_COLOR, (current_node_x, node_y), radius, 2)
        pygame.draw.circle(screen, (255, 255, 255), (current_node_x, node_y), 6)

        # Try pulling usage stats for the mapped block node
        try:
            usage = psutil.disk_usage(drive_name)
            percent_used = usage.percent
            space_text = f"{percent_used}% USED"
        except:
            space_text = "LOCKED/ERR"

        # Label Text Cards below the nodes
        label = font.render(f"MOUNT: {drive_name}", True, TEXT_COLOR)
        stats = font.render(space_text, True, (200, 200, 200))
        
        screen.blit(label, (current_node_x - 50, node_y + 55))
        screen.blit(stats, (current_node_x - 45, node_y + 75))

    # Render active shockwave particles
    for p in particles:
        p.draw(screen)

    # Clean Frame buffer Sync
    pygame.display.flip()
    clock.tick(30) # 30 FPS scanning sweep rate is gentle on CPU loops

pygame.quit()