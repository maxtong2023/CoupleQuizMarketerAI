#!/usr/bin/env python3
"""
Example Usage of TikTok Video Generator
=======================================

This script demonstrates how to use the TikTokVideoGenerator class programmatically.
"""

import json
from tiktok_generator import TikTokVideoGenerator, create_placeholder_images

def example_basic_usage():
    """Basic example of generating a TikTok video."""
    print("🎬 TikTok Video Generator - Basic Example")
    print("=" * 50)
    
    # Your ElevenLabs API key
    ELEVENLABS_API_KEY = "your_api_key_here"  # Replace with your actual key
    
    try:
        # Initialize the generator
        generator = TikTokVideoGenerator("config.json")
        
        # Load your content
        with open("questions.json", "r") as f:
            questions = json.load(f)
        
        with open("hooks.json", "r") as f:
            hooks = json.load(f)
        
        print(f"📝 Loaded {len(questions)} questions and {len(hooks)} hooks")
        
        # Create placeholder images for demonstration
        print("🖼️  Creating placeholder images...")
        image_paths = create_placeholder_images(questions, "output")
        print(f"✅ Created {len(image_paths)} placeholder images")
        
        # Generate the video
        print("🎥 Generating TikTok video...")
        output_path = generator.generate_video(
            questions=questions,
            hooks=hooks,
            image_paths=image_paths,
            output_filename="example_video.mp4"
        )
        
        print(f"🎉 Video generated successfully!")
        print(f"📁 Output: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_custom_config():
    """Example with custom configuration."""
    print("\n🎬 TikTok Video Generator - Custom Config Example")
    print("=" * 50)
    
    # Create custom configuration
    custom_config = {
        "video_settings": {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "text_font_size": 100,  # Larger text
            "text_color": "yellow",  # Different color
            "text_stroke_color": "black",
            "text_stroke_width": 5
        },
        "timing_settings": {
            "question_duration": 6,  # Longer questions
            "pause_duration": 3,     # Longer pauses
            "hook_duration": 5
        },
        "voice_settings": {
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "api_key": "your_api_key_here"
        },
        "output_settings": {
            "output_dir": "custom_output",
            "output_filename": "custom_video.mp4"
        }
    }
    
    # Save custom config
    with open("custom_config.json", "w") as f:
        json.dump(custom_config, f, indent=4)
    
    print("✅ Custom configuration saved to custom_config.json")
    print("📝 You can now use: python tiktok_generator.py --config custom_config.json")

def example_batch_processing():
    """Example of batch processing multiple videos."""
    print("\n🎬 TikTok Video Generator - Batch Processing Example")
    print("=" * 50)
    
    # Different question sets
    question_sets = [
        ["Pizza or pasta?", "Summer or winter?", "Dogs or cats?"],
        ["Beach or mountains?", "Coffee or tea?", "Movies or books?"],
        ["Sweet or savory?", "Morning or night?", "City or country?"]
    ]
    
    # Different hooks
    hook_sets = [
        ["If you get more than 1 wrong, you're buying dinner!"],
        ["Score 3/3 or you owe me a coffee"],
        ["Perfect score or you're doing the dishes tonight"]
    ]
    
    print("📋 Creating multiple video configurations...")
    
    for i, (questions, hooks) in enumerate(zip(question_sets, hook_sets)):
        # Create config for this video
        config = {
            "video_settings": {
                "width": 1080,
                "height": 1920,
                "fps": 30,
                "text_font_size": 80,
                "text_color": "white",
                "text_stroke_color": "black",
                "text_stroke_width": 3
            },
            "timing_settings": {
                "question_duration": 5,
                "pause_duration": 2,
                "hook_duration": 4
            },
            "voice_settings": {
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "api_key": "your_api_key_here"
            },
            "output_settings": {
                "output_dir": "batch_output",
                "output_filename": f"batch_video_{i+1}.mp4"
            }
        }
        
        # Save config
        config_file = f"batch_config_{i+1}.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        
        # Save questions and hooks
        with open(f"batch_questions_{i+1}.json", "w") as f:
            json.dump(questions, f, indent=4)
        
        with open(f"batch_hooks_{i+1}.json", "w") as f:
            json.dump(hooks, f, indent=4)
        
        print(f"✅ Created configuration {i+1}: {config_file}")
    
    print("\n📝 To generate all videos, run:")
    for i in range(len(question_sets)):
        print(f"   python tiktok_generator.py --config batch_config_{i+1}.json")

def main():
    """Run all examples."""
    print("🚀 TikTok Video Generator Examples")
    print("=" * 50)
    
    # Note: These examples require a valid ElevenLabs API key
    print("⚠️  Note: Update the API key in the examples before running")
    print()
    
    example_basic_usage()
    example_custom_config()
    example_batch_processing()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Get your ElevenLabs API key from https://elevenlabs.io")
    print("2. Update the API key in the examples")
    print("3. Run: python example_usage.py")
    print("4. Or use the GUI: python tiktok_gui.py")

if __name__ == "__main__":
    main()
