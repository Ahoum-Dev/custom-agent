"""
Call management script for initiating outbound calls to facilitators
"""
import asyncio
import logging
import os
from datetime import datetime
from csv_manager import CSVManager
from telephony_service import TelephonyService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self):
        self.csv_manager = CSVManager()
        self.telephony_service = TelephonyService()
        self.max_calls_per_session = int(os.getenv("MAX_CALLS_PER_SESSION", "10"))
        self.call_interval_seconds = int(os.getenv("CALL_INTERVAL_SECONDS", "120"))  # 2 minutes between calls
        
    async def start_calling_session(self):
        """Main method to start calling facilitators"""
        logger.info("=== Starting Outbound Calling Session ===")
        
        # Initialize database
        try:
            from database import db_manager
            await db_manager.create_tables()
            logger.info("Database tables ready")
        except ImportError:
            logger.warning("Database module not available - calls will be tracked only in CSV")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
        
        # Get statistics before starting
        stats = self.csv_manager.get_stats()
        logger.info(f"Initial stats: {stats}")
        
        call_count = 0
        successful_calls = 0
        failed_calls = 0
        
        while call_count < self.max_calls_per_session:
            # Get next facilitator to call
            facilitator = self.csv_manager.get_next_facilitator()
            
            if not facilitator:
                logger.info("No more facilitators to call")
                break
            
            logger.info(f"[{call_count + 1}/{self.max_calls_per_session}] Preparing to call {facilitator['name']} at {facilitator['phone_number']}")
            
            # Make the call
            call_result = await self.make_call(facilitator)
            
            if call_result['success']:
                successful_calls += 1
                logger.info(f"✅ Call to {facilitator['name']} initiated successfully")
            else:
                failed_calls += 1
                logger.error(f"❌ Call to {facilitator['name']} failed: {call_result.get('error', 'Unknown error')}")
            
            call_count += 1
            
            # Wait before next call (except for the last call)
            if call_count < self.max_calls_per_session:
                logger.info(f"Waiting {self.call_interval_seconds} seconds before next call...")
                await asyncio.sleep(self.call_interval_seconds)
        
        # Final statistics
        final_stats = self.csv_manager.get_stats()
        logger.info("=== Calling Session Complete ===")
        logger.info(f"Total calls attempted: {call_count}")
        logger.info(f"Successful calls: {successful_calls}")
        logger.info(f"Failed calls: {failed_calls}")
        logger.info(f"Final stats: {final_stats}")
        
        return {
            "total_calls": call_count,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "final_stats": final_stats
        }
    
    async def make_call(self, facilitator: dict) -> dict:
        """Make a call to a specific facilitator"""
        facilitator_index = facilitator['index']
        
        try:
            # Update status to in_progress
            self.csv_manager.update_call_status(
                index=facilitator_index,
                status="in_progress",
                notes="Call initiated"
            )
            
            # Generate unique room name for this call
            timestamp = int(datetime.now().timestamp())
            room_name = f"onboarding-{facilitator_index}-{timestamp}"
            
            # Initiate the call
            call_result = await self.telephony_service.initiate_outbound_call(
                phone_number=facilitator['phone_number'],
                room_name=room_name,
                facilitator_name=facilitator['name']
            )
            
            if call_result.get('success'):
                # Update status to called
                self.csv_manager.update_call_status(
                    index=facilitator_index,
                    status="called",
                    notes=f"Call initiated successfully. Room: {room_name}, Call SID: {call_result.get('call_sid', 'N/A')}"
                )
                
                return {
                    "success": True,
                    "facilitator": facilitator['name'],
                    "room_name": room_name,
                    "call_sid": call_result.get('call_sid')
                }
            else:
                # Update status to failed
                error_msg = call_result.get('error', 'Unknown error')
                self.csv_manager.update_call_status(
                    index=facilitator_index,
                    status="failed",
                    notes=f"Call initiation failed: {error_msg}"
                )
                
                return {
                    "success": False,
                    "facilitator": facilitator['name'],
                    "error": error_msg
                }
                
        except Exception as e:
            # Update status to failed
            error_msg = f"Exception during call: {str(e)}"
            self.csv_manager.update_call_status(
                index=facilitator_index,
                status="failed",
                notes=error_msg
            )
            
            logger.error(f"Exception during call to {facilitator['name']}: {e}")
            
            return {
                "success": False,
                "facilitator": facilitator['name'],
                "error": error_msg
            }
    
    async def check_call_statuses(self):
        """Check status of ongoing calls"""
        logger.info("Checking status of recent calls...")
        
        # This would check Twilio call statuses and update records
        # Implementation depends on your specific needs
        
        return "Call status check completed"
    
    def get_calling_stats(self):
        """Get current calling statistics"""
        return self.csv_manager.get_stats()
    
    def add_facilitator(self, name: str, phone_number: str):
        """Add a new facilitator to call list"""
        self.csv_manager.add_facilitator(name, phone_number)
        logger.info(f"Added new facilitator: {name} - {phone_number}")

async def main():
    """Main function to run the call manager"""
    call_manager = CallManager()
    
    # Check if we should just show stats
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            stats = call_manager.get_calling_stats()
            print("Current Facilitator Statistics:")
            print(f"Total facilitators: {stats['total']}")
            print(f"Pending calls: {stats['pending']}")
            print(f"Completed onboardings: {stats['completed']}")
            print(f"Failed calls: {stats['failed']}")
            return
        elif sys.argv[1] == "add" and len(sys.argv) >= 4:
            name = sys.argv[2]
            phone = sys.argv[3]
            call_manager.add_facilitator(name, phone)
            return
    
    # Start the calling session
    try:
        result = await call_manager.start_calling_session()
        print("\n" + "="*50)
        print("CALLING SESSION SUMMARY")
        print("="*50)
        print(f"Total calls attempted: {result['total_calls']}")
        print(f"Successful calls: {result['successful_calls']}")
        print(f"Failed calls: {result['failed_calls']}")
        print(f"Remaining pending: {result['final_stats']['pending']}")
        print("="*50)
        
    except KeyboardInterrupt:
        logger.info("Calling session interrupted by user")
    except Exception as e:
        logger.error(f"Error during calling session: {e}")

if __name__ == "__main__":
    # Usage examples:
    # python call_manager.py                    # Start calling session
    # python call_manager.py stats              # Show statistics
    # python call_manager.py add "John Doe" "+1234567890"  # Add facilitator
    
    asyncio.run(main())
