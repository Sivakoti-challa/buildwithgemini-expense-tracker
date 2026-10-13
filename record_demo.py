import time
import os
import subprocess
from playwright.sync_api import sync_playwright

output_dir = "/config/Desktop/BuildWithGemini/recordings"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 760},
        record_video_dir=output_dir,
        record_video_size={"width": 1280, "height": 760}
    )
    page = context.new_page()
    
    print("Navigating to http://localhost:8080...")
    page.goto("http://localhost:8080")
    page.wait_for_load_state("networkidle")
    time.sleep(2.0)
    
    # 1. Showcase Theme Toggle (Light -> Dark -> Light)
    print("Demonstrating dark mode...")
    page.click("#theme-btn")
    time.sleep(1.5)
    page.click("#theme-btn")
    time.sleep(1.0)
    
    # 2. Click Groceries prompt chip
    print("Querying groceries via prompt chip...")
    # Find button containing Groceries
    groceries_btn = page.locator("button.prompt-chip:has-text('Groceries')")
    groceries_btn.click()
    
    # Wait for response card
    page.wait_for_selector(".a2card", timeout=45000)
    time.sleep(3.5)
    
    # 3. Log a new expense via Modal
    print("Opening Quick Log Expense modal...")
    page.click("button.btn-quick-add")
    time.sleep(1.0)
    
    page.fill("#modal-amount", "18.50")
    time.sleep(0.5)
    page.fill("#modal-merchant", "Blue Bottle Coffee")
    time.sleep(0.5)
    page.select_option("#modal-category", "Dining")
    time.sleep(0.5)
    page.select_option("#modal-payment", "Credit Card")
    time.sleep(0.8)
    
    print("Saving expense...")
    page.click("button.btn-primary:has-text('Save Expense')")
    
    # Wait for the agent to reply
    time.sleep(6.0)
    
    # 4. Check Budget Status
    print("Checking budget status...")
    budget_btn = page.locator("button.prompt-chip:has-text('Budget Status')")
    budget_btn.click()
    time.sleep(6.0)
    
    # Smooth scroll to bottom
    page.evaluate("document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight")
    time.sleep(3.0)
    
    video_path = page.video.path()
    context.close()
    browser.close()
    print("Recorded raw video at:", video_path)

# Mux with upbeat lo-fi track using ffmpeg
final_mp4 = "/config/Desktop/BuildWithGemini/expense_tracker_demo.mp4"
lofi_audio = "/config/Desktop/BuildWithGemini/lofi_track.wav"

cmd = [
    "ffmpeg", "-y",
    "-i", video_path,
    "-stream_loop", "-1", "-i", lofi_audio,
    "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    final_mp4
]
print("Muxing video with audio...")
subprocess.run(cmd, check=True)
print("Finished demo video:", final_mp4)
