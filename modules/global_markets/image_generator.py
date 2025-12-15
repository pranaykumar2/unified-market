import os
import logging
import re
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

# Configuration - Increased dimensions for better visibility with larger fonts
IMAGE_WIDTH = 1200
ROW_HEIGHT = 60       # Was 55, increased to 60 for larger font
HEADER_HEIGHT = 80    # Was 70, increased to 80 for larger font
TITLE_HEIGHT = 100    # Was 90, increased to 100 for larger font
MARGIN = 25
FOOTER_HEIGHT = 45    # Was 40, increased to 45 for larger font

# Colors - Vibrant theme
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# Title backgrounds - Vibrant colors for each section
MAJOR_INDICES_BG = (0, 150, 136)  # Teal #(255, 87, 34)  # Vibrant Orange
INDIAN_INDICES_BG = (0, 150, 136)  # Teal ##(255, 152, 0)  # Bright Amber
COMMODITIES_BG = (0, 150, 136)  # Teal ##(156, 39, 176)  # Rich Purple
CURRENCIES_BG = (0, 150, 136)  # Teal
# Column header - Dark contrast
COLUMN_HEADER_BG = (33, 33, 33)  # Near black
# Data rows
ALT_ROW_BG = (250, 250, 252)  # Very light blue-gray
# Value colors
GREEN = (46, 125, 50)  # Material Green
RED = (211, 47, 47)  # Material Red
BORDER_COLOR = (100, 100, 100)  # Darker gray for better visibility
TABLE_BORDER_COLOR = (33, 33, 33)  # Dark border for outer table

# Font sizes - Further increased for better and clean visibility
TITLE_FONT_SIZE = 50        # Was 36, now +4
COLUMN_HEADER_FONT_SIZE = 30  # Was 20, now +4
DATA_FONT_SIZE = 28         # Was 18, now +4
FOOTER_FONT_SIZE = 16       # Was 14, now +2


def download_google_font(font_family, style):
    """Download Google Font from CDN and cache it locally."""
    if not font_family:
        return None
    
    # Use centralized fonts directory
    cache_dir = Path(settings.FONTS_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Map style to Google Fonts parameters
    if style == 'bold':
        weight = '700'
        italic = ''
    elif style == 'italic':
        weight = '400'
        italic = 'ital,'
    else:  # normal
        weight = '400'
        italic = ''
    
    # Check if font is already cached
    font_filename = f"{font_family.replace(' ', '')}-{style}.ttf"
    font_path = cache_dir / font_filename
    
    if font_path.exists():
        logger.debug(f"Using cached font: {font_family} ({style})")
        return str(font_path)
    
    # Download from Google Fonts CDN
    try:
        logger.info(f"⬇️ Downloading font: {font_family} ({style})...")
        
        # Request font CSS with proper User-Agent
        font_name_encoded = font_family.replace(' ', '+')
        
        if italic:
            api_url = f"https://fonts.googleapis.com/css2?family={font_name_encoded}:ital,wght@1,{weight}&display=swap"
        else:
            api_url = f"https://fonts.googleapis.com/css2?family={font_name_encoded}:wght@{weight}&display=swap"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse CSS to find font file URL
        font_urls = re.findall(r'src:\s*url\(([^)]+)\)', response.text)
        
        if font_urls:
            font_url = font_urls[0].strip()
            
            font_response = requests.get(font_url, timeout=15)
            font_response.raise_for_status()
            
            with open(font_path, 'wb') as f:
                f.write(font_response.content)
            
            logger.info(f"✅ Font downloaded: {font_path}")
            return str(font_path)
        else:
            logger.warning(f"⚠️ No font URL found in CSS for {font_family}")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not download Google Font {font_family} ({style}): {e}")
    
    return None


def ensure_fonts_downloaded():
    """Pre-download required fonts at startup to avoid delays during image generation."""
    logger.info("📥 Ensuring required fonts are available...")
    fonts_needed = [
        ('Roboto', 'normal'),
        ('Roboto', 'bold')
    ]
    
    downloaded = 0
    cached = 0
    failed = 0
    
    for font_family, style in fonts_needed:
        cache_dir = Path(settings.FONTS_DIR)
        font_filename = f"{font_family.replace(' ', '')}-{style}.ttf"
        font_path = cache_dir / font_filename
        
        if font_path.exists():
            cached += 1
        else:
            result = download_google_font(font_family, style)
            if result:
                downloaded += 1
            else:
                failed += 1
    
    logger.info(f"✅ Font check complete: {cached} cached, {downloaded} downloaded, {failed} failed")
    return True


def get_font(size, bold=False):
    """Get font with fallback options, with auto-download from Google Fonts."""
    font_options = []
    
    # Check centralized fonts directory first
    fonts_dir = Path(settings.FONTS_DIR)
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Try to download from Google Fonts if not already cached
    style = 'bold' if bold else 'normal'
    google_font_path = download_google_font('Roboto', style)
    if google_font_path:
        font_options.append(google_font_path)
    
    # 2. Look for existing Roboto fonts (downloaded by capital_market or manually added)
    if bold:
        font_options.append(str(fonts_dir / 'Roboto-bold.ttf'))
        font_options.append(str(fonts_dir / 'Roboto-Bold.ttf'))
        font_options.append(str(fonts_dir / 'arialbd.ttf'))
    else:
        font_options.append(str(fonts_dir / 'Roboto-normal.ttf'))
        font_options.append(str(fonts_dir / 'Roboto-Regular.ttf'))
        font_options.append(str(fonts_dir / 'arial.ttf'))

    # 3. System font options as final fallback
    if bold:
        font_options.extend([
            'arialbd.ttf',  # Windows Arial Bold
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Termux
            'DejaVuSans-Bold.ttf',
        ])
    else:
        font_options.extend([
            'arial.ttf',  # Windows Arial
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Termux
            'DejaVuSans.ttf',
        ])
    
    # Try each font option
    for font_path in font_options:
        try:
            font = ImageFont.truetype(font_path, size)
            logger.debug(f"Loaded font: {font_path} (size: {size})")
            return font
        except Exception as e:
            continue
    
    # Final fallback - but log a warning
    logger.warning(f"⚠️ Could not load any TrueType fonts, falling back to default font (size: {size})")
    return ImageFont.load_default()



def safe_float(value):
    """Convert string with commas to float."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.replace(",", ""))
        return 0.0
    except:
        return 0.0


def format_number(value, decimal_places=2):
    """Format number with specific decimal places."""
    try:
        num = safe_float(value)
        if abs(num) >= 1000:
            # For large numbers, use comma separators
            return f"{num:,.{decimal_places}f}"
        else:
            return f"{num:.{decimal_places}f}"
    except:
        return str(value)


def create_single_market_image(data_list, title, title_color):
    """
    Create a single market image for one category.
    
    Args:
        data_list: List of market items
        title: Title for the image
        title_color: Background color for the title
        
    Returns:
        PIL Image object
    """
    try:
        if not data_list:
            logger.warning(f"No data provided for {title}")
            return None
        
        # Calculate image height
        total_height = TITLE_HEIGHT + HEADER_HEIGHT + (len(data_list) * ROW_HEIGHT) + FOOTER_HEIGHT + MARGIN
        
        # Create image
        img = Image.new('RGB', (IMAGE_WIDTH, total_height), WHITE)
        draw = ImageDraw.Draw(img)
        
        # Fonts
        font_title = get_font(TITLE_FONT_SIZE, bold=True)
        font_header = get_font(COLUMN_HEADER_FONT_SIZE, bold=True)
        font_data = get_font(DATA_FONT_SIZE)
        font_data_bold = get_font(DATA_FONT_SIZE, bold=True)  # Bold font for NAME column
        font_footer = get_font(FOOTER_FONT_SIZE)
        
        current_y = 0
        
        # === TITLE ===
        draw.rectangle([0, current_y, IMAGE_WIDTH, current_y + TITLE_HEIGHT], fill=title_color)
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        draw.text(
            ((IMAGE_WIDTH - title_width) // 2, current_y + (TITLE_HEIGHT - title_height) // 2),
            title,
            fill=WHITE,
            font=font_title
        )
        current_y += TITLE_HEIGHT
        
        # === COLUMN HEADERS ===
        draw.rectangle([0, current_y, IMAGE_WIDTH, current_y + HEADER_HEIGHT], fill=COLUMN_HEADER_BG)
        
        # Equal column spacing - distributed evenly across width
        margin_left = 30
        margin_right = 30
        available_width = IMAGE_WIDTH - margin_left - margin_right  # 1140px
        
        # Distribute columns more evenly
        name_x = margin_left
        name_width = 280  # Reduced from 450 to make more space for other columns
        
        ltp_x = name_x + name_width + 40  # Add spacing between columns
        ltp_width = 230  # Increased from 200
        
        chg_x = ltp_x + ltp_width + 40  # Add spacing between columns
        chg_width = 220  # Increased from 180
        
        chgper_x = chg_x + chg_width + 40  # Add spacing between columns
        chgper_width = 220  # Increased from 170
        
        header_y = current_y + (HEADER_HEIGHT - 25) // 2
        
        # Draw headers with center alignment in their columns
        draw.text((name_x, header_y), 'NAME', fill=WHITE, font=font_header)
        
        # Center-align numeric headers
        ltp_header_bbox = draw.textbbox((0, 0), 'LAST PRICE', font=font_header)
        ltp_header_width = ltp_header_bbox[2] - ltp_header_bbox[0]
        draw.text((ltp_x + (ltp_width - ltp_header_width) // 2, header_y), 'LAST PRICE', fill=WHITE, font=font_header)
        
        chg_header_bbox = draw.textbbox((0, 0), 'CHANGE', font=font_header)
        chg_header_width = chg_header_bbox[2] - chg_header_bbox[0]
        draw.text((chg_x + (chg_width - chg_header_width) // 2, header_y), 'CHANGE', fill=WHITE, font=font_header)
        
        chgper_header_bbox = draw.textbbox((0, 0), 'CHANGE %', font=font_header)
        chgper_header_width = chgper_header_bbox[2] - chgper_header_bbox[0]
        draw.text((chgper_x + (chgper_width - chgper_header_width) // 2, header_y), 'CHANGE %', fill=WHITE, font=font_header)
        
        # Draw vertical separators in header section
        separator_offset = 8
        draw.line([ltp_x - separator_offset, current_y, ltp_x - separator_offset, current_y + HEADER_HEIGHT], fill=(80, 80, 80), width=3)
        draw.line([chg_x - separator_offset, current_y, chg_x - separator_offset, current_y + HEADER_HEIGHT], fill=(80, 80, 80), width=3)
        draw.line([chgper_x - separator_offset, current_y, chgper_x - separator_offset, current_y + HEADER_HEIGHT], fill=(80, 80, 80), width=3)
        
        current_y += HEADER_HEIGHT
        
        # Draw outer table border on left side (below header)
        table_start_y = current_y
        
        # === DATA ROWS ===
        for idx, item in enumerate(data_list):
            bg_color = WHITE if idx % 2 == 0 else ALT_ROW_BG
            draw.rectangle([0, current_y, IMAGE_WIDTH, current_y + ROW_HEIGHT], fill=bg_color)
            
            # Extract data
            name = str(item.get('name', '')).strip()
            ltp_raw = item.get('ltp', '')
            chg = safe_float(item.get('chg', 0))
            chgper = safe_float(item.get('chgper', 0))
            
            # Format values with proper decimal places
            ltp = format_number(ltp_raw, 2)
            chg_text = f'{chg:+.2f}'
            chgper_text = f'{chgper:+.2f}%'
            
            # Determine color for change values
            chg_color = GREEN if chg >= 0 else RED
            
            # Vertical centering for text
            text_y = current_y + (ROW_HEIGHT - 22) // 2
            
            # Draw name (left aligned with BOLD font)
            draw.text((name_x, text_y), name, fill=BLACK, font=font_data_bold)
            
            # Draw LTP (center aligned in column)
            ltp_bbox = draw.textbbox((0, 0), ltp, font=font_data)
            ltp_text_width = ltp_bbox[2] - ltp_bbox[0]
            ltp_text_x = ltp_x + (ltp_width - ltp_text_width) // 2
            draw.text((ltp_text_x, text_y), ltp, fill=BLACK, font=font_data)
            
            # Draw Change (center aligned in column)
            chg_bbox = draw.textbbox((0, 0), chg_text, font=font_data)
            chg_text_width = chg_bbox[2] - chg_bbox[0]
            chg_text_x = chg_x + (chg_width - chg_text_width) // 2
            draw.text((chg_text_x, text_y), chg_text, fill=chg_color, font=font_data)
            
            # Draw Change % (center aligned in column)
            chgper_bbox = draw.textbbox((0, 0), chgper_text, font=font_data)
            chgper_text_width = chgper_bbox[2] - chgper_bbox[0]
            chgper_text_x = chgper_x + (chgper_width - chgper_text_width) // 2
            draw.text((chgper_text_x, text_y), chgper_text, fill=chg_color, font=font_data)
            
            # Draw vertical separator lines with increased width (3px instead of 1px)
            separator_offset = 8
            draw.line([ltp_x - separator_offset, current_y, ltp_x - separator_offset, current_y + ROW_HEIGHT], fill=BORDER_COLOR, width=3)
            draw.line([chg_x - separator_offset, current_y, chg_x - separator_offset, current_y + ROW_HEIGHT], fill=BORDER_COLOR, width=3)
            draw.line([chgper_x - separator_offset, current_y, chgper_x - separator_offset, current_y + ROW_HEIGHT], fill=BORDER_COLOR, width=3)
            
            # Draw horizontal border line with increased width (3px instead of 1px)
            current_y += ROW_HEIGHT
            draw.line([0, current_y, IMAGE_WIDTH, current_y], fill=BORDER_COLOR, width=3)
        
        # Draw outer table borders (thicker borders around the entire table)
        table_end_y = current_y
        # Top border (below header)
        draw.line([0, table_start_y, IMAGE_WIDTH, table_start_y], fill=TABLE_BORDER_COLOR, width=3)
        # Bottom border
        draw.line([0, table_end_y, IMAGE_WIDTH, table_end_y], fill=TABLE_BORDER_COLOR, width=3)
        # Left border
        draw.line([0, table_start_y, 0, table_end_y], fill=TABLE_BORDER_COLOR, width=3)
        # Right border
        draw.line([IMAGE_WIDTH - 1, table_start_y, IMAGE_WIDTH - 1, table_end_y], fill=TABLE_BORDER_COLOR, width=3)
        
        # === FOOTER ===
        current_y += MARGIN // 2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        footer_text = f'Generated: {timestamp}'
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(
            ((IMAGE_WIDTH - footer_width) // 2, current_y),
            footer_text,
            fill=(150, 150, 150),
            font=font_footer
        )
        
        return img
        
    except Exception as e:
        logger.error(f'Error creating image for {title}: {e}', exc_info=True)
        return None


def create_market_images(all_data):
    """
    Create 4 separate market images for each category.
    
    Args:
        all_data: Dictionary with keys 'major_indices', 'indian_indices', 'commodities', 'currencies'
        
    Returns:
        dict: Dictionary with image paths for each category
    """
    try:
        logger.info('Creating market images...')
        
        # Ensure directory exists
        Path(settings.TEMP_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define categories with their titles, colors, and enable flags - UPDATED TITLES
        categories = [
            ('major_indices', 'GLOBAL INDICES', MAJOR_INDICES_BG, settings.ENABLE_GLOBAL_INDICES),
            ('indian_indices', 'INDIAN INDICES', INDIAN_INDICES_BG, settings.ENABLE_INDIAN_INDICES),
            ('commodities', 'GLOBAL COMMODITIES', COMMODITIES_BG, settings.ENABLE_GLOBAL_COMMODITIES),
            ('currencies', 'GLOBAL CURRENCIES', CURRENCIES_BG, settings.ENABLE_GLOBAL_CURRENCIES)
        ]
        
        image_paths = {}
        skipped = []
        
        for category_key, title, color, is_enabled in categories:
            # Check if this category is enabled
            if not is_enabled:
                logger.info(f'⏭️ Skipped: {title} (disabled in config)')
                skipped.append(title)
                continue
            
            data_list = all_data.get(category_key, [])
            
            if not data_list:
                logger.warning(f'⚠️ No data for {title}, skipping...')
                skipped.append(title)
                continue
            
            # Create image
            img = create_single_market_image(data_list, title, color)
            
            if img:
                # Save image
                image_filename = f'market_{category_key}_{timestamp}.png'
                image_path = os.path.join(settings.TEMP_IMAGES_DIR, image_filename)
                img.save(image_path, 'PNG', quality=95)
                image_paths[category_key] = image_path
                logger.info(f'✅ Created: {title} -> {image_filename}')
            else:
                logger.error(f'❌ Failed to create image for {title}')
                skipped.append(title)
        
        if skipped:
            logger.info(f'Skipped {len(skipped)} categories: {", ".join(skipped)}')
        logger.info(f'Successfully created {len(image_paths)} images')
        return image_paths
        
    except Exception as e:
        logger.error(f'Error creating market images: {e}', exc_info=True)
        return {}


# Keep the old function for backward compatibility (deprecated)
def create_market_image(all_data):
    """
    DEPRECATED: Creates a single combined image.
    Use create_market_images() instead for separate images.
    """
    logger.warning('create_market_image() is deprecated. Use create_market_images() for separate images.')
    
    # Call new function and return first image path for compatibility
    image_paths = create_market_images(all_data)
    if image_paths:
        return list(image_paths.values())[0]
    return None
