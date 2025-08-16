#!/usr/bin/env python3
"""
TikTok Quiz Video Generator
============================

This script generates TikTok-style quiz videos with:
- Custom questions and hooks from JSON files
- Text-to-speech using ElevenLabs API
- Image processing for TikTok's 9:16 aspect ratio
- Video composition with MoviePy
- Pause clips between questions
- Professional text styling and animations

Usage:
    python tiktok_generator.py [--config config.json] [--images image1.jpg image2.jpg ...]
"""

import os
import json
import argparse
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
import logging
import sys

# Video and audio processing
from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip, 
    CompositeVideoClip, concatenate_videoclips, ColorClip
)
from moviepy.video.fx import resize, fadein, fadeout
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# TTS
try:
    from elevenlabs import ElevenLabs
except ImportError:
    # Try newer import
    try:
        from elevenlabs import generate, set_api_key
        ELEVENLABS_NEW_API = True
    except ImportError:
        print("Error: Could not import ElevenLabs. Please install: pip install elevenlabs")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tiktok_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TikTokVideoGenerator:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the TikTok video generator with configuration.
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config = self._load_config(config_path)
        
        # Initialize ElevenLabs (try both old and new APIs)
        try:
            self.elevenlabs = ElevenLabs(api_key=self.config["voice_settings"]["api_key"])
        except:
            # New API doesn't need initialization
            self.elevenlabs = None
        
        # Set up output directory
        self.output_dir = Path(self.config["output_settings"]["output_dir"])
        self.output_dir.mkdir(exist_ok=True)
        
        # Load settings from config
        self.width = self.config["video_settings"]["width"]
        self.height = self.config["video_settings"]["height"]
        self.fps = self.config["video_settings"]["fps"]
        self.text_font_size = self.config["video_settings"]["text_font_size"]
        self.text_color = self.config["video_settings"]["text_color"]
        self.text_stroke_color = self.config["video_settings"]["text_stroke_color"]
        self.text_stroke_width = self.config["video_settings"]["text_stroke_width"]
        
        self.question_duration = self.config["timing_settings"]["question_duration"]
        self.pause_duration = self.config["timing_settings"]["pause_duration"]
        self.hook_duration = self.config["timing_settings"]["hook_duration"]
        
        self.voice_id = self.config["voice_settings"]["voice_id"]
        
        logger.info(f"Initialized TikTok Video Generator with config: {config_path}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def resize_image_for_tiktok(self, image_path: str) -> str:
        """
        Resize or pad an image to fit TikTok's 1080x1920 format.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Path to the resized image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate new dimensions maintaining aspect ratio
                img_ratio = img.width / img.height
                target_ratio = self.width / self.height
                
                if img_ratio > target_ratio:
                    # Image is wider than target, fit to height
                    new_height = self.height
                    new_width = int(self.height * img_ratio)
                else:
                    # Image is taller than target, fit to width
                    new_width = self.width
                    new_height = int(self.width / img_ratio)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create new image with target dimensions and black background
                new_img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
                
                # Calculate position to center the image
                x = (self.width - new_width) // 2
                y = (self.height - new_height) // 2
                
                # Paste resized image onto background
                new_img.paste(img_resized, (x, y))
                
                # Save resized image
                output_path = str(self.output_dir / f"resized_{Path(image_path).name}")
                new_img.save(output_path, 'JPEG', quality=95)
                
                logger.info(f"Image resized and saved to {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            raise
    
    def generate_tts_audio(self, text: str, filename: str) -> str:
        """
        Generate TTS audio for given text using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            filename: Name for the output audio file
            
        Returns:
            Path to the generated audio file
        """
        try:
            if hasattr(self, 'elevenlabs') and self.elevenlabs:
                # Old API
                audio = self.elevenlabs.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text
                )
            else:
                # New API
                from elevenlabs import generate, set_api_key
                set_api_key(self.config["voice_settings"]["api_key"])
                audio = generate(
                    text=text,
                    voice=self.voice_id,
                    model="eleven_monolingual_v1"
                )
            
            output_path = str(self.output_dir / f"{filename}.mp3")
            with open(output_path, "wb") as f:
                f.write(audio)
            
            logger.info(f"TTS audio generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating TTS for '{text}': {e}")
            raise
    
    def create_text_clip(self, text: str, duration: float, position: str = "center") -> TextClip:
        """
        Create a text clip with styling and positioning.
        
        Args:
            text: Text to display
            duration: Duration of the text clip
            position: Position on screen ("center", "top", "bottom")
            
        Returns:
            TextClip object
        """
        try:
            # Create text clip
            text_clip = TextClip(
                text, 
                fontsize=self.text_font_size,
                color=self.text_color,
                stroke_color=self.text_stroke_color,
                stroke_width=self.text_stroke_width,
                font='Arial-Bold',
                method='caption',
                size=(self.width * 0.9, None)  # 90% of width
            ).set_duration(duration)
            
            # Position the text
            if position == "center":
                text_clip = text_clip.set_position(("center", "center"))
            elif position == "top":
                text_clip = text_clip.set_position(("center", 100))
            elif position == "bottom":
                text_clip = text_clip.set_position(("center", self.height - 200))
            
            # Add fade effects
            text_clip = text_clip.fadein(0.5).fadeout(0.5)
            
            return text_clip
            
        except Exception as e:
            logger.error(f"Error creating text clip: {e}")
            raise
    
    def create_image_clip(self, image_path: str, duration: float) -> ImageClip:
        """
        Create an image clip with fade effects.
        
        Args:
            image_path: Path to the image
            duration: Duration of the clip
            
        Returns:
            ImageClip object
        """
        try:
            # Resize image for TikTok format
            resized_path = self.resize_image_for_tiktok(image_path)
            
            # Create image clip
            image_clip = ImageClip(resized_path).set_duration(duration)
            
            # Add fade effects
            image_clip = image_clip.fadein(0.5).fadeout(0.5)
            
            return image_clip
            
        except Exception as e:
            logger.error(f"Error creating image clip: {e}")
            raise
    
    def create_pause_clip(self, duration: float, clock_audio_path: Optional[str] = None) -> CompositeVideoClip:
        """
        Create a pause clip with optional clock sound.
        
        Args:
            duration: Duration of the pause
            clock_audio_path: Optional path to clock sound effect
            
        Returns:
            CompositeVideoClip object
        """
        try:
            # Create black background
            background = ColorClip(
                size=(self.width, self.height), 
                color=(0, 0, 0)
            ).set_duration(duration)
            
            # Add clock sound if provided
            if clock_audio_path and os.path.exists(clock_audio_path):
                audio_clip = AudioFileClip(clock_audio_path)
                background = background.set_audio(audio_clip)
            
            return background
            
        except Exception as e:
            logger.error(f"Error creating pause clip: {e}")
            raise
    
    def create_question_clip(self, question: str, image_path: str, audio_path: str) -> CompositeVideoClip:
        """
        Create a video clip for a question with image, text, and audio.
        
        Args:
            question: Question text
            image_path: Path to the question image
            audio_path: Path to the question audio
            
        Returns:
            CompositeVideoClip object
        """
        try:
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create image clip
            image_clip = self.create_image_clip(image_path, duration)
            
            # Create text clip
            text_clip = self.create_text_clip(question, duration, "center")
            
            # Combine image and text
            video_clip = CompositeVideoClip([image_clip, text_clip])
            
            # Add audio
            video_clip = video_clip.set_audio(audio_clip)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error creating question clip: {e}")
            raise
    
    def create_hook_clip(self, hook: str, audio_path: str) -> CompositeVideoClip:
        """
        Create a video clip for the hook with text and audio.
        
        Args:
            hook: Hook text
            audio_path: Path to the hook audio
            
        Returns:
            CompositeVideoClip object
        """
        try:
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create background (you can customize this)
            background = ColorClip(
                size=(self.width, self.height), 
                color=(20, 20, 60)  # Dark blue
            ).set_duration(duration)
            
            # Create text clip
            text_clip = self.create_text_clip(hook, duration, "center")
            
            # Combine background and text
            video_clip = CompositeVideoClip([background, text_clip])
            
            # Add audio
            video_clip = video_clip.set_audio(audio_clip)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error creating hook clip: {e}")
            raise
    
    def generate_video(self, 
                       questions: List[str], 
                       hooks: List[str], 
                       image_paths: List[str],
                       clock_audio_path: Optional[str] = None,
                       output_filename: Optional[str] = None) -> str:
        """
        Generate the complete TikTok video.
        
        Args:
            questions: List of question texts
            hooks: List of hook texts
            image_paths: List of image paths (one per question)
            clock_audio_path: Optional path to clock sound effect
            output_filename: Name for the output video file
            
        Returns:
            Path to the generated video file
        """
        try:
            logger.info("Starting video generation...")
            
            # Use config filename if none provided
            if output_filename is None:
                output_filename = self.config["output_settings"]["output_filename"]
            
            # Validate inputs
            if len(questions) != len(image_paths):
                raise ValueError(f"Number of questions ({len(questions)}) must match number of images ({len(image_paths)})")
            
            clips = []
            
            # Generate hook clip (use first hook)
            if hooks:
                logger.info("Generating hook clip...")
                hook_audio_path = self.generate_tts_audio(hooks[0], "hook")
                hook_clip = self.create_hook_clip(hooks[0], hook_audio_path)
                clips.append(hook_clip)
            
            # Generate clips for each question
            for i, (question, image_path) in enumerate(zip(questions, image_paths)):
                logger.info(f"Generating clip for question {i+1}...")
                
                # Generate TTS for question
                question_audio_path = self.generate_tts_audio(question, f"question_{i+1}")
                
                # Create question clip
                question_clip = self.create_question_clip(question, image_path, question_audio_path)
                clips.append(question_clip)
                
                # Add pause clip (except after the last question)
                if i < len(questions) - 1:
                    pause_clip = self.create_pause_clip(self.pause_duration, clock_audio_path)
                    clips.append(pause_clip)
            
            # Concatenate all clips
            logger.info("Concatenating video clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Write final video
            output_path = str(self.output_dir / output_filename)
            logger.info(f"Writing final video to {output_path}...")
            
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Video generation complete: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            raise

def create_placeholder_images(questions: List[str], output_dir: str = "output") -> List[str]:
    """Create placeholder images for testing purposes."""
    output_paths = []
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for i, question in enumerate(questions):
        # Create a simple placeholder image
        img = Image.new('RGB', (1080, 1920), color=(50 + i*30, 100 + i*20, 150 + i*10))
        draw = ImageDraw.Draw(img)
        
        # Add text to placeholder
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Wrap text for better display
        words = question.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 20:  # Approximate character limit
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text
        y_position = 800
        for line in lines:
            draw.text((540, y_position), line, fill=(255, 255, 255), anchor="mm", font=font)
            y_position += 80
        
        placeholder_path = str(output_path / f"placeholder_question_{i+1}.jpg")
        img.save(placeholder_path)
        output_paths.append(placeholder_path)
    
    return output_paths

def main():
    """Main function to run the video generator."""
    parser = argparse.ArgumentParser(description="Generate TikTok quiz videos")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--images", nargs="+", help="Paths to question images")
    parser.add_argument("--clock-audio", help="Path to clock sound effect")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--create-placeholders", action="store_true", 
                       help="Create placeholder images for testing")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        with open("questions.json", "r") as f:
            questions = json.load(f)
        
        with open("hooks.json", "r") as f:
            hooks = json.load(f)
        
        logger.info(f"Loaded {len(questions)} questions and {len(hooks)} hooks")
        
        # Initialize generator
        generator = TikTokVideoGenerator(args.config)
        
        # Handle images
        if args.images:
            image_paths = args.images
            logger.info(f"Using provided images: {image_paths}")
        elif args.create_placeholders:
            image_paths = create_placeholder_images(questions, generator.output_dir)
            logger.info(f"Created placeholder images: {image_paths}")
        else:
            # Create placeholder images by default
            image_paths = create_placeholder_images(questions, generator.output_dir)
            logger.info(f"Created placeholder images: {image_paths}")
        
        # Generate video
        output_path = generator.generate_video(
            questions=questions,
            hooks=hooks,
            image_paths=image_paths,
            clock_audio_path=args.clock_audio,
            output_filename=args.output
        )
        
        print(f"✅ Video generated successfully: {output_path}")
        
        # Clean up placeholder images if we created them
        if args.create_placeholders or (not args.images):
            for path in image_paths:
                if os.path.exists(path) and "placeholder" in path:
                    os.remove(path)
                    logger.info(f"Cleaned up placeholder image: {path}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
