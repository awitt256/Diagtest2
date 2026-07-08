import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Setup Screen
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Particle Gravity Sandbox")
clock = pygame.time.Clock()

# Particle Configuration
NUM_PARTICLES = 1500
MAX_SPEED = 8
GRAVITY_STRENGTH = 0.3
FRICTION = 0.99  # Slightly slows particles down over time so they don't swing forever

class Particle:
    def __init__(self):
        self.reset()
        # Random initial position anywhere on screen
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)

    def reset(self):
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        # Give them vibrant neon colors (cyans, purples, pinks)
        self.color = random.choice([
            (0, 255, 255),   # Cyan
            (255, 0, 128),   # Hot Pink
            (128, 0, 255),   # Purple
            (0, 255, 128)    # Neon Green
        ])
        self.size = random.randint(1, 3)

    def update(self, target_x, target_y, attract=True):
        # Calculate distance vectors to the target (mouse)
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance > 5:  # Prevent division by zero / extreme slingshots
            # Normalize vector to get direction
            fx = dx / distance
            fy = dy / distance
            
            # Gravity formula (pulls harder the closer they get)
            force = GRAVITY_STRENGTH * (100 / max(distance, 20))
            
            if attract:
                self.vx += fx * force
                self.vy += fy * force
            else:
                # Repel mode (Right click/Shockwave)
                self.vx -= fx * force * 5
                self.vy -= fy * force * 5

        # Apply speeds and environmental friction
        self.vx *= FRICTION
        self.vy *= FRICTION
        
        # Limit speed capping
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            self.vx = (self.vx / speed) * MAX_SPEED
            self.vy = (self.vy / speed) * MAX_SPEED

        self.x += self.vx
        self.y += self.vy

        # Soft bounce boundaries
        if self.x < 0 or self.x > WIDTH: self.vx *= -0.5
        if self.y < 0 or self.y > HEIGHT: self.vy *= -0.5

    def draw(self, surface):
        # Draw particle as a simple clean circle
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


# Instantiate particle array
particles = [Particle() for _ in range(NUM_PARTICLES)]

# Main Loop
running = True
repel_mode = False

while running:
    # Handle Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click tracks normally, holds down
                pass
            elif event.button == 3: # Right click triggers an explosion push
                repel_mode = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                repel_mode = False

    # Get Mouse Position
    mx, my = pygame.mouse.get_pos()

    # Create Motion Blur Effect (Draw a translucent dark rectangle instead of clearing completely)
    trail_surface = pygame.Surface((WIDTH, HEIGHT))
    trail_surface.set_alpha(35) # Lower = longer glowing light trails
    trail_surface.fill((10, 10, 15)) # Deep space dark blue/black background
    screen.blit(trail_surface, (0,0))

    # Update and Draw Particles
    for p in particles:
        p.update(mx, my, attract=not repel_mode)
        p.draw(screen)

    # Frame Management
    pygame.display.flip()
    clock.tick(60) # Locked smooth 60fps frame updates

pygame.quit()