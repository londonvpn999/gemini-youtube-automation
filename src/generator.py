Each lesson object must have these keys: "chapter" (set to "Horror"), "part" (set to "1"), "title" (THIS MUST BE THE HORROR STORY TEXT), "status" (set to "pending"), and "youtube_id" (set to null).
"""
        
        response_text = call_groq(prompt)
        json_string = response_text.strip().replace(chr(96)*3 + "json", "").replace(chr(96)*3, "")
        curriculum = json.loads(json_string)
        print("✅ New curriculum generated successfully!")
        return curriculum
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to generate curriculum. {e}")
        raise

def generate_lesson_content(lesson_title):
    print(f"📝 Generating content for lesson: '{lesson_title}'...")
    try:
        prompt = f"""
You are a master horror storyteller.
The topic is '{lesson_title}'.
Write a terrifying, spine-chilling horror story based on this topic. Do not mention AI or education.

Generate a JSON response with three keys:
1. "long_form_slides": A list of 1 to 2 slide objects. Each object needs a "title" (e.g., "The Encounter") and "content" (The actual terrifying story text).
2. "short_form_highlight": A single, punchy, 1-2 sentence summary for a YouTube Short.
3. "hashtags": A string of 5-7 relevant space-separated hashtags (e.g., "#HorrorStory #Scary #Mystery #Creepy #Shorts").

Return only valid JSON.
"""
        response_text = call_groq(prompt)
        json_string = response_text.strip().replace(chr(96)*3 + "json", "").replace(chr(96)*3, "")
        content = json.loads(json_string)
        print("✅ Lesson content generated successfully.")
        return content
    except Exception as e:
        print(f"❌ ERROR: Failed to generate lesson content: {e}")
        raise

def generate_visuals(output_dir, video_type, slide_content=None, thumbnail_title=None, slide_number=0, total_slides=1):
    W, H = 1080, 1920
    story_text = slide_content.get("content", "A scary story") if slide_content else "A scary story"
    
    print("🎙️ Generating Audio...")
    try:
        tts = gTTS(text=story_text, lang='en', slow=False)
        audio_path = "temp_audio.mp3"
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
    except Exception as e:
        print(f"TTS error: {e}")
        audio_clip = None
        duration = 15 

    print("🎬 Fetching Background Video...")
    video_path = fetch_pexels_video("horror dark")
    
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
