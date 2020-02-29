#########
# BOIDS #
#########
# Peter Pegues
# python 3.8.1
# pygame 1.9.6
import os, pygame, random, math
from pygame.locals import *
from pygame.compat import geterror

if not pygame.font:
    print("Warning, fonts disabled")
if not pygame.mixer:
    print("Warning, sound disabled")

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")

##############
# Boid Class #
##############
class Boid(pygame.sprite.Sprite):
    ########
    # Init #
    ########
    def __init__(self, init_loc):
        
        # call the parent class constructor
        pygame.sprite.Sprite.__init__(self)

        # Create the image and fill
        # Boid size and color
        self.image = pygame.Surface([5, 5])
        self.color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        # Group detection radius, higher number makes them more stickey
        self.radius = 25
        # Inital speed, heading, location
        self.speed = 4
        self.heading = random.randint(0, 359)
        self.loc = init_loc
        self.rect.x = self.loc[0]
        self.rect.y = self.loc[1]
    
    #############################
    # Coordinate transformation #
    #############################
    def cord_trans(self, loc):
        dx = loc[0] - self.loc[0]
        dy = loc[1] - self.loc[1] 
        # transform dx dy to new axis
        tx = int(dx*math.cos(math.radians(self.heading)) + dy*math.sin(math.radians(self.heading)))
        ty = int(dy*math.cos(math.radians(self.heading)) - dx*math.sin(math.radians(self.heading)))
        # quads
        if tx > 0 and ty > 0:
            boid_dir = 1
        elif tx < 0 and ty > 0:
            boid_dir = 2
        elif tx < 0 and ty < 0:
            boid_dir = 3
        elif tx > 0 and ty < 0:
            boid_dir = 4
        else:
            boid_dir = 0
                
        return boid_dir
    
    ##################
    # Boid Avoidance #
    ##################
    def avoid_the_boid(self, boids_group):
        # find closeest boid on the front and sides
        # seens to work but quads are mirrored? carry on.
        detection_distance = 15
        boid_dir = 0
        for boid in boids_group:
            # don't look at yourself
            if boid.loc != self.loc:
                boid_dis = math.hypot(boid.loc[0]-self.loc[0], boid.loc[1]-self.loc[1])
                if boid_dis < detection_distance:
                    boid_dir = self.cord_trans(boid.loc)
                    
                
        return boid_dir
    
    ##################
    # Center of Mass #
    ##################
    # Find Center of mass for local group
    def center_mass(self, boids_group):
        detection_distance = 30
        close_boids = []
        c_mass = [0,0]

        for boid in boids_group:
            boid_dis = math.hypot(boid.loc[0]-self.loc[0], boid.loc[1]-self.loc[1])
            if boid_dis < detection_distance:
                close_boids.append(boid)
        if len(close_boids) > 1:
            for boid in close_boids:
                c_mass[0] += boid.loc[0]
                c_mass[1] += boid.loc[1]
            c_mass[0] = int(c_mass[0]/len(close_boids))
            c_mass[1] = int(c_mass[1]/len(close_boids))
            return c_mass
        else:
            return None
    
    ###################    
    # Update The Boid #
    ###################
    def update(self, boids_group):
        # Get Close by boids
        # I used pygames built in collision detect here, the circle size is based off self.radius
        local_group = pygame.sprite.spritecollide(self, boids_group, False, pygame.sprite.collide_circle)
        
        # Alignment
        # Heading Avg
        if len(local_group) > 1:
            heading_avg = 0
            for bh in local_group:
                heading_avg += bh.heading
            heading_avg = int(heading_avg/len(local_group))
            self.heading = heading_avg
        
        # Cohesion
        # Turn to Center of Mass
        c_mass_offset = 15
        c_mass_loc = self.center_mass(boids_group.sprites())
        if c_mass_loc is not None:
            c_mass_dir = self.cord_trans(c_mass_loc)
            if c_mass_dir == 1:
                self.heading -= c_mass_offset
            elif c_mass_dir == 2:
                self.heading += c_mass_offset
            elif c_mass_dir == 3:
                self.heading -= c_mass_offset
            elif c_mass_dir == 4:
                self.heading += c_mass_offset
        
        # Seperation
        close_boid_dir = self.avoid_the_boid(boids_group.sprites())
        sep_offset = 15
        if close_boid_dir == 1:
            self.heading += sep_offset
        elif close_boid_dir == 2:
            self.heading -= sep_offset

        # Heading corrections, keeps headings from coumpunding into gigantic numbers
        while self.heading > 360 or self.heading < 0:
            if self.heading < 0:
                self.heading = 360 + self.heading
            if self.heading > 360:
                self.heading = 360 - self.heading
        

        '''# turning speed
        turning_speed = 15
        if self.target_heading < self.heading:
            self.heading -= turning_speed
        elif self.target_heading > self.heading:
            self.heading += turning_speed'''
        
        

        # Calc movement vectors #
        vect_x = int(math.sin(math.radians(self.heading))*self.speed)
        vect_y = int(math.cos(math.radians(self.heading))*self.speed)
        # Set New Pos
        self.loc[0] -= vect_x
        self.loc[1] += vect_y
        
        ## Wrap screen
        if self.loc[0] >= 600:
            self.loc[0] = 600 - self.loc[0]
        elif self.loc[0] <= 0:
            self.loc[0] = self.loc[0] + 600
        
        if self.loc[1] >= 600:
            self.loc[1] = 600 - self.loc[1]
        elif self.loc[1] <= 0:
            self.loc[1] = self.loc[1] + 600
        
        # Set the draw location
        self.rect.x = self.loc[0]
        self.rect.y = self.loc[1]

###################
# Draw the screen #
###################

# Create The Backgound
def draw_screen(screen):
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))
    
    # Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()


########
# Main #
########

def main():

     # Initialize Everything
    pygame.init()
    pygame.display.set_caption("PyBoids")
    pygame.mouse.set_visible(1)

    screen = pygame.display.set_mode((600, 600))
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))
    

    # Create the boids
    boids_group = pygame.sprite.Group()
    for n in range(30):
        loc = [random.randint(0,599), random.randint(0,599)]
        boids_group.add(Boid(init_loc=loc))
    
    
    clock = pygame.time.Clock()
    going = True
    while going == True:
        clock.tick(30)
        # Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                going = False
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                # Click to make a boid
                loc = list(pygame.mouse.get_pos())
                boids_group.add(Boid(init_loc=loc))
        
        
        # Draw Screen
        boids_group.update(boids_group)
        screen.blit(background, (0, 0))
        boids_group.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()