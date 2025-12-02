import pygame
import random

# ------------- BASIC SETUP -------------
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    # sound might not work on some setups; game still runs
    pass

WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("T-Rex Runner (Pygame)")

clock = pygame.time.Clock()
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_COLOR = (120, 120, 120)
DINO_COLOR = (50, 180, 50)
DINO_DUCK_COLOR = (40, 140, 40)
CACTUS_COLOR = (30, 100, 30)
CLOUD_COLOR = (230, 230, 230)
SKY_DAY = (235, 245, 255)
SKY_NIGHT = (15, 20, 40)

GROUND_Y = 320  # y position of ground line

font = pygame.font.SysFont(None, 32)


# --------- optional sound loading ----------
def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None


jump_sound = load_sound("jump.wav")
hit_sound = load_sound("hit.wav")
point_sound = load_sound("point.wav")


# ------------- DINO CLASS -------------
class Dino:
    def __init__(self):
        self.stand_width = 40
        self.stand_height = 50
        self.duck_width = 60
        self.duck_height = 30

        self.x = 80
        self.y = GROUND_Y - self.stand_height
        self.rect = pygame.Rect(self.x, self.y, self.stand_width, self.stand_height)

        self.vel_y = 0
        self.gravity = 1.1
        self.jump_strength = -20
        self.on_ground = True
        self.ducking = False

        # animation timers
        self.leg_timer = 0
        self.leg_state = 0  # 0 or 1

    def jump(self):
        if self.on_ground and not self.ducking:
            self.vel_y = self.jump_strength
            self.on_ground = False
            if jump_sound:
                jump_sound.play()

    def set_duck(self, duck):
        # only allow duck on ground
        if not self.on_ground and duck:
            return
        if duck and not self.ducking:
            # switch to duck rect
            bottom = self.rect.bottom
            self.rect.width = self.duck_width
            self.rect.height = self.duck_height
            self.rect.bottom = bottom
            self.ducking = True
        elif not duck and self.ducking:
            # switch to stand rect
            bottom = self.rect.bottom
            self.rect.width = self.stand_width
            self.rect.height = self.stand_height
            self.rect.bottom = bottom
            self.ducking = False

    def update(self, dt):
        # apply gravity
        self.vel_y += self.gravity
        self.rect.y += int(self.vel_y)

        # clamp to ground
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        # leg animation
        if self.on_ground:
            self.leg_timer += dt
            if self.leg_timer > 80:
                self.leg_timer = 0
                self.leg_state = 1 - self.leg_state
        else:
            self.leg_state = 0

    def draw(self, surf, night_mode=False):
        # body
        color = DINO_DUCK_COLOR if self.ducking else DINO_COLOR
        body_rect = self.rect.copy()
        pygame.draw.rect(surf, color, body_rect, border_radius=4)

        # head
        if self.ducking:
            head_rect = pygame.Rect(
                body_rect.right - 20, body_rect.top + 2, 18, body_rect.height - 8
            )
        else:
            head_rect = pygame.Rect(
                body_rect.right - 15, body_rect.top - 18, 18, 18
            )
        pygame.draw.rect(surf, color, head_rect, border_radius=4)

        # eye
        eye_color = WHITE if not night_mode else (220, 220, 220)
        pupil_color = BLACK if not night_mode else (10, 10, 10)
        eye_center = (head_rect.centerx + 3, head_rect.centery - 3)
        pygame.draw.circle(surf, eye_color, eye_center, 4)
        pygame.draw.circle(surf, pupil_color, (eye_center[0] + 1, eye_center[1]), 2)

        # legs / feet
        foot_y = body_rect.bottom
        if self.ducking:
            pygame.draw.line(surf, BLACK, (body_rect.left + 10, foot_y),
                             (body_rect.left + 20, foot_y), 2)
            pygame.draw.line(surf, BLACK, (body_rect.left + 30, foot_y),
                             (body_rect.left + 40, foot_y), 2)
        else:
            offset = 6 if self.leg_state == 0 else -6
            pygame.draw.line(surf, BLACK, (body_rect.left + 10, foot_y),
                             (body_rect.left + 10 + offset, foot_y + 8), 2)
            pygame.draw.line(surf, BLACK, (body_rect.left + 25, foot_y),
                             (body_rect.left + 25 - offset, foot_y + 8), 2)


# ------------- OBSTACLE CLASS -------------
class Cactus:
    def __init__(self, speed):
        self.kind = random.choice(["small", "big", "double"])
        if self.kind == "small":
            self.width = 20
            self.height = 40
        elif self.kind == "big":
            self.width = 30
            self.height = 60
        else:  # double
            self.width = 45
            self.height = 55

        self.x = WIDTH + 20
        self.y = GROUND_Y - self.height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, CACTUS_COLOR, self.rect, border_radius=4)
        if self.kind in ("big", "double"):
            arm_height = int(self.height * 0.4)
            left_arm = pygame.Rect(self.rect.left - 6,
                                   self.rect.bottom - arm_height - 5,
                                   8, arm_height)
            right_arm = pygame.Rect(self.rect.right - 2,
                                    self.rect.bottom - arm_height - 12,
                                    8, arm_height + 5)
            pygame.draw.rect(surf, CACTUS_COLOR, left_arm, border_radius=4)
            pygame.draw.rect(surf, CACTUS_COLOR, right_arm, border_radius=4)

    def is_off_screen(self):
        return self.rect.right < 0


# ------------- CLOUD CLASS -------------
class Cloud:
    def __init__(self, speed):
        self.x = WIDTH + random.randint(0, 200)
        self.y = random.randint(50, 180)
        self.speed = speed * 0.4
        self.width = random.randint(40, 80)
        self.height = random.randint(18, 30)

    def update(self):
        self.x -= self.speed

    def draw(self, surf, night_mode=False):
        color = CLOUD_COLOR if not night_mode else (180, 180, 200)
        rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.ellipse(surf, color, rect)

    def is_off_screen(self):
        return self.x + self.width < 0


# ------------- GAME FUNCTIONS -------------
def draw_ground(surf, offset, night_mode=False):
    y = GROUND_Y
    ground_top_color = (180, 180, 180) if not night_mode else (120, 120, 120)
    pygame.draw.rect(surf, ground_top_color, (0, y, WIDTH, HEIGHT - y))

    line_color = (60, 60, 60) if not night_mode else (200, 200, 200)
    for x in range(-offset, WIDTH, 40):
        pygame.draw.line(surf, line_color, (x, y), (x + 20, y), 2)


def draw_text_center(text, y, night_mode=False):
    text_color = BLACK if not night_mode else (230, 230, 230)
    surf = font.render(text, True, text_color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    screen.blit(surf, rect)


def draw_text_left(text, y, night_mode=False):
    text_color = BLACK if not night_mode else (230, 230, 230)
    surf = font.render(text, True, text_color)
    rect = surf.get_rect(topleft=(10, y))
    screen.blit(surf, rect)


def reset_game():
    dino = Dino()
    obstacles = []
    clouds = []
    score = 0
    speed = 8
    spawn_timer = 0
    cloud_timer = 0
    return dino, obstacles, clouds, score, speed, spawn_timer, cloud_timer


# ------------- MAIN LOOP -------------
def main():
    running = True

    # game_state: "start", "play", "game_over"
    game_state = "start"

    dino, obstacles, clouds, score, speed, spawn_timer, cloud_timer = reset_game()
    ground_offset = 0
    night_mode = False
    high_score = 0
    last_checkpoint = 0  # for 100-point sound

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if game_state == "start":
                        # start the game
                        game_state = "play"
                    elif game_state == "play":
                        dino.jump()
                    elif game_state == "game_over":
                        # restart
                        dino, obstacles, clouds, score, speed, spawn_timer, cloud_timer = reset_game()
                        game_state = "play"
                        last_checkpoint = 0

                elif event.key == pygame.K_DOWN:
                    if game_state == "play":
                        dino.set_duck(True)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    dino.set_duck(False)

        # ----- UPDATE -----
        # clouds always move (even at start / game over, for nice look)
        cloud_timer += dt
        if cloud_timer > random.randint(1200, 2500) and game_state == "play":
            clouds.append(Cloud(speed))
            cloud_timer = 0

        for cl in clouds:
            cl.update()
        clouds = [cl for cl in clouds if not cl.is_off_screen()]

        if game_state == "play":
            dino.update(dt)
            ground_offset = (ground_offset + speed) % 40

            # spawn obstacles
            spawn_timer += dt
            if spawn_timer > random.randint(900, 1400):
                obstacles.append(Cactus(speed))
                spawn_timer = 0

            # update obstacles
            for c in obstacles:
                c.update()
            obstacles = [c for c in obstacles if not c.is_off_screen()]

            # collision check
            for c in obstacles:
                if dino.rect.colliderect(c.rect):
                    game_state = "game_over"
                    if hit_sound:
                        hit_sound.play()
                    break

            # score & difficulty
            score += dt * 0.01
            if int(score) > high_score:
                high_score = int(score)

            # checkpoint sound every 100 points
            current_checkpoint = int(score) // 100
            if current_checkpoint > last_checkpoint:
                last_checkpoint = current_checkpoint
                if point_sound and score > 0:
                    point_sound.play()

            # day/night based on score
            night_mode = (int(score) // 500) % 2 == 1

        # ----- DRAW -----
        bg_color = SKY_NIGHT if night_mode else SKY_DAY
        screen.fill(bg_color)

        # clouds behind ground
        for cl in clouds:
            cl.draw(screen, night_mode=night_mode)

        draw_ground(screen, ground_offset, night_mode=night_mode)

        # dino & obstacles
        dino.draw(screen, night_mode=night_mode)
        for c in obstacles:
            c.draw(screen)

        # score + high score
        draw_text_left(f"Score: {int(score)}   High: {high_score}", 10, night_mode=night_mode)

        if game_state == "start":
            draw_text_center("T-REX RUNNER", 120, night_mode=night_mode)
            draw_text_center("Press SPACE or UP to start", 160, night_mode=night_mode)
            draw_text_center("Press DOWN to duck", 200, night_mode=night_mode)

        elif game_state == "game_over":
            draw_text_center("GAME OVER", 120, night_mode=night_mode)
            draw_text_center("Press SPACE or UP to restart", 160, night_mode=night_mode)
            draw_text_center("Press DOWN to duck", 200, night_mode=night_mode)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
