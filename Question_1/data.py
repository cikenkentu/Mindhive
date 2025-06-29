from dataclasses import dataclass


@dataclass
class OutletInfo:
    """
    outlet information data
    """
    name: str
    location: str
    opening_time: str
    closing_time: str
    phone: str
    address: str


# sample outlet database
OUTLETS_DB = {
    "petaling_jaya": [
        OutletInfo(
            name="SS 2 Outlet",
            location="SS 2, Petaling Jaya",
            opening_time="9:00 AM",
            closing_time="10:00 PM",
            phone="+603-1234-5678",
            address="123 SS 2/4, Petaling Jaya, Selangor"
        ),
        OutletInfo(
            name="PJ Central Outlet",
            location="PJ Central, Petaling Jaya",
            opening_time="10:00 AM",
            closing_time="9:00 PM",
            phone="+603-2345-6789",
            address="456 PJ Central Mall, Petaling Jaya, Selangor"
        )
    ],
    "kuala_lumpur": [
        OutletInfo(
            name="KLCC Outlet",
            location="KLCC, Kuala Lumpur",
            opening_time="10:00 AM",
            closing_time="10:00 PM",
            phone="+603-3456-7890",
            address="789 KLCC Mall, Kuala Lumpur"
        )
    ]
} 