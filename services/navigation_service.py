import os
import threading
import time
import json
from models.path_calculation import PathCalculator
from models.adaptive_learning import adaptive_learning_model
from services.voice_service import voice_command_service

class NavigationService:
    """
    Service to handle navigation requests and provide guidance to users.
    Connects object detection with path calculation to generate navigation instructions.
    """
    
    def __init__(self):
        """Initialize the navigation service"""
        self.path_calculator = PathCalculator()
        self.detected_objects = []
        self.current_path = []
        self.current_directions = []
        self.is_active = False
        self.navigation_thread = None
        self.lock = threading.Lock()
        self.voice_enabled = True
        self.session_start_time = None
        self.last_user_position = None
        self.obstacles_avoided = []
        self.last_feedback = None
        
    def start_navigation(self, goal_type, params=None, user_id=None):
        """
        Start navigation guidance to a specific goal
        
        Args:
            goal_type: Type of goal ('exit', 'object', 'direction', 'coordinates')
            params: Additional parameters for the goal
            user_id: Optional user ID for personalized learning
            
        Returns:
            success: True if navigation started successfully
            message: Status message
        """
        with self.lock:
            if self.is_active:
                return False, "Navigation already in progress. Please stop current navigation first."
            
            # Initialize adaptive learning for this session if user_id provided
            if user_id:
                adaptive_learning_model.user_id = user_id
                
                # Apply learned parameters to path calculator
                learned_params = adaptive_learning_model.get_adjusted_parameters()
                self.path_calculator.safe_distance = learned_params.get(
                    "max_warning_distance", self.path_calculator.safe_distance)
            
            # Reset session data
            self.session_start_time = time.time()
            self.obstacles_avoided = []
            self.last_user_position = self.path_calculator.current_position
            
            # Set the goal in the path calculator
            self.path_calculator.set_goal(goal_type, params)
            
            # Calculate initial path
            self.current_path, self.current_directions = self.path_calculator.find_path()
            
            if not self.current_path:
                return False, "Could not find a path to the destination. Please try again."
            
            # Start navigation thread
            self.is_active = True
            self.navigation_thread = threading.Thread(target=self._navigation_loop)
            self.navigation_thread.daemon = True
            self.navigation_thread.start()
            
            initial_direction = self.current_directions[0] if self.current_directions else "Starting navigation..."
            return True, f"Navigation started. {initial_direction}"
    
    def stop_navigation(self):
        """
        Stop current navigation guidance
        
        Returns:
            success: True if navigation stopped successfully
            message: Status message
        """
        with self.lock:
            if not self.is_active:
                return False, "No active navigation to stop."
            
            # Capture data for learning before stopping
            session_duration = time.time() - self.session_start_time if self.session_start_time else 0
            successful = True  # Assume successful if manually stopped
            
            # Set is_active to False before joining thread
            self.is_active = False
            
            # Wait for thread to terminate
            if self.navigation_thread:
                self.navigation_thread.join(timeout=1.0)
            
            # Record navigation session in adaptive learning model
            if adaptive_learning_model.user_id and self.session_start_time:
                adaptive_learning_model.record_navigation_session(
                    start_point=self.last_user_position,
                    end_point=self.path_calculator.current_position,
                    path_taken=self.current_path,
                    obstacles_avoided=self.obstacles_avoided,
                    duration=session_duration,
                    successful=successful
                )
            
            self.current_path = []
            self.current_directions = []
            return True, "Navigation stopped."
    
    def update_detected_objects(self, objects):
        """
        Update the list of detected objects
        
        Args:
            objects: List of detected objects with position and class
        """
        with self.lock:
            # Track new obstacles for learning
            for obj in objects:
                if obj.get('class') in ['person', 'bicycle', 'car', 'chair', 'sofa', 'bench', 'potted plant']:
                    if obj not in self.detected_objects:
                        self.obstacles_avoided.append(obj)
            
            # Update the detected objects list
            self.detected_objects = objects
            
            # If navigation is active, update the path
            if self.is_active:
                # Apply any adaptive learning parameters
                if adaptive_learning_model.user_id:
                    params = adaptive_learning_model.get_adjusted_parameters()
                    confidence_threshold = params.get("obstacle_confidence_threshold", 0.6)
                    
                    # Only keep objects with confidence above threshold
                    filtered_objects = [obj for obj in objects 
                                       if obj.get('confidence', 0) >= confidence_threshold]
                else:
                    filtered_objects = objects
                
                # Update path calculation with filtered objects
                self.path_calculator.update_obstacle_map(filtered_objects)
                self.current_path, self.current_directions = self.path_calculator.find_path()
    
    def get_current_guidance(self):
        """
        Get the current navigation guidance
        
        Returns:
            guidance: Dictionary with current guidance information
        """
        with self.lock:
            # Get adaptive learning progress if available
            learning_progress = None
            if adaptive_learning_model.user_id:
                learning_progress = adaptive_learning_model.get_learning_progress()
            
            # Get voice command help if needed
            voice_commands = voice_command_service.get_available_commands()
            
            return {
                'is_active': self.is_active,
                'directions': self.current_directions,
                'current_step': 0 if not self.current_directions else 1,
                'total_steps': len(self.current_directions),
                'visualization': self.path_calculator.visualize_path(self.current_path).tolist() if self.current_path else None,
                'learning_progress': learning_progress,
                'voice_commands': voice_commands,
                'voice_enabled': self.voice_enabled
            }
    
    def toggle_voice(self, enabled=None):
        """
        Toggle voice guidance on/off
        
        Args:
            enabled: Set to True or False to enable/disable, or None to toggle
            
        Returns:
            voice_enabled: Current voice enabled status
        """
        with self.lock:
            if enabled is not None:
                self.voice_enabled = enabled
            else:
                self.voice_enabled = not self.voice_enabled
            return self.voice_enabled
    
    def process_voice_command(self, voice_input, user_id=None):
        """
        Process voice command and take appropriate action
        
        Args:
            voice_input: String containing transcribed voice input
            user_id: Optional user ID for personalized learning
            
        Returns:
            result: Dictionary with command processing result
        """
        # Set user ID for adaptive learning if provided
        if user_id:
            adaptive_learning_model.user_id = user_id
        
        # Process command with voice service
        command_result = voice_command_service.process_command(voice_input)
        
        # If command successful, take action
        if command_result["success"]:
            command_type = command_result["command_type"]
            action = command_result["action"]
            
            if command_type == "navigation":
                if action == "find_exit":
                    # Start navigation to exit
                    success, message = self.start_navigation("exit", user_id=user_id)
                    command_result["action_result"] = {"success": success, "message": message}
                
                elif action == "go_forward":
                    # Start navigation forward
                    params = {"direction": "forward", "distance": 5}
                    success, message = self.start_navigation("direction", params, user_id=user_id)
                    command_result["action_result"] = {"success": success, "message": message}
                
                elif action == "go_left":
                    # Start navigation left
                    params = {"direction": "left", "distance": 3}
                    success, message = self.start_navigation("direction", params, user_id=user_id)
                    command_result["action_result"] = {"success": success, "message": message}
                
                elif action == "go_right":
                    # Start navigation right
                    params = {"direction": "right", "distance": 3}
                    success, message = self.start_navigation("direction", params, user_id=user_id)
                    command_result["action_result"] = {"success": success, "message": message}
                
                elif action == "stop":
                    # Stop navigation
                    success, message = self.stop_navigation()
                    command_result["action_result"] = {"success": success, "message": message}
            
            elif command_type == "information":
                if action == "what_is_around":
                    # Generate description of surroundings
                    objects_description = self._generate_environment_description()
                    command_result["action_result"] = {
                        "success": True, 
                        "message": objects_description
                    }
                
                elif action == "identify_object":
                    # Identify central object in view
                    central_object = self._identify_central_object()
                    command_result["action_result"] = {
                        "success": True,
                        "message": central_object
                    }
            
            elif command_type == "system":
                if action == "help":
                    # Generate help message
                    help_message = voice_command_service.get_help_message()
                    command_result["action_result"] = {
                        "success": True,
                        "message": "Available commands:\n" + help_message
                    }
        
        return command_result
    
    def submit_feedback(self, direction_type, was_helpful, context=None):
        """
        Submit user feedback on navigation directions
        
        Args:
            direction_type: Type of direction (e.g., 'turn', 'obstacle_warning')
            was_helpful: Whether direction was helpful
            context: Additional context about the situation
            
        Returns:
            success: Whether feedback was recorded
        """
        if not adaptive_learning_model.user_id:
            return False
        
        # Record feedback in adaptive learning model
        adaptive_learning_model.record_user_feedback(direction_type, was_helpful, context)
        
        # Store last feedback
        self.last_feedback = {
            "direction_type": direction_type,
            "was_helpful": was_helpful,
            "timestamp": time.time()
        }
        
        return True
    
    def _navigation_loop(self):
        """
        Internal navigation loop that runs in a separate thread to continuously 
        update navigation guidance based on detected objects
        """
        step_index = 0
        last_update_time = time.time()
        
        while self.is_active:
            current_time = time.time()
            
            # Get update frequency from adaptive learning if available
            update_frequency = 2.0  # Default
            if adaptive_learning_model.user_id:
                params = adaptive_learning_model.get_adjusted_parameters()
                update_frequency = params.get("navigation_frequency", 2.0)
            
            # Update path at the specified frequency
            if current_time - last_update_time >= update_frequency:
                with self.lock:
                    # Update the obstacle map with the latest detected objects
                    self.path_calculator.update_obstacle_map(self.detected_objects)
                    
                    # Calculate new path
                    self.current_path, new_directions = self.path_calculator.find_path()
                    
                    # Check if directions changed significantly
                    if new_directions and self.current_directions and new_directions[0] != self.current_directions[0]:
                        # Directions changed, reset step index
                        step_index = 0
                        self.current_directions = new_directions
                    elif not self.current_directions:
                        self.current_directions = new_directions
                
                last_update_time = current_time
            
            # Sleep to avoid consuming too much CPU
            time.sleep(0.1)
    
    def get_next_direction(self):
        """
        Get the next direction in the sequence
        
        Returns:
            direction: Next navigation direction
        """
        with self.lock:
            if not self.current_directions:
                return "No directions available."
            
            # Get the first direction and rotate list
            direction = self.current_directions[0]
            if len(self.current_directions) > 1:
                self.current_directions = self.current_directions[1:] + [self.current_directions[0]]
            
            return direction
    
    def _generate_environment_description(self):
        """
        Generate a description of the surroundings based on detected objects
        
        Returns:
            description: Text description of surroundings
        """
        if not self.detected_objects:
            return "I don't see any objects around you."
        
        # Count objects by class
        object_counts = {}
        for obj in self.detected_objects:
            obj_class = obj.get('class', 'unknown')
            object_counts[obj_class] = object_counts.get(obj_class, 0) + 1
        
        # Generate description
        description_parts = ["I can see:"]
        for obj_class, count in object_counts.items():
            if count == 1:
                description_parts.append(f"a {obj_class}")
            else:
                description_parts.append(f"{count} {obj_class}s")
        
        return " ".join(description_parts)
    
    def _identify_central_object(self):
        """
        Identify the central object in the current view
        
        Returns:
            description: Text description of the central object
        """
        if not self.detected_objects:
            return "I don't see any objects."
        
        # Find object closest to center (0.5, 0.5)
        center_x, center_y = 0.5, 0.5
        closest_object = None
        min_distance = float('inf')
        
        for obj in self.detected_objects:
            obj_x = obj.get('x', 0)
            obj_y = obj.get('y', 0)
            distance = ((obj_x - center_x) ** 2 + (obj_y - center_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_object = obj
        
        if closest_object:
            obj_class = closest_object.get('class', 'unknown object')
            confidence = closest_object.get('confidence', 0) * 100
            return f"I see a {obj_class} in front of you with {confidence:.1f}% confidence."
        else:
            return "I don't see any clear objects in front of you."

# Create a singleton instance
navigation_service = NavigationService() 