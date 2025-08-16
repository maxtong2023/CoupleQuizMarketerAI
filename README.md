# TikTok Quiz Video Generator

A comprehensive Python tool for automatically generating TikTok-style quiz videos with text-to-speech, image processing, and professional video composition.

## Features

A quick couple quiz generator using Elevenlabs api calls, numpy, pillow, moviepy etc. For automating the tikTok process. Make sure that you have Python 3.11 from the official python website and not via homebrew. 

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd "AI Marketer On Steroids"

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your API Key

Edit `config.json` and replace the ElevenLabs API key with your own:

```json
{
    "voice_settings": {
        "api_key": "your_elevenlabs_api_key_here"
    }
}
```

**Get your API key**: Sign up at [ElevenLabs](https://elevenlabs.io) (10 minutes free per month, $11/month for 100 minutes)

### 3. Add Your Content

**Questions** (`questions.json`):
```json
[
    "Steak or sushi?",
    "Beach or mountains?",
    "Coffee or tea?"
]
```

**Hooks** (`hooks.json`):
```json
[
    "If your partner gets more than 2 wrong, they owe you a cute $100 bill",
    "If your partner gets more than 2 wrong, they have to get your name tattooed on their forehead"
]
```

### 4. Generate Your Video

**Option A: GUI (Recommended for beginners)**
```bash
python tiktok_gui.py
```

**Option B: Command Line**
```bash
# Generate with placeholder images
python tiktok_generator.py --create-placeholders

# Generate with your own images
python tiktok_generator.py --images image1.jpg image2.jpg image3.jpg

# Add clock sound effect
python tiktok_generator.py --create-placeholders --clock-audio clock.mp3
```

## How It Works

### 1. **Image Processing**
- Automatically resizes images to fit TikTok's 1080×1920 format
- Maintains aspect ratio while adding black padding if needed
- Supports JPG, PNG, BMP, and GIF formats

### 2. **Text-to-Speech Generation**
- Converts each question and hook to high-quality audio
- Uses ElevenLabs' advanced voice synthesis
- Automatically syncs audio duration with video clips

### 3. **Video Composition**
- Creates individual clips for each question with image + text overlay
- Adds professional fade effects and text styling
- Inserts pause clips between questions for dramatic effect
- Concatenates everything into a single TikTok-ready video

### 4. **Output**
- Generates MP4 video in TikTok's optimal format
- Includes all audio, images, and text overlays
- Ready to upload directly to TikTok

## Configuration Options

Edit `config.json` to customize:

```json
{
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
        "api_key": "your_api_key"
    }
}
```

## Advanced Usage

### Custom Voice Selection

ElevenLabs offers many voices. To change voices:

1. Visit [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
2. Choose a voice and copy its ID
3. Update `voice_id` in `config.json`

### Adding Clock Sound Effects

1. Download a short clock/ticking sound (MP3, WAV, etc.)
2. Use the `--clock-audio` parameter or select in GUI
3. The sound will play during pause clips between questions

### Batch Processing

For multiple videos, create different JSON files:

```bash
# Generate multiple videos
python tiktok_generator.py --config config1.json --output video1.mp4
python tiktok_generator.py --config config2.json --output video2.mp4
```

## File Structure

```
AI Marketer On Steroids/
├── main.py                 # Basic script (legacy)
├── tiktok_generator.py    # Main command-line tool
├── tiktok_gui.py         # GUI interface
├── config.json            # Configuration settings
├── questions.json         # Quiz questions
├── hooks.json            # Video hooks/intros
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── output/               # Generated videos and audio
```

## Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg: `brew install ffmpeg` (Mac) or download from [ffmpeg.org](https://ffmpeg.org)

**"ElevenLabs API error"**
- Check your API key in `config.json`
- Verify you have sufficient credits in your ElevenLabs account

**"Image processing error"**
- Ensure images are valid image files (JPG, PNG, etc.)
- Check file permissions

**"Video generation fails"**
- Ensure you have enough disk space
- Check the log file (`tiktok_generator.log`) for detailed error messages

### Performance Tips

- **Image size**: Use images around 1080×1920 for best performance
- **Audio length**: Keep questions concise (5-10 seconds each)
- **Batch processing**: Generate multiple videos during off-peak hours

## Cost Analysis

**Free Tier (ElevenLabs)**: 10 minutes/month
- Perfect for testing and small projects
- ~20-30 short quiz videos per month

**Paid Plans**:
- **$11/month**: 100 minutes (100-300 videos)
- **$22/month**: 250 minutes (250-750 videos)
- **$99/month**: 1000 minutes (1000-3000 videos)

**Other Costs**: $0 (all other tools are free/open-source)

## Alternatives

If you prefer not to use ElevenLabs:

- **Google gTTS**: Free but lower quality
- **Amazon Polly**: Pay-per-use, high quality
- **Azure Speech**: Microsoft's TTS service

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the tool!

## License

This project is open source. Use it for personal or commercial projects.

---

**Ready to create viral TikTok quiz videos?** 🚀

Start with the GUI version (`python tiktok_gui.py`) for the easiest experience, or dive into the command-line tool for automation and scripting.
