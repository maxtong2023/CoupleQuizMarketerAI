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
    level=logging.DEBUG,  # Temporarily enable debug logging
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
        self.text_stroke_color = self.config["video_settings"].get("text_stroke_color", "black")
        self.text_stroke_width = self.config["video_settings"].get("text_stroke_width", 0)
        self.font_path = self.config["video_settings"].get("font_path", "fonts/Renogare-Regular.ttf")
        
        # Brand/background colors
        self.bg_color_hex = self.config["video_settings"].get("background_color", "#dfe3fd")
        self.text_color_hex = self.config["video_settings"].get("brand_text_color", "#8b8d9b")
        self.bg_color_rgb = self._hex_to_rgb(self.bg_color_hex)
        self.text_color_rgb = self._hex_to_rgb(self.text_color_hex)
        
        self.question_duration = self.config["timing_settings"]["question_duration"]
        self.pause_duration = self.config["timing_settings"]["pause_duration"]
        self.hook_duration = self.config["timing_settings"]["hook_duration"]
        
        self.voice_id = self.config["voice_settings"]["voice_id"]
        
        logger.info(f"Initialized TikTok Video Generator with config: {config_path}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Using font: {self.font_path}")
    
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

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        try:
            # Check if font file exists
            if not os.path.exists(self.font_path):
                logger.warning(f"Font file not found at {self.font_path}, using default font")
                return ImageFont.load_default()
            
            logger.debug(f"Loading font from {self.font_path} with size {size}")
            font = ImageFont.truetype(self.font_path, size)
            logger.debug(f"Font loaded successfully: {font}")
            return font
        except Exception as e:
            logger.warning(f"Error loading font {self.font_path}: {e}. Using default font.")
            return ImageFont.load_default()

    def _render_text_image(self, text: str, max_width: int, font_size: int, color_rgb: tuple) -> Image.Image:
        logger.debug(f"Rendering text image: '{text[:30]}...' with font_size={font_size}, max_width={max_width}")
        
        # Wrap text to fit max_width
        font = self._load_font(font_size)
        lines = []
        words = text.split()
        current = ''
        for word in words:
            trial = (current + ' ' + word).strip()
            # Use textlength for PIL 10+ compatibility
            try:
                w = ImageDraw.Draw(Image.new('RGB', (10, 10))).textlength(trial, font=font)
            except AttributeError:
                # Fallback for older PIL versions
                w, _ = ImageDraw.Draw(Image.new('RGB', (10, 10))).textsize(trial, font=font)
            if w <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        # Compute image size
        line_heights = []
        max_line_width = 0
        for line in lines:
            try:
                w = ImageDraw.Draw(Image.new('RGB', (10, 10))).textlength(line, font=font)
                h = font_size  # Approximate height
            except AttributeError:
                # Fallback for older PIL versions
                w, h = ImageDraw.Draw(Image.new('RGB', (10, 10))).textsize(line, font=font)
            max_line_width = max(max_line_width, w)
            line_heights.append(h)
        total_height = int(sum(line_heights) + (len(lines) - 1) * (font_size * 0.35))
        img = Image.new('RGBA', (int(max_line_width + 8), int(total_height + 8)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        y = 0
        for idx, line in enumerate(lines):
            draw.text((4, int(y)), line, font=font, fill=color_rgb + (255,))
            y += line_heights[idx] + (font_size * 0.35)
        return img

    def _text_clip(self, text: str, duration: float, font_size: int, max_width: int, pos: tuple, animate: bool = True) -> ImageClip:
        # Ensure position is integers
        pos = (int(pos[0]), int(pos[1]))
        logger.debug(f"Creating text clip: '{text[:30]}...' at position {pos}")
        
        pil_img = self._render_text_image(text, max_width=max_width, font_size=font_size, color_rgb=self.text_color_rgb)
        clip = ImageClip(np.array(pil_img)).set_duration(duration)
        
        # Animate entrance from slight offset and fade in/out
        if animate:
            start_offset = 60
            def position_at_time(t):
                # Ease-in to target position over 0.5s
                if t < 0.5:
                    progress = t / 0.5
                    return (pos[0], pos[1] + int((1 - progress) * start_offset))
                return pos
            clip = clip.set_position(position_at_time).fadein(0.4).fadeout(0.4)
        else:
            clip = clip.set_position(pos)
        return clip
    
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
    
    # Old TextClip creator not used anymore; replaced with PIL-based _text_clip for custom font/color
    
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
            # Create image clip directly (assume it will be composed on background)
            image_clip = ImageClip(image_path).set_duration(duration)
            
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
            # Create brand background
            background = ColorClip(
                size=(self.width, self.height), 
                color=self.bg_color_rgb
            ).set_duration(duration)
            
            # Add clock sound if provided
            if clock_audio_path and os.path.exists(clock_audio_path):
                audio_clip = AudioFileClip(clock_audio_path)
                background = background.set_audio(audio_clip)
            
            return background
            
        except Exception as e:
            logger.error(f"Error creating pause clip: {e}")
            raise
    
    def create_question_clip(self, question: str, image_path_top: str, image_path_bottom: str, audio_path: str) -> CompositeVideoClip:
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
            logger.debug(f"Creating question clip for: '{question[:30]}...'")
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 3.0  # extra 3s pause after TTS
            
            # Background
            bg = ColorClip(size=(self.width, self.height), color=self.bg_color_rgb).set_duration(duration)

            # Images will be resized and cropped to square in the create_resized_clip function below

            # Compute layout
            margin_x = 90
            max_text_width = self.width - 2 * margin_x
            question_font_size = int(self.text_font_size * 1.1)
            or_font_size = int(self.text_font_size * 0.9)
            
            # Render text clips
            question_clip = self._text_clip(
                text=question,
                duration=duration,
                font_size=question_font_size,
                max_width=max_text_width,
                pos=(int(self.width/2 - max_text_width/2), 100),
                animate=True
            )
            or_clip = self._text_clip(
                text="Or",
                duration=duration,
                font_size=or_font_size,
                max_width=200,
                pos=(int(self.width/2 - 50), 1000),
                animate=True
            )

            # Size images - resize the PIL images before creating clips to avoid MoviePy resize issues
            img_width = self.width - 2 * margin_x
            img_size = int(min(img_width, 900))
            
            # Create resized image clips directly from PIL images to avoid MoviePy resize issues
            def create_resized_clip(image_path, new_size):
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Crop to square first
                    w, h = img.size
                    if w == h:
                        cropped = img
                    elif w > h:
                        left = (w - h) // 2
                        cropped = img.crop((left, 0, left + h, h))
                    else:
                        top = (h - w) // 2
                        cropped = img.crop((0, top, w, top + w))
                    
                    # Resize to target size
                    img_resized = cropped.resize((new_size, new_size), Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    resized_path = str(self.output_dir / f"_resized_{Path(image_path).stem}.jpg")
                    img_resized.save(resized_path, 'JPEG', quality=92)
                    
                    # Create new clip with resized image
                    return ImageClip(resized_path).set_duration(duration)
            
            top_img_clip = create_resized_clip(image_path_top, img_size)
            bottom_img_clip = create_resized_clip(image_path_bottom, img_size)
            
            # Position calculations
            y_top_img = int(100 + question_font_size * 2.2)
            logger.debug(f"Positioning top image at y={y_top_img}")
            top_img_clip = top_img_clip.set_position((int((self.width - img_size)/2), y_top_img))
            
            y_or = int(y_top_img + img_size + 30)
            logger.debug(f"Positioning 'Or' text at y={y_or}")
            or_clip = or_clip.set_position((int((self.width - 100)/2), y_or))
            
            y_bottom_img = int(y_or + or_font_size * 1.6)
            logger.debug(f"Positioning bottom image at y={y_bottom_img}")
            bottom_img_clip = bottom_img_clip.set_position((int((self.width - img_size)/2), y_bottom_img))

            # Build composite
            composite = CompositeVideoClip([bg, top_img_clip, or_clip, bottom_img_clip, question_clip]).set_duration(duration)
            composite = composite.set_audio(audio_clip)
            return composite
            
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
            
            # Create branded background
            background = ColorClip(
                size=(self.width, self.height), 
                color=self.bg_color_rgb
            ).set_duration(duration)
            
            # Create animated text clip
            text_width = int(self.width * 0.9)
            text_clip = self._text_clip(
                text=hook,
                duration=duration,
                font_size=self.text_font_size,
                max_width=text_width,
                pos=(int(self.width/2 - text_width/2), int(self.height/2 - self.text_font_size)),
                animate=True
            )
            
            # Combine background and text
            video_clip = CompositeVideoClip([background, text_clip])
            
            # Add audio
            video_clip = video_clip.set_audio(audio_clip)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error creating hook clip: {e}")
            raise
    
    def create_intro_clip(self, theme: str) -> CompositeVideoClip:
        # Short intro with title and theme
        duration = 2.8
        bg = ColorClip(size=(self.width, self.height), color=self.bg_color_rgb).set_duration(duration)
        title_width = int(self.width * 0.9)
        title_clip = self._text_clip(
            text="Couples Quiz!",
            duration=duration,
            font_size=int(self.text_font_size * 1.2),
            max_width=title_width,
            pos=(int(self.width/2 - title_width/2), 220),
            animate=True
        )
        theme_label = self._text_clip(
            text="Today's theme is:",
            duration=duration,
            font_size=self.text_font_size,
            max_width=title_width,
            pos=(int(self.width/2 - title_width/2), 420),
            animate=True
        )
        theme_text = self._text_clip(
            text=theme,
            duration=duration,
            font_size=int(self.text_font_size * 1.1),
            max_width=title_width,
            pos=(int(self.width/2 - title_width/2), 560),
            animate=True
        )
        return CompositeVideoClip([bg, title_clip, theme_label, theme_text]).set_duration(duration)

    def create_share_clip(self) -> CompositeVideoClip:
        duration = 2.4
        bg = ColorClip(size=(self.width, self.height), color=self.bg_color_rgb).set_duration(duration)
        text_width = int(self.width * 0.9)
        text_clip = self._text_clip(
            text="save and share this with them!",
            duration=duration,
            font_size=int(self.text_font_size * 1.05),
            max_width=text_width,
            pos=(int(self.width/2 - text_width/2), int(self.height/2 - self.text_font_size)),
            animate=True
        )
        return CompositeVideoClip([bg, text_clip]).set_duration(duration)

    def generate_video(self, 
                       questions: List[str], 
                       theme: str,
                       hook: str,
                       question_image_pairs: List[tuple],
                       clock_audio_path: Optional[str] = None,
                       output_filename: Optional[str] = None) -> str:
        """
        Generate the complete TikTok video.
        
        Args:
            questions: List of question texts
            theme: The theme string
            hook: The hook string
            question_image_pairs: List of (img1, img2) per question
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
            if len(questions) != len(question_image_pairs):
                raise ValueError(f"Number of questions ({len(questions)}) must match number of image pairs ({len(question_image_pairs)})")
            
            clips = []
            
            # Intro
            clips.append(self.create_intro_clip(theme))
            
            # Hook
            logger.info("Generating hook clip...")
            hook_audio_path = self.generate_tts_audio(hook, "hook")
            hook_clip = self.create_hook_clip(hook, hook_audio_path)
            clips.append(hook_clip)
            
            # Share CTA
            clips.append(self.create_share_clip())
            
            # Generate clips for each question
            for i, (question, img_pair) in enumerate(zip(questions, question_image_pairs)):
                logger.info(f"Generating clip for question {i+1}...")
                
                # Generate TTS for question
                question_audio_path = self.generate_tts_audio(question, f"question_{i+1}")
                
                # Create question clip
                img1, img2 = img_pair
                question_clip = self.create_question_clip(question, img1, img2, question_audio_path)
                clips.append(question_clip)
            
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
    """Deprecated: kept for backward compatibility. Creates one image per question."""
    pairs = create_placeholder_image_pairs(questions, output_dir)
    # Flatten and return only first image per pair to preserve old behavior
    return [pair[0] for pair in pairs]

def create_placeholder_image_pairs(questions: List[str], output_dir: str = "output") -> List[tuple]:
    """Create two square placeholder images per question and return a list of (img1, img2) tuples."""
    output_pairs: List[tuple] = []
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for i, question in enumerate(questions):
        # Two colors for variety
        base_colors = [
            (210, 230, 255),
            (200, 210, 240),
            (230, 220, 255),
            (220, 255, 230),
            (255, 230, 220),
        ]
        color1 = base_colors[i % len(base_colors)]
        color2 = base_colors[(i + 2) % len(base_colors)]
        
        for variant in ["A", "B"]:
            img = Image.new('RGB', (1080, 1080), color=(color1 if variant == "A" else color2))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
            except Exception:
                font = ImageFont.load_default()
            draw.text((540, 540), f"Q{i+1} {variant}", fill=(50, 50, 80), anchor="mm", font=font)
            placeholder_path = str(output_path / f"placeholder_q{i+1}_{variant}.jpg")
            img.save(placeholder_path)
            if variant == "A":
                first = placeholder_path
            else:
                second = placeholder_path
        output_pairs.append((first, second))
    return output_pairs

def main():
    """Main function to run the video generator."""
    parser = argparse.ArgumentParser(description="Generate TikTok quiz videos")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--images", nargs="+", help="Paths to question images (must be 2 per question, in order)")
    parser.add_argument("--clock-audio", help="Path to clock sound effect")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--create-placeholders", action="store_true", help="Create placeholder images for testing (two per question)")
    parser.add_argument("--theme", help="Theme string to display in intro")
    parser.add_argument("--hook", help="Hook string to TTS and display")
    
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
        
        # Theme and hook
        theme = args.theme if args.theme else "General"
        hook = args.hook if args.hook else (hooks[0] if hooks else "Let's play!")

        # Handle images (must be 2 per question)
        if args.images:
            image_paths = args.images
            if len(image_paths) != len(questions) * 2:
                raise ValueError(f"You provided {len(image_paths)} images for {len(questions)} questions; expected {len(questions)*2} images (2 per question).")
            question_image_pairs = [(image_paths[i], image_paths[i+1]) for i in range(0, len(image_paths), 2)]
            logger.info(f"Using provided image pairs: {question_image_pairs}")
        elif args.create_placeholders:
            question_image_pairs = create_placeholder_image_pairs(questions, generator.output_dir)
            logger.info(f"Created placeholder image pairs: {question_image_pairs}")
        else:
            question_image_pairs = create_placeholder_image_pairs(questions, generator.output_dir)
            logger.info(f"Created placeholder image pairs: {question_image_pairs}")
        
        # Generate video
        output_path = generator.generate_video(
            questions=questions,
            theme=theme,
            hook=hook,
            question_image_pairs=question_image_pairs,
            clock_audio_path=args.clock_audio,
            output_filename=args.output
        )
        
        print(f"✅ Video generated successfully: {output_path}")
        
        # Clean up placeholder images if we created them
        if args.create_placeholders or (not args.images):
            for pair in question_image_pairs:
                for path in pair:
                    if os.path.exists(path) and "placeholder" in path:
                        os.remove(path)
                        logger.info(f"Cleaned up placeholder image: {path}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
