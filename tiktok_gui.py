#!/usr/bin/env python3
"""
TikTok Quiz Video Generator - GUI Version
==========================================

A simple GUI interface for the TikTok video generator.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from pathlib import Path
import sys

# Import our modules
try:
    from tiktok_generator import TikTokVideoGenerator, create_placeholder_images
except ImportError:
    # Try alternative import paths
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from tiktok_generator import TikTokVideoGenerator, create_placeholder_images
    except ImportError:
        print("Error: Could not import tiktok_generator module.")
        print("Make sure tiktok_generator.py exists in the same directory.")
        print("Current directory:", os.getcwd())
        print("Files in directory:", os.listdir('.'))
        sys.exit(1)

class TikTokGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Quiz Video Generator")
        self.root.geometry("800x600")
        
        # Variables
        self.questions = []
        self.hooks = []
        self.image_paths = []
        self.clock_audio_path = tk.StringVar()
        self.output_filename = tk.StringVar(value="tiktok_quiz_video.mp4")
        self.config_path = tk.StringVar(value="config.json")
        
        # Generator instance
        self.generator = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="TikTok Quiz Video Generator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(config_frame, text="Config File:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.config_path, width=40).grid(row=0, column=1, padx=(5, 5))
        ttk.Button(config_frame, text="Browse", command=self.browse_config).grid(row=0, column=2)
        
        # Questions section
        questions_frame = ttk.LabelFrame(main_frame, text="Questions", padding="10")
        questions_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Questions list
        ttk.Label(questions_frame, text="Questions:").grid(row=0, column=0, sticky=tk.W)
        self.questions_text = scrolledtext.ScrolledText(questions_frame, height=6, width=60)
        self.questions_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Hooks section
        hooks_frame = ttk.LabelFrame(main_frame, text="Hooks", padding="10")
        hooks_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(hooks_frame, text="Hooks:").grid(row=0, column=0, sticky=tk.W)
        self.hooks_text = scrolledtext.ScrolledText(hooks_frame, height=4, width=60)
        self.hooks_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Images section
        images_frame = ttk.LabelFrame(main_frame, text="Images", padding="10")
        images_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(images_frame, text="Select Images", command=self.select_images).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(images_frame, text="Create Placeholders", command=self.create_placeholders).grid(row=0, column=1, padx=(10, 0))
        
        self.images_label = ttk.Label(images_frame, text="No images selected")
        self.images_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Clock audio section
        audio_frame = ttk.LabelFrame(main_frame, text="Audio", padding="10")
        audio_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(audio_frame, text="Clock Sound (optional):").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(audio_frame, textvariable=self.clock_audio_path, width=50).grid(row=0, column=1, padx=(5, 5))
        ttk.Button(audio_frame, text="Browse", command=self.browse_clock_audio).grid(row=0, column=2)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(output_frame, text="Output Filename:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(output_frame, textvariable=self.output_filename, width=50).grid(row=0, column=1, padx=(5, 5))
        
        # Generate button
        self.generate_button = ttk.Button(main_frame, text="Generate Video", 
                                        command=self.generate_video, style="Accent.TButton")
        self.generate_button.grid(row=7, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to generate video")
        self.status_label.grid(row=9, column=0, columnspan=3)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for log frame
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
    
    def load_data(self):
        """Load questions and hooks from JSON files."""
        try:
            # Load questions
            if os.path.exists("questions.json"):
                with open("questions.json", "r") as f:
                    self.questions = json.load(f)
                self.questions_text.delete(1.0, tk.END)
                self.questions_text.insert(1.0, "\n".join(self.questions))
            
            # Load hooks
            if os.path.exists("hooks.json"):
                with open("hooks.json", "r") as f:
                    self.hooks = json.load(f)
                self.hooks_text.delete(1.0, tk.END)
                self.hooks_text.insert(1.0, "\n".join(self.hooks))
            
            self.log("Data loaded successfully")
            
        except Exception as e:
            self.log(f"Error loading data: {e}", "error")
    
    def browse_config(self):
        """Browse for configuration file."""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_path.set(filename)
    
    def select_images(self):
        """Select image files for questions."""
        filenames = filedialog.askopenfilenames(
            title="Select Question Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if filenames:
            self.image_paths = list(filenames)
            self.images_label.config(text=f"{len(self.image_paths)} images selected")
            self.log(f"Selected {len(self.image_paths)} images")
    
    def create_placeholders(self):
        """Create placeholder images for testing."""
        try:
            # Get questions from text area
            questions_text = self.questions_text.get(1.0, tk.END).strip()
            if questions_text:
                self.questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            if not self.questions:
                messagebox.showwarning("Warning", "Please enter some questions first.")
                return
            
            # Create placeholder images
            self.image_paths = create_placeholder_images(self.questions, "output")
            self.images_label.config(text=f"{len(self.image_paths)} placeholder images created")
            self.log(f"Created {len(self.image_paths)} placeholder images")
            
        except Exception as e:
            self.log(f"Error creating placeholders: {e}", "error")
            messagebox.showerror("Error", f"Failed to create placeholder images: {e}")
    
    def browse_clock_audio(self):
        """Browse for clock sound effect."""
        filename = filedialog.askopenfilename(
            title="Select Clock Sound Effect",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.m4a *.aac"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.clock_audio_path.set(filename)
    
    def log(self, message, level="info"):
        """Add message to log area."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if level == "error":
            tag = "error"
            color = "red"
        elif level == "warning":
            tag = "warning"
            color = "orange"
        else:
            tag = "info"
            color = "black"
        
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # Apply color tags
        last_line_start = self.log_text.index("end-2c linestart")
        last_line_end = self.log_text.index("end-1c")
        
        self.log_text.tag_add(tag, last_line_start, last_line_end)
        self.log_text.tag_config(tag, foreground=color)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
    
    def generate_video(self):
        """Generate the TikTok video in a separate thread."""
        if not self.questions:
            messagebox.showwarning("Warning", "Please enter some questions first.")
            return
        
        if not self.image_paths:
            messagebox.showwarning("Warning", "Please select images or create placeholders first.")
            return
        
        if len(self.questions) != len(self.image_paths):
            messagebox.showerror("Error", f"Number of questions ({len(self.questions)}) must match number of images ({len(self.image_paths)})")
            return
        
        # Disable generate button and show progress
        self.generate_button.config(state="disabled")
        self.progress.start()
        self.status_label.config(text="Generating video...")
        
        # Start generation in separate thread
        thread = threading.Thread(target=self._generate_video_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_video_thread(self):
        """Generate video in background thread."""
        try:
            # Get current data from UI
            questions_text = self.questions_text.get(1.0, tk.END).strip()
            hooks_text = self.hooks_text.get(1.0, tk.END).strip()
            
            self.questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            self.hooks = [h.strip() for h in hooks_text.split('\n') if h.strip()]
            
            # Initialize generator
            self.generator = TikTokVideoGenerator(self.config_path.get())
            
            # Generate video
            output_path = self.generator.generate_video(
                questions=self.questions,
                hooks=self.hooks,
                image_paths=self.image_paths,
                clock_audio_path=self.clock_audio_path.get() if self.clock_audio_path.get() else None,
                output_filename=self.output_filename.get()
            )
            
            # Update UI on main thread
            self.root.after(0, self._generation_complete, output_path, None)
            
        except Exception as e:
            # Update UI on main thread
            self.root.after(0, self._generation_complete, None, str(e))
    
    def _generation_complete(self, output_path, error):
        """Handle video generation completion."""
        # Stop progress and re-enable button
        self.progress.stop()
        self.generate_button.config(state="normal")
        
        if error:
            self.status_label.config(text="Generation failed")
            self.log(f"Video generation failed: {error}", "error")
            messagebox.showerror("Error", f"Failed to generate video: {error}")
        else:
            self.status_label.config(text="Video generated successfully!")
            self.log(f"Video generated successfully: {output_path}")
            messagebox.showinfo("Success", f"Video generated successfully!\n\nOutput: {output_path}")

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = TikTokGeneratorGUI(root)
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Run the application
    root.mainloop()

if __name__ == "__main__":
    main()
