import numpy as np
import cv2
import math
from collections import deque

class PathCalculator:
    """
    Handles path calculation and navigation guidance based on detected objects
    and obstacles from camera and other sensors.
    """
    
    def __init__(self, safe_distance=1.0, grid_size=100):
        """
        Initialize the path calculator
        
        Args:
            safe_distance: Safe distance to maintain from obstacles (in meters)
            grid_size: Size of the grid for path planning
        """
        self.safe_distance = safe_distance
        self.grid_size = grid_size
        self.obstacle_grid = np.zeros((grid_size, grid_size), dtype=np.uint8)
        self.current_position = (grid_size // 2, grid_size - 5)  # Start at bottom center
        self.goal_position = None
        
    def update_obstacle_map(self, detected_objects, depth_data=None):
        """
        Update the obstacle map based on detected objects and depth information
        
        Args:
            detected_objects: List of detected objects with position and class
            depth_data: Optional depth map from sensors (if available)
        """
        # Reset grid
        self.obstacle_grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)
        
        # Add detected objects to grid
        for obj in detected_objects:
            # Extract object information
            obj_class = obj['class']
            obj_x = obj['x'] 
            obj_y = obj['y']
            obj_width = obj['width']
            obj_height = obj['height']
            
            # Determine if object is an obstacle
            is_obstacle = obj_class in ['person', 'bicycle', 'car', 'motorcycle', 'bus', 
                                       'truck', 'chair', 'sofa', 'bench', 'potted plant']
            
            # Determine if object is a pathway
            is_path = obj_class in ['floor', 'road', 'sidewalk', 'path']
            
            # Convert to grid coordinates 
            grid_x = int(obj_x * self.grid_size)
            grid_y = int(obj_y * self.grid_size)
            grid_width = max(1, int(obj_width * self.grid_size))
            grid_height = max(1, int(obj_height * self.grid_size))
            
            # Mark on grid (1 for obstacles, 0 for free space, 2 for paths)
            if is_obstacle:
                # Add padding around obstacles for safe distance
                cv2.rectangle(self.obstacle_grid, 
                             (max(0, grid_x - grid_width//2 - 2), 
                              max(0, grid_y - grid_height//2 - 2)),
                             (min(self.grid_size-1, grid_x + grid_width//2 + 2), 
                              min(self.grid_size-1, grid_y + grid_height//2 + 2)),
                             1, -1)
            elif is_path:
                cv2.rectangle(self.obstacle_grid, 
                             (max(0, grid_x - grid_width//2), 
                              max(0, grid_y - grid_height//2)),
                             (min(self.grid_size-1, grid_x + grid_width//2), 
                              min(self.grid_size-1, grid_y + grid_height//2)),
                             2, -1)
        
        # If depth data is available, use it to further refine the obstacle map
        if depth_data is not None:
            # Normalize depth data to grid size
            depth_resized = cv2.resize(depth_data, (self.grid_size, self.grid_size))
            
            # Mark close objects as obstacles
            close_obstacles = depth_resized < self.safe_distance
            self.obstacle_grid[close_obstacles] = 1
    
    def set_goal(self, goal_type, params=None):
        """
        Set navigation goal
        
        Args:
            goal_type: Type of goal ('exit', 'object', 'direction', 'coordinates')
            params: Additional parameters for the goal
        """
        if goal_type == 'exit':
            # Find exits in the obstacle grid (simplified - in a real system
            # this would use object detection to identify doors/exits)
            self.goal_position = (self.grid_size // 2, 0)  # Assume exit is at the top
            
        elif goal_type == 'object' and params:
            # Set goal to navigate to a specific object
            object_class = params.get('class')
            # Find the object in detected objects
            # This is simplified - real implementation would track objects
            self.goal_position = (params.get('x', 0), params.get('y', 0))
            
        elif goal_type == 'direction' and params:
            # Set goal based on a direction (e.g., "go forward 5 meters")
            direction = params.get('direction', 'forward')
            distance = params.get('distance', 3)
            
            # Convert direction and distance to a goal position
            x, y = self.current_position
            if direction == 'forward':
                y = max(0, y - int(distance * 10))
            elif direction == 'backward':
                y = min(self.grid_size - 1, y + int(distance * 10))
            elif direction == 'left':
                x = max(0, x - int(distance * 10))
            elif direction == 'right':
                x = min(self.grid_size - 1, x + int(distance * 10))
                
            self.goal_position = (x, y)
            
        elif goal_type == 'coordinates' and params:
            # Set goal to specific coordinates
            self.goal_position = (params.get('x', 0), params.get('y', 0))
    
    def find_path(self):
        """
        Find path from current position to goal using Breadth-First Search
        
        Returns:
            path: List of coordinates representing the path
            directions: List of navigation directions
        """
        if not self.goal_position:
            return [], ["No goal set. Please specify a destination."]
        
        # Initialize BFS
        queue = deque([self.current_position])
        visited = {self.current_position: None}  # Maps cell -> parent cell
        
        # BFS to find path
        while queue and self.goal_position not in visited:
            current = queue.popleft()
            x, y = current
            
            # Try all four directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:  # Up, Right, Down, Left
                nx, ny = x + dx, y + dy
                
                # Check bounds and if not an obstacle and not visited
                if (0 <= nx < self.grid_size and 0 <= ny < self.grid_size and 
                    self.obstacle_grid[ny, nx] != 1 and (nx, ny) not in visited):
                    queue.append((nx, ny))
                    visited[(nx, ny)] = current
        
        # Reconstruct path
        path = []
        if self.goal_position in visited:
            current = self.goal_position
            while current != self.current_position:
                path.append(current)
                current = visited[current]
            path.append(self.current_position)
            path.reverse()
        
        # Generate directions from path
        directions = self._generate_directions(path)
        
        return path, directions
    
    def _generate_directions(self, path):
        """
        Generate human-readable directions from path
        
        Args:
            path: List of coordinates representing the path
            
        Returns:
            directions: List of navigation directions
        """
        if not path or len(path) < 2:
            return ["Unable to find a safe path. Please wait for assistance."]
        
        directions = []
        prev_direction = None
        steps_in_direction = 0
        
        for i in range(1, len(path)):
            x1, y1 = path[i-1]
            x2, y2 = path[i]
            
            # Determine direction
            if x2 > x1:
                current_direction = "right"
            elif x2 < x1:
                current_direction = "left"
            elif y2 < y1:
                current_direction = "forward"
            else:
                current_direction = "backward"
            
            # Check if direction changed
            if current_direction != prev_direction:
                if prev_direction:
                    directions.append(f"Move {prev_direction} {steps_in_direction} steps.")
                prev_direction = current_direction
                steps_in_direction = 1
            else:
                steps_in_direction += 1
        
        # Add the last direction
        if prev_direction:
            directions.append(f"Move {prev_direction} {steps_in_direction} steps.")
        
        # Check for obstacles near the path and add warnings
        for i, (x, y) in enumerate(path):
            # Simplified obstacle detection - check surrounding cells
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_size and 0 <= ny < self.grid_size and 
                    self.obstacle_grid[ny, nx] == 1):
                    # Determine the direction of the obstacle
                    if dx == 1:
                        obstacle_dir = "right"
                    elif dx == -1:
                        obstacle_dir = "left"
                    elif dy == 1:
                        obstacle_dir = "behind"
                    else:
                        obstacle_dir = "ahead"
                    
                    # Add warning if not already warned about this obstacle
                    warning = f"Caution: Obstacle to your {obstacle_dir}."
                    if warning not in directions:
                        directions.insert(min(i, len(directions)), warning)
        
        # Add completion message
        if self.goal_position == path[-1]:
            directions.append("You have reached your destination.")
        
        return directions
        
    def visualize_path(self, path=None):
        """
        Generate a visualization of the obstacle map and path
        
        Args:
            path: Optional path to visualize
            
        Returns:
            visualization: Numpy array with the visualization
        """
        # Create RGB visualization
        vis = np.zeros((self.grid_size, self.grid_size, 3), dtype=np.uint8)
        
        # Mark obstacles in red
        vis[self.obstacle_grid == 1] = [0, 0, 255]
        
        # Mark paths in green
        vis[self.obstacle_grid == 2] = [0, 255, 0]
        
        # Mark current position in blue
        cx, cy = self.current_position
        cv2.circle(vis, (cx, cy), 2, (255, 0, 0), -1)
        
        # Mark goal position in yellow if set
        if self.goal_position:
            gx, gy = self.goal_position
            cv2.circle(vis, (gx, gy), 2, (0, 255, 255), -1)
        
        # Draw path in white if provided
        if path:
            for i in range(1, len(path)):
                x1, y1 = path[i-1]
                x2, y2 = path[i]
                cv2.line(vis, (x1, y1), (x2, y2), (255, 255, 255), 1)
        
        return vis 