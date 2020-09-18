#!/usr/bin/env
#########
# BOIDS #
#########
# Peter Pegues
# python 3.8.1
# pygame 1.9.6

import os, pygame, random, math, copy
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
        # Inital speed, heading, location
        self.speed = 4
        self.target_heading = random.randint(0, 359)
        self.current_heading = copy.copy(self.target_heading)
        self.avoid_distance = 10
        self.heading_avg_distance = 10
        self.cmass_distance = 100
        self.loc = init_loc
        self.loc_next = copy.copy(self.loc)
        self.rect.x = self.loc[0]
        self.rect.y = self.loc[1]
    
    #############################
    # Coordinate transformation #
    #############################
    def cord_trans(self, loc):
        dx = loc[0] - self.loc[0]
        dy = loc[1] - self.loc[1] 
        # transform dx dy to new axis
        tx = int(dx*math.cos(math.radians(self.current_heading)) + dy*math.sin(math.radians(self.current_heading)))
        ty = int(dy*math.cos(math.radians(self.current_heading)) - dx*math.sin(math.radians(self.current_heading)))
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
    #################
    # Boid Distance #
    #################
    def distance_to_boid(self,boid):
        return math.hypot(boid.loc[0]-self.loc[0], boid.loc[1]-self.loc[1])

    ##################
    # Boid Avoidance #
    ##################
    def avoid_the_boid(self, boids_group):
        # find closeest boid on the front and sides
        min_boid = copy.copy(self.avoid_distance)
        boid_dir = 0
        target_boid_loc = None
        for boid in boids_group:
            # don't look at yourself
            if boid.loc != self.loc:
                boid_dis = self.distance_to_boid(boid)
                if boid_dis < min_boid:
                    min_boid = boid_dis
                    target_boid_loc = boid.loc
        if target_boid_loc is not None:
            boid_dir = self.cord_trans(boid.loc) # pulled out of loop to only do once per cycle
        if min_boid < 2:
            # emergency turn
            return 5
        else:
            return boid_dir # return value of 0 means no boids in dection dis
    
    ##################
    # Center of Mass #
    ##################
    # Find Center of mass for local group
    def center_mass(self, close_boids):
        c_mass = [0,0]

        if len(close_boids) > 1:
            for boid in close_boids:
                c_mass[0] += boid.loc[0]
                c_mass[1] += boid.loc[1]
            
            c_mass[0] = int(c_mass[0]/len(close_boids))
            c_mass[1] = int(c_mass[1]/len(close_boids))
            
            return c_mass
        else:
            return None
    
    ##########################
    # Align To Group Heading #
    ##########################
    def group_avg_heading(self, local_group):
        heading_avg = 0
        # If detection distance is too high they seem to convirge on 180ish and I suspect because its the avg of numbers 0-360. The center of mass calc than somehow rotates this avg by 90 deg making them prefer 270. Weird but ok.
        if len(local_group) > 1:
            for boid in local_group:
                heading_avg += boid.current_heading
            heading_avg = int(heading_avg/len(local_group))
        else:
            heading_avg = self.current_heading

        return heading_avg

    ####################
    # Rescale Headings #
    ####################
    def rescale_heading(self,heading):
        while heading > 360 or heading < 0:
            if heading < 0:
                heading = heading + 360
            if heading > 360:
                heading = heading - 360
        return heading
    
    #####################
    # Create the Groups #
    #####################
    def create_local_groups(self,boids_group):
        avoid_group = []
        heading_avg_group = []
        cmass_group = []
        for boid in boids_group:
            dtb = self.distance_to_boid(boid)
            if dtb <= self.avoid_distance:
                avoid_group.append(boid)
            if dtb <= self.heading_avg_distance:
                heading_avg_group.append(boid)
            if dtb <= self.cmass_distance:
                cmass_group.append(boid)
        return [heading_avg_group,cmass_group,avoid_group]

    ###################    
    # Update The Boid #
    ###################
    def update(self, boids_group):
        # Create Local Groups
        # 0 - heading_avg_group, 1 - cmass_group, 2-avoid_group
        local_groups = self.create_local_groups(boids_group.sprites())
        
        # Align To Group
        self.target_heading = self.group_avg_heading(local_groups[0])

        # Cohesion
        # Turn to Center of Mass
        # This is workign better than the last version but still needs improvment
        c_mass_loc = self.center_mass(local_groups[1]) 
        
        if c_mass_loc is not None:
            deg_Turn = 10
            dx = c_mass_loc[0] - self.loc[0]
            dy = c_mass_loc[1] - self.loc[1]
            if dx == 0: # dont divide by zero
                dx = 0.0000000000001
            if dy == 0:
                dy = 0.0000000000001
            angleR = math.atan(dy/dx)
            angleD = int(math.degrees(angleR))

            # Correct the heading when target is to the left
            if dx < 0:
                angleD = angleD + 180

            angleD = self.rescale_heading(angleD)

            # decide if clockwise or counter clockwise is shorter
            if angleD < self.target_heading:
                if self.target_heading - angleD > 180:
                    self.target_heading += deg_Turn
                else:
                    self.target_heading -= deg_Turn

            elif angleD > self.target_heading:
                if angleD - self.target_heading > 180:
                    self.target_heading -= deg_Turn
                else:
                    self.target_heading += deg_Turn
        
        # Seperation
        # The left front should be quad 1 and the rigth front should be quad 4 after the transformation
        close_boid_dir = self.avoid_the_boid(local_groups[2])
        sep_deg_turn = 15
        if close_boid_dir == 1:
            self.target_heading -= sep_deg_turn
        elif close_boid_dir == 4:
            self.target_heading += sep_deg_turn
        elif close_boid_dir == 5:
            # Emergency Turn
            self.target_heading += sep_deg_turn * 3
        
        # Heading corrections, keeps headings from coumpunding into gigantic numbers
        self.target_heading = self.rescale_heading(self.target_heading)

        # Turning 
        turning_speed = 5
        # Turning attempt 2
        if self.target_heading > self.current_heading:
            if self.target_heading - self.current_heading > 180:
                self.current_heading -= turning_speed
            else:
                self.current_heading += turning_speed
        
        elif self.target_heading < self.current_heading:
            if self.current_heading - self.target_heading > 180:
                self.current_heading += turning_speed
            else:
                self.current_heading -= turning_speed
        
        # Heading corrections, keeps headings from coumpunding into gigantic numbers
        self.current_heading = self.rescale_heading(self.current_heading)
        # setting target heading to the final current heading for the next round.
        self.target_heading = copy.copy(self.current_heading)

        # Calc movement vectors #
        vect_x = int(math.cos(math.radians(self.current_heading))*self.speed)
        vect_y = int(math.sin(math.radians(self.current_heading))*self.speed)
        # Set New Pos
        self.loc_next[0] += vect_x
        self.loc_next[1] += vect_y
        
        ## Wrap screen
        if self.loc_next[0] >= 600:
            self.loc_next[0] = 600 - self.loc[0]
        elif self.loc_next[0] <= 0:
            self.loc_next[0] = self.loc[0] + 600
        
        if self.loc_next[1] >= 600:
            self.loc_next[1] = 600 - self.loc[1]
        elif self.loc_next[1] <= 0:
            self.loc_next[1] = self.loc[1] + 600
    
    def update_loc(self):
        # Set the draw location
        self.rect.x = self.loc_next[0]
        self.rect.y = self.loc_next[1]
        self.loc = copy.copy(self.loc_next)

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
    for n in range(100):
        loc = [random.randint(0,599), random.randint(0,599)]
        boids_group.add(Boid(init_loc=loc))
    
    clock = pygame.time.Clock()
    going = True
    while going == True:
        clock.tick(60)
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
        for boid in boids_group:
            boid.update_loc()
        screen.blit(background, (0, 0))
        boids_group.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
