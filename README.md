# PyGame Boids
### An Implementation of Boids in PyGame. 

This was a quick single day project where I wanted to try and write boids just based on my interpretation of the rules. I challenged myself not to look at any other implementations of boids during the process. It is by no means perfect or optimized but it seems to work well enough.

### Rules
1. **Separation:** steer to avoid crowding local flockmates
2. **Alignment:** steer towards the average heading of local flockmates
3. **Cohesion:** steer to move towards the average position (center of mass) of local flockmates

![Boids](./boids.gif)