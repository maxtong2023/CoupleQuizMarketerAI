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
    from tiktok_generator import (
        TikTokVideoGenerator,
        create_placeholder_images,
        create_placeholder_image_pairs,
    )
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
        print("\nTrying to import directly...")
        
        # Try importing the module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("tiktok_generator", "tiktok_generator.py")
        if spec and spec.loader:
            tiktok_generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tiktok_generator)
            TikTokVideoGenerator = tiktok_generator.TikTokVideoGenerator
            create_placeholder_images = tiktok_generator.create_placeholder_images
            create_placeholder_image_pairs = tiktok_generator.create_placeholder_image_pairs
        else:
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
        self.theme_var = tk.StringVar(value="General")
        self.hook_var = tk.StringVar(value="")
        
        # Generator instance
        self.generator = None
        self.image_pairs = []  # List[Tuple[str, str]]
        
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

        ttk.Label(config_frame, text="Theme:").grid(row=1, column=0, sticky=tk.W, pady=(6,0))
        ttk.Entry(config_frame, textvariable=self.theme_var, width=40).grid(row=1, column=1, padx=(5,5), pady=(6,0))

        ttk.Label(config_frame, text="Hook:").grid(row=2, column=0, sticky=tk.W, pady=(6,6))
        ttk.Entry(config_frame, textvariable=self.hook_var, width=60).grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(6,6))
        
        # Questions section
        questions_frame = ttk.LabelFrame(main_frame, text="Questions", padding="10")
        questions_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Questions header with add/remove buttons
        questions_header = ttk.Frame(questions_frame)
        questions_header.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(questions_header, text="Questions:").grid(row=0, column=0, sticky=tk.W)
        ttk.Button(questions_header, text="+ Add Question", command=self.add_question).grid(row=0, column=1, padx=(20, 5))
        ttk.Button(questions_header, text="- Remove Last", command=self.remove_last_question).grid(row=0, column=2, padx=(5, 0))
        
        # Questions list (now using a frame with individual question entries)
        self.questions_container = ttk.Frame(questions_frame)
        self.questions_container.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Initialize with one question
        self.question_entries = []
        self.add_question()
        
        # Hooks section
        hooks_frame = ttk.LabelFrame(main_frame, text="Notes (optional)", padding="10")
        hooks_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Label(hooks_frame, text="You can still paste extra hooks here; the first line is used only if 'Hook' above is empty.").grid(row=0, column=0, sticky=tk.W)
        self.hooks_text = scrolledtext.ScrolledText(hooks_frame, height=3, width=60)
        self.hooks_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Images section
        images_frame = ttk.LabelFrame(main_frame, text="Images", padding="10")
        images_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(images_frame, text="Select Images (2 per question)", command=self.select_images).grid(row=0, column=0, sticky=tk.W)
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
                # Clear existing question entries and recreate from loaded data
                for entry in self.question_entries:
                    entry.destroy()
                self.question_entries.clear()
                
                for question in self.questions:
                    self.add_question(question)
            
            # Load hooks
            if os.path.exists("hooks.json"):
                with open("hooks.json", "r") as f:
                    self.hooks = json.load(f)
                self.hooks_text.delete(1.0, tk.END)
                self.hooks_text.insert(1.0, "\n".join(self.hooks))
                # Default hook value if empty
                if not self.hook_var.get() and self.hooks:
                    self.hook_var.set(self.hooks[0])
            
            self.log("Data loaded successfully")
            
        except Exception as e:
            self.log(f"Error loading data: {e}", "error")
    
    def add_question(self, question_text: str = ""):
        """Add a new question entry field."""
        question_num = len(self.question_entries) + 1
        
        # Create frame for this question
        question_frame = ttk.Frame(self.questions_container)
        question_frame.grid(row=question_num-1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(2, 0))
        
        # Question label and entry
        ttk.Label(question_frame, text=f"Q{question_num}:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        question_entry = ttk.Entry(question_frame, width=70)
        question_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        question_entry.insert(0, question_text)
        
        # Store reference
        self.question_entries.append(question_frame)
        
        # Update grid weights
        self.questions_container.columnconfigure(1, weight=1)
    
    def remove_last_question(self):
        """Remove the last question entry."""
        if len(self.question_entries) > 1:  # Keep at least one question
            last_entry = self.question_entries.pop()
            last_entry.destroy()
            self.log("Removed last question")
        else:
            messagebox.showinfo("Info", "You need at least one question!")
    
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
            self.image_pairs = []  # reset; will form pairs during generation
            self.images_label.config(text=f"{len(self.image_paths)} images selected (need 2 per question)")
            self.log(f"Selected {len(self.image_paths)} images (need 2 per question)")
    
    def create_placeholders(self):
        """Create placeholder images for testing."""
        try:
            # Get questions from entry fields
            self.questions = []
            for entry_frame in self.question_entries:
                for child in entry_frame.winfo_children():
                    if isinstance(child, ttk.Entry):
                        question_text = child.get().strip()
                        if question_text:
                            self.questions.append(question_text)
                        break
            
            if not self.questions:
                messagebox.showwarning("Warning", "Please enter some questions first.")
                return
            
            # Create placeholder images
            self.image_pairs = create_placeholder_image_pairs(self.questions, "output")
            flat = [p for pair in self.image_pairs for p in pair]
            self.image_paths = flat
            self.images_label.config(text=f"{len(self.image_paths)} placeholder images created ({len(self.image_pairs)} pairs)")
            self.log(f"Created {len(self.image_pairs)} placeholder pairs / {len(self.image_pairs)} images")
            
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
        
        if len(self.image_paths) % 2 != 0:
            messagebox.showerror("Error", "The number of images must be even (2 per question).")
            return
        if len(self.questions) * 2 != len(self.image_paths):
            messagebox.showerror("Error", f"You selected {len(self.image_paths)} images for {len(self.questions)} questions. You need exactly 2 images per question ({len(self.questions)*2}).")
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
            self.questions = []
            for entry_frame in self.question_entries:
                # Find the entry widget in this frame
                for child in entry_frame.winfo_children():
                    if isinstance(child, ttk.Entry):
                        question_text = child.get().strip()
                        if question_text:
                            self.questions.append(question_text)
                        break
            
            hooks_text = self.hooks_text.get(1.0, tk.END).strip()
            self.hooks = [h.strip() for h in hooks_text.split('\n') if h.strip()]
            theme = self.theme_var.get().strip() or "General"
            hook = self.hook_var.get().strip() or (self.hooks[0] if self.hooks else "Let's play!")
            
            # Initialize generator
            self.generator = TikTokVideoGenerator(self.config_path.get())
            
            # Prepare image pairs
            if not self.image_pairs and self.image_paths:
                # Chunk into pairs
                self.image_pairs = [(self.image_paths[i], self.image_paths[i+1]) for i in range(0, len(self.image_paths), 2)]
            
            # Generate video
            output_path = self.generator.generate_video(
                questions=self.questions,
                theme=theme,
                hook=hook,
                question_image_pairs=self.image_pairs,
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
