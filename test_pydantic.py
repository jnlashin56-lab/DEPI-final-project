import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.schemas import BookingAction
print(BookingAction(action='create_booking', place_id=0, visit_date='20/7/2026', visit_time='2 pm'))
