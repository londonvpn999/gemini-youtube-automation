def generate_visuals(output_dir, video_type, slide_content=None, thumbnail_title=None, slide_number=0, total_slides=1):
    W, H = (1080, 1920)
    
    video_path = fetch_pexels_video(slide_content.get("title", "horror") if slide_content else "horror")
    
    if video_path:
        try:
            bg = VideoFileClip(video_path).subclip(0, 60)
            bg = bg.resize(height=H)
            if bg.w < W:
                bg = bg.resize(width=W)
            bg = bg.crop(x_center=bg.w/2, y_center=bg.h/2, width=W, height=H)
        except Exception as e:
            print(f"Video clip error: {e}")
            bg = ImageClip("assets/black_screen.png").set_duration(60).resize((W, H))
    else:
        bg = ImageClip("assets/black_screen.png").set_duration(60).resize((W, H))

    txt_clip = ImageClip("assets/black_screen.png").set_duration(bg.duration)
    
    final_video = CompositeVideoClip([bg, txt_clip])
    return final_video

def main():
    print("🚀 Starting Autonomous Horror Video Generator")
    OUTPUT_DIR = Path("output")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("📝 Generating Script...")
    plan = generate_curriculum()
    lesson = plan['lessons'][0]
    
    print("🎬 Rendering Video...")
    video = generate_visuals(OUTPUT_DIR, "short", slide_content=lesson)
    
    video_path = OUTPUT_DIR / "final_horror_video.mp4"
    video.write_videofile(str(video_path), fps=24, codec="libx264", audio=False)
    
    print("✅ Video generated!")
    
    plan['lessons'][0]['status'] = 'complete'
    with open('content_plan.json', 'w') as f:
        json.dump(plan, f)

if name == "main":
    main()
