import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

output_dir = Path("sample_manuscripts")
output_dir.mkdir(parents=True, exist_ok=True)

def create_manuscript_image(text_lines, filename, title="ANCIENT INSCRIPTION"):
    width, height = 900, 480
    # Create antique parchment parchment background color
    img = Image.new("RGB", (width, height), color=(243, 230, 206))
    draw = ImageDraw.Draw(img)

    # Draw border simulating ancient stone/parchment frame
    draw.rectangle([15, 15, width - 15, height - 15], outline=(150, 110, 70), width=4)
    draw.rectangle([25, 25, width - 25, height - 25], outline=(180, 140, 95), width=2)

    # Add header
    draw.text((45, 40), f"✦ {title} ✦", fill=(120, 80, 40))

    # Try default font or system font
    y_offset = 120
    for line in text_lines:
        draw.text((60, y_offset), line, fill=(45, 30, 15))
        y_offset += 65

    # Seal at bottom
    draw.ellipse([width - 140, height - 110, width - 50, height - 30], outline=(160, 60, 50), width=3)
    draw.text((width - 125, height - 80), "SEAL", fill=(160, 60, 50))

    output_path = output_dir / filename
    img.save(str(output_path))
    print(f"Created manuscript image: {output_path.resolve()}")
    return str(output_path.resolve())

if __name__ == "__main__":
    # 1. Sanskrit Shanti Mantra Manuscript
    create_manuscript_image(
        text_lines=[
            "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः ।",
            "सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥",
            "ॐ शान्तिः शान्तिः शान्तिः ॥"
        ],
        filename="shanti_mantra_manuscript.png",
        title="TAITTIRIYA UPANISHAD MANUSCRIPT - C. 500 BCE"
    )

    # 2. Ashoka Rock Edict Fragment
    create_manuscript_image(
        text_lines=[
            "देवानंपिये पियदसि राजा हेवं आहा ।",
            "सत्यं वदेत धर्मं चरेत स्वाध्यायान्मा प्रमदः ।",
            "धम्म विजयो च मुखमतो ॥"
        ],
        filename="ashoka_rock_edict.png",
        title="EMPEROR ASHOKA MAJOR ROCK EDICT - SARNATH"
    )
