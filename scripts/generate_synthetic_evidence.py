import os
import struct
from PIL import Image
from PIL import ImageDraw, ImageFont

def generate_synthetic_data(output_dir="./data/synthetic"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating synthetic, non-sensitive investigation evidence in '{output_dir}'...")

    # 1. Benign Synthetic Chat Log
    chat_content = """[2026-08-10 14:00:12] @CyberHawk: Are you ready for the sync?
[2026-08-10 14:00:45] @NightOwl: Yes, I am at the meeting location. Contact me on +1-555-0199 or email alpha@fictional-domain.test.
[2026-08-10 14:01:20] @CyberHawk: Sending the file now. Confirm receipt at 192.168.1.105.
[2026-08-10 14:02:00] @NightOwl: Received. Payment routed to wallet 0x71C7656EC7ab88b098defB751B7401B5f6d8976F.
"""
    chat_file_path = os.path.join(output_dir, "synthetic_chat_log.txt")
    with open(chat_file_path, "w", encoding="utf-8") as f:
        f.write(chat_content)
    print(f"-> Created synthetic chat log: {chat_file_path}")

    # 2. Benign Synthetic Image with EXIF & OCR Text
    img = Image.new("RGB", (600, 400), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)
    
    # Draw fictional evidence banner
    draw.rectangle([20, 20, 580, 80], fill=(15, 23, 42))
    draw.text((40, 40), "ARGUS DEMO EVIDENCE - SYNTHETIC EXIF IMAGE", fill=(255, 255, 255))
    draw.text((40, 120), "TARGET HANDLE: @CyberHawk", fill=(56, 189, 248))
    draw.text((40, 160), "LOCATION: SAN FRANCISCO DOCK 14", fill=(74, 222, 128))
    draw.text((40, 200), "DEVICE ID: SPH-9000-SYNTHETIC", fill=(251, 146, 60))
    draw.text((40, 280), "CONFIDENTIAL INVESTIGATION DEMO ONLY", fill=(244, 63, 94))

    img_file_path = os.path.join(output_dir, "synthetic_evidence_photo.jpg")
    img.save(img_file_path, "JPEG")
    print(f"-> Created synthetic image: {img_file_path}")

    # 3. Benign Document
    doc_content = """OFFICIAL SYNTHETIC CASE MEMORANDUM
Case Reference: ARGUS-2026-0891
Subject: Cyber Investigation Support Proof-of-Concept

Summary of Synthetic Findings:
- Associated Email: suspect_lead@fictional-intel.org
- Target IP Address: 10.0.4.12
- Verified Handle: @CyberHawk
- Alternate Contact: +1-555-0144
"""
    doc_file_path = os.path.join(output_dir, "synthetic_memo.txt")
    with open(doc_file_path, "w", encoding="utf-8") as f:
        f.write(doc_content)
    print(f"-> Created synthetic memo document: {doc_file_path}")

    print("Synthetic evidence generation complete.")

if __name__ == "__main__":
    generate_synthetic_data()
