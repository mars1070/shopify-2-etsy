#!/usr/bin/env python3
"""
Test script to verify Gemini prompts are working correctly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from gemini_enhancer import GeminiEnhancer
import json

def test_prompts():
    # Load API key from settings
    settings_file = os.path.abspath('settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            api_key = settings.get('gemini_api_key')
    else:
        print("❌ Settings file not found")
        return
    
    if not api_key:
        print("❌ No API key found in settings")
        return
    
    print("✅ API key loaded successfully")
    
    # Initialize enhancer
    enhancer = GeminiEnhancer(api_key)
    
    # Test with a sample image URL (using a real product image from CSV)
    test_image_url = "https://cdn.shopify.com/s/files/1/1006/1296/4701/files/Designsanstitre_32.png?v=1762878146"
    
    print(f"🔄 Testing with image: {test_image_url}")
    
    # Download and process image
    image_bytes = enhancer.download_image_as_base64(test_image_url)
    
    if not image_bytes:
        print("❌ Failed to download image")
        return
    
    print("✅ Image downloaded successfully")
    
    # Generate content
    print("🔄 Generating content with Gemini...")
    result = enhancer.generate_product_content(image_bytes)
    
    if not result:
        print("❌ Failed to generate content")
        return
    
    print("✅ Content generated successfully!")
    print("\n" + "="*60)
    print("GENERATED TITLE:")
    print(result['title'])
    print("\nGENERATED DESCRIPTION:")
    print(result['description'])
    print("\nGENERATED TAGS:")
    print(result['tags'])
    print("="*60)
    
    # Verify format compliance
    print("\n🔍 FORMAT VERIFICATION:")
    
    # Check title format (2-3 phrases separated by " | ")
    title_parts = result['title'].split(' | ')
    print(f"✅ Title has {len(title_parts)} phrases (expected 2-3)")
    
    # Check tags format (13 tags, comma-separated, no spaces)
    tags_list = result['tags'].split(',')
    print(f"✅ Tags count: {len(tags_list)} (expected 13)")
    print(f"✅ Tags format: {'✓' if ', ' not in result['tags'] else '✗ (has spaces after commas)'}")
    print(f"✅ Tags lowercase: {'✓' if result['tags'].islower() else '✗'}")
    
    # Check description structure
    has_features = "✨ Features" in result['description']
    has_faq = "❓ FAQ" in result['description']
    no_bold = "**" not in result['description']
    
    print(f"✅ Description has Features section: {'✓' if has_features else '✗'}")
    print(f"✅ Description has FAQ section: {'✓' if has_faq else '✗'}")
    print(f"✅ Description has no bold text: {'✓' if no_bold else '✗'}")

if __name__ == "__main__":
    test_prompts()
