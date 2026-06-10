import re
import json
import os
import time
from datetime import datetime

class VoiceCommandService:
    """
    Service for handling voice commands and processing natural language inputs
    from users for navigation and assistance.
    """
    
    def __init__(self, commands_file="voice_commands.json"):
        """
        Initialize the voice command service
        
        Args:
            commands_file: File containing voice command patterns and actions
        """
        self.commands_file = commands_file
        self.command_patterns = self._load_command_patterns()
        self.command_history = []
        self.max_history = 100
        self.last_command_time = 0
        self.cooldown_period = 1.0  # Seconds between commands to avoid duplicate recognition
    
    def _load_command_patterns(self):
        """Load command patterns from file, or create defaults if not exists"""
        if os.path.exists(self.commands_file):
            try:
                with open(self.commands_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading voice commands: {e}")
        
        # Default command patterns
        return {
            "navigation": {
                "find_exit": [
                    "find (the |an |)(exit|way out|door)",
                    "guide me to (the |an |)(exit|way out|door)",
                    "where is (the |an |)(exit|way out|door)",
                    "take me to (the |an |)(exit|way out|door)"
                ],
                "go_forward": [
                    "go (forward|straight|ahead)",
                    "move (forward|straight|ahead)",
                    "walk (forward|straight|ahead)",
                    "continue (forward|straight|ahead)"
                ],
                "go_left": [
                    "go (to the |)left",
                    "turn left",
                    "move left"
                ],
                "go_right": [
                    "go (to the |)right",
                    "turn right",
                    "move right"
                ],
                "stop": [
                    "stop( navigation|)",
                    "halt",
                    "pause( navigation|)",
                    "end navigation"
                ]
            },
            "information": {
                "what_is_around": [
                    "what('s| is) around( me|)",
                    "describe (my |the |)surroundings",
                    "what do you see",
                    "scan (the |my |)environment"
                ],
                "identify_object": [
                    "what('s| is) (this|that)( object|)",
                    "identify (this|that)( object|)",
                    "what do I see",
                    "what am I looking at"
                ],
                "distance_to_object": [
                    "how far (is|to) (the|this|that) (.+)",
                    "distance to (.+)",
                    "how close (is|to) (.+)"
                ]
            },
            "system": {
                "help": [
                    "help( me|)",
                    "what (can|should) I (say|do)",
                    "list commands",
                    "what commands (are available|can I use)"
                ],
                "increase_volume": [
                    "increase volume",
                    "louder",
                    "volume up",
                    "speak (up|louder)"
                ],
                "decrease_volume": [
                    "decrease volume",
                    "quieter",
                    "volume down",
                    "speak (down|quieter)"
                ],
                "repeat": [
                    "repeat( that|)",
                    "say (that |)again",
                    "what did you say"
                ]
            },
            "emergency": {
                "call_for_help": [
                    "call for help",
                    "emergency",
                    "I need (help|assistance)",
                    "SOS"
                ]
            }
        }
    
    def process_command(self, voice_input):
        """
        Process voice input and determine the command
        
        Args:
            voice_input: String containing transcribed voice input
            
        Returns:
            result: Dictionary with command information
        """
        # Check cooldown period to avoid duplicate recognition
        current_time = time.time()
        if current_time - self.last_command_time < self.cooldown_period:
            return {
                "success": False,
                "command_type": None,
                "action": None,
                "confidence": 0,
                "message": "Command cooldown in effect"
            }
        
        self.last_command_time = current_time
        
        # Clean up input
        input_text = voice_input.lower().strip()
        if not input_text:
            return {
                "success": False,
                "command_type": None,
                "action": None,
                "confidence": 0,
                "message": "No input detected"
            }
        
        # Try to match command
        best_match = self._find_best_command_match(input_text)
        
        # Record in history
        self.command_history.append({
            "timestamp": datetime.now().isoformat(),
            "input": input_text,
            "matched_command": best_match["command_type"] + "." + best_match["action"] if best_match["success"] else None,
            "confidence": best_match["confidence"]
        })
        
        # Limit history size
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
        
        return best_match
    
    def _find_best_command_match(self, input_text):
        """
        Find the best matching command for the input
        
        Args:
            input_text: Cleaned voice input
            
        Returns:
            match: Best matching command info
        """
        best_match = {
            "success": False,
            "command_type": None,
            "action": None,
            "confidence": 0,
            "params": {},
            "message": "No matching command found"
        }
        
        # Try to match against all patterns
        for command_type, actions in self.command_patterns.items():
            for action, patterns in actions.items():
                for pattern in patterns:
                    # Create regex pattern - replace spaces with flexible whitespace
                    regex_pattern = f"^{pattern}$"
                    match = re.search(regex_pattern, input_text)
                    
                    if match:
                        # Calculate confidence based on match length relative to input length
                        # Longer matches relative to input = higher confidence
                        confidence = len(match.group(0)) / len(input_text)
                        
                        # If better than current best, update
                        if confidence > best_match["confidence"]:
                            best_match = {
                                "success": True,
                                "command_type": command_type,
                                "action": action,
                                "confidence": confidence,
                                "params": self._extract_params(match, action),
                                "message": f"Matched command: {command_type}.{action}"
                            }
        
        return best_match
    
    def _extract_params(self, match, action):
        """
        Extract parameters from the command match
        
        Args:
            match: Regex match object
            action: Matched action name
            
        Returns:
            params: Dictionary of extracted parameters
        """
        params = {}
        
        # Special case for distance_to_object
        if action == "distance_to_object" and len(match.groups()) >= 1:
            params["object"] = match.group(1)
        
        # Add extracted groups as numbered parameters
        for i, group in enumerate(match.groups()):
            if group:
                params[f"param{i+1}"] = group
        
        return params
    
    def get_available_commands(self):
        """
        Get a list of available voice commands
        
        Returns:
            commands: List of available command phrases by category
        """
        available_commands = {}
        
        for command_type, actions in self.command_patterns.items():
            available_commands[command_type] = {}
            for action, patterns in actions.items():
                # Take the first pattern as example and clean it up
                example = patterns[0]
                # Remove regex parts
                example = re.sub(r'\(.+?\|.+?\)', lambda m: m.group(0).split('|')[0][1:], example)
                example = re.sub(r'\(|\)|\|', '', example)
                available_commands[command_type][action] = example
        
        return available_commands
    
    def get_command_history(self, limit=10):
        """
        Get recent command history
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            history: List of recent commands
        """
        return self.command_history[-limit:]
    
    def add_custom_command(self, command_type, action, patterns):
        """
        Add a custom voice command pattern
        
        Args:
            command_type: Category of command (navigation, information, etc.)
            action: Action name
            patterns: List of regex patterns to match
            
        Returns:
            success: Whether the command was added successfully
        """
        if not command_type or not action or not patterns:
            return False
        
        # Create category if not exists
        if command_type not in self.command_patterns:
            self.command_patterns[command_type] = {}
        
        # Add or update command
        self.command_patterns[command_type][action] = patterns
        
        # Save updated commands
        try:
            with open(self.commands_file, 'w') as f:
                json.dump(self.command_patterns, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving voice commands: {e}")
            return False
    
    def get_help_message(self):
        """
        Get a help message with example commands
        
        Returns:
            help_message: String with help information
        """
        commands = self.get_available_commands()
        
        help_sections = []
        for command_type, actions in commands.items():
            section = f"{command_type.capitalize()} Commands:"
            examples = []
            for action, example in actions.items():
                examples.append(f"• {example}")
            help_sections.append(section + "\n" + "\n".join(examples))
        
        return "\n\n".join(help_sections)

# Create singleton instance
voice_command_service = VoiceCommandService() 