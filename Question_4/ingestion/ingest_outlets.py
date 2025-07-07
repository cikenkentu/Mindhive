#!/usr/bin/env python3
"""
Outlet ingestion script for ZUS Coffee outlets.
Populates SQLite database with outlet information.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.db import SessionLocal, create_tables
from app.models import Outlet

def populate_outlets_db():
    """Populate database with ZUS outlet data"""
    
    try:
        # Create tables
        create_tables()
        
        # Sample outlet data (based on ZUS Coffee locations)
        outlets_data = [
            {
                "name": "SS 2 Outlet",
                "city": "Petaling Jaya", 
                "address": "29, Jalan SS 2/61, SS 2, 47300 Petaling Jaya, Selangor",
                "hours": "9:00 AM - 10:00 PM",
                "services": "coffee,Wi-Fi,drive-thru"
            },
            {
                "name": "PJ Central Outlet",
                "city": "Petaling Jaya",
                "address": "PJ Central, Jalan Timur, 46200 Petaling Jaya, Selangor", 
                "hours": "10:00 AM - 9:00 PM",
                "services": "coffee,Wi-Fi,pastries"
            },
            {
                "name": "KLCC Outlet", 
                "city": "Kuala Lumpur",
                "address": "Suria KLCC, Kuala Lumpur City Centre, 50088 Kuala Lumpur",
                "hours": "10:00 AM - 10:00 PM",
                "services": "coffee,Wi-Fi,premium-seating"
            },
            {
                "name": "Mid Valley Outlet",
                "city": "Kuala Lumpur", 
                "address": "Mid Valley Megamall, Lingkaran Syed Putra, 59200 Kuala Lumpur",
                "hours": "10:00 AM - 10:00 PM",
                "services": "coffee,Wi-Fi,meeting-rooms"
            },
            {
                "name": "IOI City Mall Outlet",
                "city": "Putrajaya",
                "address": "IOI City Mall, Lebuh IRC, IOI Resort City, 62502 Putrajaya", 
                "hours": "10:00 AM - 10:00 PM",
                "services": "coffee,Wi-Fi,family-friendly"
            },
            {
                "name": "Bangsar Village Outlet",
                "city": "Kuala Lumpur",
                "address": "Bangsar Village II, Jalan Telawi 1, Bangsar Baru, 59100 Kuala Lumpur",
                "hours": "8:00 AM - 11:00 PM", 
                "services": "coffee,Wi-Fi,outdoor-seating"
            }
        ]
        
        # Insert data
        session = SessionLocal()
        
        # Clear existing data
        session.query(Outlet).delete()
        
        # Add new outlets
        for outlet_data in outlets_data:
            outlet = Outlet(**outlet_data)
            session.add(outlet)
        
        session.commit()
        session.close()
        
        print(f"✅ Successfully populated database with {len(outlets_data)} outlets")
        return True
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False

def verify_database():
    """Verify the populated database"""
    try:
        session = SessionLocal()
        outlets = session.query(Outlet).all()
        
        print(f"\n🔍 Database contains {len(outlets)} outlets:")
        for outlet in outlets:
            print(f"  • {outlet.name} ({outlet.city}) - {outlet.hours}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False

if __name__ == "__main__":
    print("ZUS Coffee Outlets Ingestion")
    print("=" * 40)
    
    success = populate_outlets_db()
    
    if success:
        verify_database()
    else:
        print("❌ Database population failed")
        sys.exit(1) 