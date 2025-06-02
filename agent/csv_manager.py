"""
CSV manager for handling facilitator phone numbers and call tracking.
"""
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import os

logger = logging.getLogger("csv_manager")

class CSVManager:
    def __init__(self, csv_file_path: str = "facilitators.csv"):
        self.csv_file_path = csv_file_path
        self.df = None
        self.load_csv()
    
    def load_csv(self):
        """Load the CSV file with facilitator data."""
        try:
            if os.path.exists(self.csv_file_path):
                self.df = pd.read_csv(self.csv_file_path)
                logger.info(f"Loaded CSV with {len(self.df)} records")
            else:
                # Create default CSV structure
                self.df = pd.DataFrame(columns=[
                    'name', 'phone_number', 'status', 'last_called', 
                    'call_attempts', 'notes', 'onboarding_completed'
                ])
                self.save_csv()
                logger.info(f"Created new CSV file: {self.csv_file_path}")
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            self.df = pd.DataFrame(columns=[
                'name', 'phone_number', 'status', 'last_called', 
                'call_attempts', 'notes', 'onboarding_completed'
            ])
    
    def save_csv(self):
        """Save the current dataframe to CSV."""
        try:
            self.df.to_csv(self.csv_file_path, index=False)
            logger.info(f"Saved CSV to {self.csv_file_path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    def get_next_facilitator(self) -> Optional[Dict[str, Any]]:
        """Get the next facilitator to call based on priority logic."""
        if self.df.empty:
            return None
        
        # Filter for facilitators who haven't completed onboarding
        pending = self.df[self.df['onboarding_completed'] != True].copy()
        
        if pending.empty:
            return None
        
        # Sort by call attempts (ascending) and last called (ascending, nulls first)
        pending['last_called'] = pd.to_datetime(pending['last_called'], errors='coerce')
        pending = pending.sort_values(['call_attempts', 'last_called'], na_position='first')
        
        # Get the first facilitator
        facilitator = pending.iloc[0]
        return {
            'index': facilitator.name,  # pandas index
            'name': facilitator['name'],
            'phone_number': facilitator['phone_number'],
            'status': facilitator['status'],
            'last_called': facilitator['last_called'],
            'call_attempts': facilitator['call_attempts'] if pd.notna(facilitator['call_attempts']) else 0,
            'notes': facilitator['notes'],
            'onboarding_completed': facilitator['onboarding_completed']
        }
    
    def update_call_status(self, index: int, status: str, notes: str = "", completed: bool = False):
        """Update the call status for a facilitator."""
        try:
            self.df.loc[index, 'status'] = status
            self.df.loc[index, 'last_called'] = datetime.now().isoformat()
            self.df.loc[index, 'call_attempts'] = self.df.loc[index, 'call_attempts'] + 1 if pd.notna(self.df.loc[index, 'call_attempts']) else 1
            if notes:
                current_notes = self.df.loc[index, 'notes'] if pd.notna(self.df.loc[index, 'notes']) else ""
                self.df.loc[index, 'notes'] = f"{current_notes}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {notes}".strip()
            if completed:
                self.df.loc[index, 'onboarding_completed'] = True
            self.save_csv()
            logger.info(f"Updated facilitator {index} with status: {status}")
        except Exception as e:
            logger.error(f"Error updating call status: {e}")
    
    def add_facilitator(self, name: str, phone_number: str):
        """Add a new facilitator to the CSV."""
        new_row = {
            'name': name,
            'phone_number': phone_number,
            'status': 'pending',
            'last_called': None,
            'call_attempts': 0,
            'notes': '',
            'onboarding_completed': False
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save_csv()
        logger.info(f"Added new facilitator: {name} - {phone_number}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the facilitators."""
        if self.df.empty:
            return {'total': 0, 'pending': 0, 'completed': 0, 'failed': 0}
        
        total = len(self.df)
        completed = len(self.df[self.df['onboarding_completed'] == True])
        pending = len(self.df[self.df['onboarding_completed'] != True])
        failed = len(self.df[self.df['status'] == 'failed'])
        
        return {
            'total': total,
            'pending': pending,
            'completed': completed,
            'failed': failed
        }
