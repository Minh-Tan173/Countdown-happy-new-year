import pygame
from random import randint, uniform, choice
import math
from datetime import datetime

vector2 = pygame.math.Vector2
trails = []
fade_p = []

# general
GRAVITY_FIREWORK = vector2(0, 0.3)
GRAVITY_PARTICLE = vector2(0, 0.07)
DISPLAY_WIDTH = DISPLAY_HEIGHT = 720
BACKGROUND_COLOR = (20, 20, 30) 
# firework
FIREWORK_SPEED_MIN = 17
FIREWORK_SPEED_MAX = 20
FIREWORK_SIZE = 5
# particle
PARTICLE_LIFESPAN = 70
X_SPREAD = 0.8
Y_SPREAD = 0.8
PARTICLE_SIZE = 4
MIN_PARTICLES = 100
MAX_PARTICLES = 200
X_WIGGLE_SCALE = 20  # higher -> less wiggle
Y_WIGGLE_SCALE = 10
EXPLOSION_RADIUS_MIN = 10
EXPLOSION_RADIUS_MAX = 25
COLORFUL = True
# trail
TRAIL_LIFESPAN = PARTICLE_LIFESPAN / 2
TRAIL_FREQUENCY = 10  # higher -> less trails
TRAILS = True


class Firework:
    def __init__(self):
        self.colour = tuple(randint(0, 255) for _ in range(3))
        self.colours = tuple(tuple(randint(0, 255) for _ in range(3)) for _ in range(3))
        # Creates the firework particle
        self.firework = Particle(randint(0, DISPLAY_WIDTH), DISPLAY_HEIGHT, True, self.colour)
        self.exploded = False
        self.particles = []

    def update(self, win: pygame.Surface) -> None:
        # method called every frame
        if not self.exploded:
            self.firework.apply_force(GRAVITY_FIREWORK)
            self.firework.move()
            self.show(win)
            if self.firework.vel.y >= 0:
                self.exploded = True
                self.explode()

        else:
            for particle in self.particles:
                particle.update()
                particle.show(win)

    def explode(self):
        # when the firework has entered a stand still, create the explosion particles
        amount = randint(MIN_PARTICLES, MAX_PARTICLES)
        if COLORFUL:
            self.particles = [Particle(self.firework.pos.x, self.firework.pos.y, False, choice(self.colours)) for _ in range(amount)]
        else:
            self.particles = [Particle(self.firework.pos.x, self.firework.pos.y, False, self.colour) for _ in range(amount)]

    def show(self, win: pygame.Surface) -> None:
        # draw the firework on the given surface
        x = int(self.firework.pos.x)
        y = int(self.firework.pos.y)
        pygame.draw.circle(win, self.colour, (x, y), self.firework.size)

    def remove(self) -> bool:
        if not self.exploded:
            return False

        for p in self.particles:
            if p.remove:
                self.particles.remove(p)

        # remove the firework object if all particles are gone
        return len(self.particles) == 0


class Particle(object):
    def __init__(self, x, y, firework, colour):
        self.firework = firework
        self.pos = vector2(x, y)
        self.origin = vector2(x, y)
        self.acc = vector2(0, 0)
        self.remove = False
        self.explosion_radius = randint(EXPLOSION_RADIUS_MIN, EXPLOSION_RADIUS_MAX)
        self.life = 0
        self.colour = colour
        self.trail_frequency = TRAIL_FREQUENCY + randint(-3, 3)

        if self.firework:
            self.vel = vector2(0, -randint(FIREWORK_SPEED_MIN, FIREWORK_SPEED_MAX))
            self.size = FIREWORK_SIZE
        else:
            # set random position of particle 
            self.vel = vector2(uniform(-1, 1), uniform(-1, 1))
            self.vel.x *= randint(7, self.explosion_radius + 2)
            self.vel.y *= randint(7, self.explosion_radius + 2)
            self.size = randint(PARTICLE_SIZE - 1, PARTICLE_SIZE + 1)
            # update pos and remove particle if outside radius
            self.move()
            self.outside_spawn_radius()

    def update(self) -> None:
        # called every frame
        self.life += 1
        # add a new trail if life % x == 0
        if self.life % self.trail_frequency == 0:
            trails.append(Trail(self.pos.x, self.pos.y, False, self.colour, self.size))
        # wiggle
        self.apply_force(vector2(uniform(-1, 1) / X_WIGGLE_SCALE, GRAVITY_PARTICLE.y + uniform(-1, 1) / Y_WIGGLE_SCALE))
        self.move()

    def apply_force(self, force: pygame.math.Vector2) -> None:
        self.acc += force

    def outside_spawn_radius(self) -> bool:
        # if the particle spawned is outside of the radius that creates the circular firework, remov it
        distance = math.sqrt((self.pos.x - self.origin.x) ** 2 + (self.pos.y - self.origin.y) ** 2)
        return distance > self.explosion_radius

    def move(self) -> None:
        # called every frame, moves the particle
        if not self.firework:
            self.vel.x *= X_SPREAD
            self.vel.y *= Y_SPREAD

        self.vel += self.acc
        self.pos += self.vel
        self.acc *= 0

        self.decay()

    def show(self, win: pygame.Surface) -> None:
        # draw the particle on to the surface
        x = int(self.pos.x)
        y = int(self.pos.y)
        pygame.draw.circle(win, self.colour, (x, y), self.size)

    def decay(self) -> None:
        # random decay of the particles
        if self.life > PARTICLE_LIFESPAN:
            if randint(0, 15) == 0:
                self.remove = True
        # if too old, begone
        if not self.remove and self.life > PARTICLE_LIFESPAN * 1.5:
            self.remove = True


class Trail(Particle):
    def __init__(self, x, y, is_firework, colour, parent_size):
        Particle.__init__(self, x, y, is_firework, colour)
        self.size = parent_size - 1

    def decay(self) -> bool:
        # decay also changes the color on the trails
        # returns true if to be removed, else false
        self.life += 1
        if self.life % 100 == 0:
            self.size -= 1

        self.size = max(0, self.size)
        # static yellow-ish colour self.colour = (255, 255, 220)
        self.colour = (min(self.colour[0] + 5, 255), min(self.colour[1] + 5, 255), min(self.colour[2] + 5, 255))

        if self.life > TRAIL_LIFESPAN:
            ran = randint(0, 15)
            if ran == 0:
                return True
        # if too old, begone
        if not self.remove and self.life > TRAIL_LIFESPAN * 1.5:
            return True
        
        return False


class Clock:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.clock_radius = 200
        self.hand_length_hour = 120
        self.hand_length_minute = 160
        self.hand_length_second = 180
        self.new_year = datetime(datetime.now().year + 1, 1, 1)

    def update_time(self):
        now = datetime.now()
        self.current_time = now.strftime("%H:%M:%S")
        self.current_date = now.strftime("%Y-%m-%d")
        self.hour = now.hour % 12
        self.minute = now.minute
        self.second = now.second
        self.time_to_new_year = self.new_year - now

    def show(self, win, running = True):
        self.update_time()

        # Hiển thị đồng hồ
        pygame.draw.circle(win, (255, 255, 255), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2), self.clock_radius, 2)

        # Hiển thị số giờ
        for i in range(1, 13):
            angle = math.radians(90 - i * 30)  # Bắt đầu từ góc 90 độ, mỗi số giờ cách nhau 30 độ
            number_x = int(DISPLAY_WIDTH // 2 + (self.clock_radius - 20) * math.cos(angle))
            number_y = int(DISPLAY_HEIGHT // 2 - (self.clock_radius - 20) * math.sin(angle))
            number_text = self.font.render(str(i), True, (255, 255, 255))
            number_rect = number_text.get_rect(center=(number_x, number_y))
            win.blit(number_text, number_rect)

        # Hiển thị kim giờ
        hour_angle = math.radians(90 - (self.hour % 12) * 30 - (self.minute / 60) * 30)  # 1 giờ = 30 độ, 1 phút = 0.5 độ
        hour_hand_x = int(DISPLAY_WIDTH // 2 + self.hand_length_hour * math.cos(hour_angle))
        hour_hand_y = int(DISPLAY_HEIGHT // 2 - self.hand_length_hour * math.sin(hour_angle))
        pygame.draw.line(win, (255, 255, 255), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2), (hour_hand_x, hour_hand_y), 4)

        # Hiển thị kim phút
        minute_angle = math.radians(90 - self.minute * 6)  # 1 phút = 6 độ
        minute_hand_x = int(DISPLAY_WIDTH // 2 + self.hand_length_minute * math.cos(minute_angle))
        minute_hand_y = int(DISPLAY_HEIGHT // 2 - self.hand_length_minute * math.sin(minute_angle))
        pygame.draw.line(win, (255, 255, 255), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2), (minute_hand_x, minute_hand_y), 3)

        # Hiển thị kim giây
        second_angle = math.radians(90 - self.second * 6)  # 1 giây = 6 độ
        second_hand_x = int(DISPLAY_WIDTH // 2 + self.hand_length_second * math.cos(second_angle))
        second_hand_y = int(DISPLAY_HEIGHT // 2 - self.hand_length_second * math.sin(second_angle))
        if 0<= int(self.time_to_new_year.total_seconds()) <= 10:
            pygame.draw.line(win, (255, 0, 0), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2), (second_hand_x, second_hand_y), 2)
        else:
            pygame.draw.line(win, (255, 255, 255), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2), (second_hand_x, second_hand_y), 2)

        # Hiển thị ngày tháng năm
        date_text = self.font.render(self.current_date, True, (255, 255, 255))
        date_rect = date_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 240))
        win.blit(date_text, date_rect)

        # Hiển thị số giây còn lại đến năm mới
        if not int(self.time_to_new_year.total_seconds()) <= 0:
            
            if 0 <= int(self.time_to_new_year.total_seconds()) <= 10:
                font_text = pygame.font.Font(None, 40)
                countdown_text = self.font.render("Time to New Year:", True, (255, 255, 255))
                countdown_rect = countdown_text.get_rect(center=(DISPLAY_WIDTH // 2 - 80, DISPLAY_HEIGHT // 2 + 280))
                countdown_text2 = font_text.render(f"{int(self.time_to_new_year.total_seconds())} seconds", True, (255, 0, 0))
                countdown_rect2 = countdown_text.get_rect(center=(DISPLAY_WIDTH // 2  + 135 , DISPLAY_HEIGHT // 2 + 280))

                win.blit(countdown_text, countdown_rect)
                win.blit(countdown_text2, countdown_rect2)
            elif not 0 <= int(self.time_to_new_year.total_seconds()) <= 10:
                font_text = pygame.font.Font(None, 36)
                countdown_text =self.font.render(f"Time to New Year: ", True, (255, 255, 255))
                countdown_rect = countdown_text.get_rect(center=(DISPLAY_WIDTH // 2 - 80, DISPLAY_HEIGHT // 2 + 280))
                countdown_text2 = font_text.render(f"{int(self.time_to_new_year.total_seconds())} seconds", True, (255, 255, 255))
                countdown_rect2 = countdown_text.get_rect(center=(DISPLAY_WIDTH // 2  + 135 , DISPLAY_HEIGHT // 2 + 280))
                
                win.blit(countdown_text, countdown_rect)
                win.blit(countdown_text2, countdown_rect2)

                
        else:
            countdown_text = self.font.render(f"Time to New Year: 0 seconds", True, (255, 255, 255))
            countdown_rect = countdown_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 280))
            win.blit(countdown_text, countdown_rect)

        return self.time_to_new_year.seconds
        
    def reset(self):
        self.new_year = datetime(datetime.now().year + 1, 1, 1)
        
        
def update(win, fireworks, trails, clock):
    if TRAILS:
        for t in trails:
            t.show(win)
            if t.decay():
                trails.remove(t)

    for fw in fireworks:
        fw.update(win)
        if fw.remove():
            fireworks.remove(fw)

    clock.show(win)  # Hiển thị đồng hồ
    pygame.display.update()


pygame.init()
pygame.display.set_caption("Countdown NewYear")
win = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))

def main(state1 = 1):
    
    clock = pygame.time.Clock()
    running = True
    game_clock = Clock()
    
    if state1 == 1:
        
        while running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
            win.fill(BACKGROUND_COLOR)
            game_clock.show(win)
            check = game_clock.show(win)
            pygame.display.update()
            if check == 0:
                main(state1 = 2)
            pygame.display.update()       
    
    elif state1 == 2:
        
        fireworks = [Firework() for i in range(1)]  # create the first fireworks
        running = True
        game_clock.reset()
        
        # Bắt đầu phát âm nhạc nền khi state1 == 2
        pygame.mixer.music.load(r"C:\Users\admin\OneDrive\Máy tính\Countdown NewYear\Happy New Year Remix - Hưng Hack - Nhạc Remix Quẩy Tết Năm Mới Cực Hot Tik Tok 2022.mp3")
        pygame.mixer.music.set_volume(0.4)  # Điều chỉnh âm lượng theo nhu cầu (từ 0.0 đến 1.0)
        pygame.mixer.music.play(1, start= 38)  # Bắt đầu phát âm nhạc nền trong một vòng lặp vô hạn (-1)
        
        font = pygame.font.Font(None, 50)
        happy_new_year_text = font.render("Happy New Year!", True, (255, 255, 255))
        
        color_change_interval = 6  # Đổi màu sau mỗi 30 frame
        current_frame = 0
        
        while running:
            clock.tick(60)
            current_frame += 1
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        fireworks.append(Firework())
                    elif event.key == pygame.K_2:
                        for i in range(10):
                            fireworks.append(Firework())
            win.fill(BACKGROUND_COLOR)  # draw background

            if randint(0, 70) == 1:  # create new firework
                fireworks.append(Firework())
            
            update(win, fireworks, trails, game_clock)

            # Hiển thị văn bản "Chúc Mừng Năm Mới" ở giữa màn hình
            if current_frame % color_change_interval == 0:
                text_rect = happy_new_year_text.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
                color = (randint(0, 255), randint(0, 255), randint(0, 255))  # Màu ngẫu nhiên
                happy_new_year_text = font.render("Happy New Year!", True, color)
                win.blit(happy_new_year_text, text_rect)

            pygame.display.update()

    pygame.quit()
    quit()

main()