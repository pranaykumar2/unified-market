import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Bot
from telegram.error import TelegramError
from config.settings import settings
from .data_fetcher import fetch_all_market_data, ensure_data_directories
from .image_generator import create_market_images, ensure_fonts_downloaded

logger = logging.getLogger(__name__)

# Create a dedicated executor for CPU-intensive image generation
image_executor = ThreadPoolExecutor(max_workers=4)

# Pre-download fonts at module initialization
try:
    ensure_fonts_downloaded()
except Exception as e:
    logger.warning(f"Could not pre-download fonts: {e}")


async def send_global_markets_update(bot: Bot) -> bool:
    try:
        logger.info("=" * 70)
        logger.info("STARTING Global Markets Update")
        logger.info("=" * 70)

        ensure_data_directories()
        
        # 1. Non-blocking async data fetch (concurrent API calls)
        all_data = await fetch_all_market_data()

        total_items = sum(len(v) for v in all_data.values())
        if total_items == 0:
            logger.error("FAILED: No market data received from any API")
            return False

        logger.info(f"DATA SUMMARY:")
        logger.info(f"   Major Indices: {len(all_data['major_indices'])} items")
        logger.info(f"   Indian Indices: {len(all_data['indian_indices'])} items")
        logger.info(f"   Commodities: {len(all_data['commodities'])} items")
        logger.info(f"   Currencies: {len(all_data['currencies'])} items")
        logger.info(f"   Total: {total_items} items")

        logger.info("")
        logger.info("Generating 4 separate market images...")
        
        # 2. Non-blocking image generation (offload to thread pool)
        loop = asyncio.get_running_loop()
        image_paths = await loop.run_in_executor(
            image_executor,
            create_market_images,
            all_data
        )

        if not image_paths:
            logger.error("FAILED: Could not generate any market images")
            return False

        logger.info(f"SUCCESS: Generated {len(image_paths)} images")

        logger.info("")
        logger.info("Sending images to Telegram channel...")

        # Send each image separately
        sent_count = 0
        categories_map = {
            'major_indices': 'Global Indices',
            'indian_indices': 'Indian Indices',
            'commodities': 'Global Commodities',
            'currencies': 'Global Currencies'
        }

        for category_key, image_path in image_paths.items():
            try:
                category_name = categories_map.get(category_key, category_key)
                logger.info(f"{category_name}")
                
                with open(image_path, "rb") as image_file:
                    message = await bot.send_photo(
                        chat_id=settings.TELEGRAM_CHAT_ID,
                        photo=image_file,
                        caption=f"📊 {category_name}"
                    )
                
                logger.sent(f"   ╰──> ✅ Sent: {category_name}")
                sent_count += 1
                
                # Clean up the image file
                try:
                    os.remove(image_path)
                    logger.info(f"   Cleaned up: {os.path.basename(image_path)}")
                except Exception as e:
                    logger.warning(f"   WARNING: Failed to delete {image_path}: {e}")
                
            except TelegramError as e:
                logger.error(f"❌ Failed to send {category_name}: {e}")
            except Exception as e:
                logger.error(f"❌ Error processing {category_name}: {e}", exc_info=True)

        if sent_count > 0:
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"Global Markets update completed! ({sent_count}/{len(image_paths)} images sent)")
            logger.info("=" * 70)
            return True
        else:
            logger.error("FAILED: No images were sent successfully")
            return False

    except TelegramError as e:
        logger.error(f"TELEGRAM ERROR: {e}")
        return False
    except Exception as e:
        logger.error(f"CRITICAL ERROR in send_global_markets_update: {e}", exc_info=True)
        return False
