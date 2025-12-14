"""
Test the new clean logging format
"""
from config.logger_config import setup_logger

# Create logger
logger = setup_logger("TestLog", "INFO")

# Test different log levels
logger.info("Startup complete - switching to live monitoring")
logger.feed("Scan Complete. Scanner sleeping 💤5m. Next: 15:19:02")
logger.info("After a tough 2025, are Nifty bulls ready for...")
logger.sent("   ╰──> ✅ Sent: After a tough 2025, are Nifty")
logger.info("FPIs withdraw INR 17,955 cr from Indian equit...")
logger.sent("   ╰──> ✅ Sent: FPIs withdraw INR 17,955 cr")

print("\n" + "="*60)
print("✅ New logging format test complete!")
print("="*60)
