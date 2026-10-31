import os
import json
import requests
import textwrap
import numpy as np
from io import BytesIO
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# --- API Keys ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def call_groq(prompt_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq Error: {response.text}")

def fetch_pexels_video(query):
    if not PEXELS_API_KEY: 
        return None
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": "scary dark horror", "per_page": 1, "orientation": "portrait"}
    try:
        response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        data = response.json()
        if data.get('videos'):
            video_url = max(data['videos'][0]['video_files'], key=lambda x: x['width'])['link']
            video_response = requests.get(video_url, timeout=30)
            video_path = "temp_bg_video.mp4"
            with open(video_path, "wb") as f:
                f.write(video_response.content)
            return video_path
    except Exception as e:
        print(f"Video fetch error: {e}")
    return None

def text_to_speech(text, output_path="temp_audio.mp3", lang='en'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def generate_curriculum(previous_titles=None):
    print("🔍 Generating horror story...")
    prompt = "Write a short, scary horror story under 40 seconds. Respond ONLY with a valid JSON object. Key 'lessons' which is a list of 1 lesson object. Keys inside lesson: 'chapter' ('Horror'), 'part' ('1'), 'title' (THE HORROR STORY TEXT), 'status' ('pending'), 'youtube_id' (null)."
    
    try:
        response_text = call_groq(prompt)
        json_string = response_text.strip().replace(chr(96)*3 + "json", "").replace(chr(96)*3, "")
        return json.loads(json_string)
    except Exception as e:
        print(f"Groq/JSON Error: {e}")
        return {"lessons": [{"chapter": "Horror", "part": "1", "title": "I woke up to a scratching sound inside my closet. When I opened it, there was nothing there, but the scratching was now coming from inside my walls...", "status": "pending", "youtube_id": None}]}

def generate_lesson_content(lesson_title):
    return {
        "long_form_slides": [{"title": "Horror", "content": lesson_title}],
        "short_form_highlight": lesson_title[:50],
        "hashtags": "#horror #scary #shorts"
    }

def generate_visuals(output_dir, video_type, slide_content=None, thumbnail_title=None, slide_number=0, total_slides=1):
    W, H = 1080, 1920
    story_text = slide_content.get("title", "A scary story") if slide_content else "A scary story"
    
    print("🎙️ Generating Audio...")
    audio_path = text_to_speech(story_text)
    if audio_path:
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
    else:
        audio_clip = None
        duration = 15

    print("🎬 Fetching Background Video...")
    video_path = fetch_pexels_video("horror")
    
    if video_path:
        try:
            bg = VideoFileClip(video_path)
            if bg.duration < duration:
                bg = bg.loop(duration=duration)
            else:
                bg = bg.subclip(0, duration)
            
            bg = bg.resize(height=H)
            if bg.w > W:
                bg = bg.crop(x_center=bg.w/2, width=W)
            elif bg.w < W:
                bg = bg.resize(width=W)
                bg = bg.crop(y_center=bg.h/2, height=H)
            bg = bg.set_duration(duration)
        except Exception as e:
            print(f"Video error: {e}")
            bg = ImageClip(np.zeros((H, W, 3), dtype=np.uint8), duration=duration)
    else:
        bg = ImageClip(np.zeros((H, W, 3), dtype=np.uint8), duration=duration)

    print("📝 Adding Text Overlay...")
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 70)
    except:
        font = ImageFont.load_default()

    wrapped_text = textwrap.fill(story_text, width=25)
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (W - text_w) / 2
    y = (H - text_h) / 2
    
    draw.text((x, y), wrapped_text, font=font, fill="white", stroke_width=3, stroke_fill="black")
    
    txt_clip = ImageClip(np.array(img), duration=duration)
    final_video = CompositeVideoClip([bg, txt_clip])
    
    if audio_clip:
        final_video = final_video.set_audio(audio_clip)
    
    return final_video

def main():
    print("🚀 Starting Horror Video Generation")
    OUTPUT_DIR = Path("output")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    plan = generate_curriculum()
    lesson = plan['lessons'][0]
    
    video = generate_visuals(OUTPUT_DIR, "short", slide_content=lesson)
    video_path = OUTPUT_DIR / "final_horror_video.mp4"
    
    video.write_videofile(str(video_path), fps=24, codec="libx264", audio_codec="aac")
    
    plan['lessons'][0]['status'] = 'complete'
    with open('content_plan.json', 'w') as f:
        json.dump(plan, f)

if __name__ == "__main__":
    main()
