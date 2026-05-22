from datetime import datetime, timedelta
from collections import defaultdict
import heapq
from typing import List, Dict, Optional, Tuple

# ============================================================================
# DATA STRUCTURES AND AlGORITHM by Jyoti Chhetri 
# ============================================================================

class Table:
    """Represents a restaurant table"""
    def __init__(self, table_id: int, capacity: int, location: str):
        self.table_id = table_id
        self.capacity = capacity
        self.location = location
    
    def __repr__(self):
        return f"Table({self.table_id}, capacity={self.capacity}, location={self.location})"


class Customer:
    """Represents a customer"""
    def __init__(self, customer_id: int, name: str, phone: str, email: str):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email
        self.reservation_history = []
    
    def __repr__(self):
        return f"Customer({self.customer_id}, {self.name})"


class Reservation:
    """Represents a reservation"""
    def __init__(self, reservation_id: int, customer: Customer, table: Table, 
                 reservation_time: datetime, duration_minutes: int, party_size: int):
        self.reservation_id = reservation_id
        self.customer = customer
        self.table = table
        self.reservation_time = reservation_time
        self.duration_minutes = duration_minutes
        self.party_size = party_size
        self.status = "CONFIRMED"  # CONFIRMED, CANCELLED, COMPLETED
        self.created_at = datetime.now()
    
    def get_end_time(self) -> datetime:
        """Calculate end time of reservation"""
        return self.reservation_time + timedelta(minutes=self.duration_minutes)
    
    def __repr__(self):
        return f"Reservation({self.reservation_id}, {self.customer.name}, Table {self.table.table_id}, {self.reservation_time})"


class WaitlistEntry:
    """Represents a customer on the waitlist"""
    def __init__(self, customer: Customer, party_size: int, requested_time: datetime, priority: float):
        self.customer = customer
        self.party_size = party_size
        self.requested_time = requested_time
        self.priority = priority  # Lower value = higher priority
        self.added_at = datetime.now()
    
    def __lt__(self, other):
        """Comparison for priority queue (min-heap)"""
        return self.priority < other.priority
    
    def __repr__(self):
        return f"WaitlistEntry({self.customer.name}, party_size={self.party_size})"


# ============================================================================
# RESTAURANT RESERVATION SYSTEM
# ============================================================================

class RestaurantReservationSystem:
    """
    Main reservation system using various algorithms and data structures:
    - Hash Maps for O(1) lookups
    - Priority Queue (Min-Heap) for waitlist management
    - Sorting for time-slot management
    - Binary Search for available time slots
    """
    
    def __init__(self, restaurant_name: str, open_time: str = "10:00", close_time: str = "22:00"):
        self.restaurant_name = restaurant_name
        self.open_time = datetime.strptime(open_time, "%H:%M").time()
        self.close_time = datetime.strptime(close_time, "%H:%M").time()
        
        # Data structures
        self.tables: Dict[int, Table] = {}  # Hash map for tables
        self.customers: Dict[int, Customer] = {}  # Hash map for customers
        self.reservations: Dict[int, Reservation] = {}  # Hash map for reservations
        self.reservations_by_date: defaultdict = defaultdict(list)  # For date-based lookup
        self.waitlist: List[WaitlistEntry] = []  # Min-heap for waitlist priority
        
        # Counters
        self.next_reservation_id = 1
        self.next_customer_id = 1
    
    # ========================================================================
    # TABLE MANAGEMENT
    # ========================================================================
    
    def add_table(self, table_id: int, capacity: int, location: str) -> Table:
        """Add a new table to the restaurant"""
        if table_id in self.tables:
            raise ValueError(f"Table {table_id} already exists")
        
        table = Table(table_id, capacity, location)
        self.tables[table_id] = table
        return table
    
    def get_tables_by_capacity(self, party_size: int) -> List[Table]:
        """Get all tables that can accommodate party size (sorted by capacity)"""
        suitable_tables = [t for t in self.tables.values() if t.capacity >= party_size]
        # Sorting algorithm - sort by capacity (ascending) for optimal table allocation
        suitable_tables.sort(key=lambda t: t.capacity)
        return suitable_tables
    
    # ========================================================================
    # CUSTOMER MANAGEMENT
    # ========================================================================
    
    def register_customer(self, name: str, phone: str, email: str) -> Customer:
        """Register a new customer"""
        customer_id = self.next_customer_id
        self.next_customer_id += 1
        
        customer = Customer(customer_id, name, phone, email)
        self.customers[customer_id] = customer
        return customer
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID (O(1) hash map lookup)"""
        return self.customers.get(customer_id)
    
    def get_customer_by_name(self, name: str) -> Optional[Customer]:
        """Search for customer by name (O(n) linear search)"""
        for customer in self.customers.values():
            if customer.name.lower() == name.lower():
                return customer
        return None
    
    # ========================================================================
    # AVAILABILITY CHECK (Sorting + Interval Logic)
    # ========================================================================
    
    def is_table_available(self, table: Table, reservation_time: datetime, 
                          duration_minutes: int) -> bool:
        """
        Check if a table is available for the given time slot.
        Uses sorted reservations and interval checking.
        """
        requested_end = reservation_time + timedelta(minutes=duration_minutes)
        date_key = reservation_time.date()
        
        # Get reservations for this table on this date
        reservations_on_date = [r for r in self.reservations_by_date[date_key] 
                               if r.table.table_id == table.table_id and r.status == "CONFIRMED"]
        
        # Sort by time (O(n log n))
        reservations_on_date.sort(key=lambda r: r.reservation_time)
        
        # Check for conflicts (O(n))
        for reservation in reservations_on_date:
            existing_end = reservation.get_end_time()
            
            # Check for overlap: requested time overlaps with existing reservation
            if (reservation_time < existing_end and requested_end > reservation.reservation_time):
                return False
        
        return True
    
    def find_available_tables(self, party_size: int, reservation_time: datetime, 
                             duration_minutes: int) -> List[Table]:
        """
        Find all available tables for the given party size and time.
        Returns tables sorted by capacity (best fit first).
        """
        suitable_tables = self.get_tables_by_capacity(party_size)
        available_tables = []
        
        for table in suitable_tables:
            if self.is_table_available(table, reservation_time, duration_minutes):
                available_tables.append(table)
        
        return available_tables
    
    def get_next_available_times(self, party_size: int, date: datetime, 
                                time_interval_minutes: int = 30) -> List[datetime]:
        """
        Get next available time slots for a party on a given date.
        Uses time slot iteration and availability checking.
        """
        available_times = []
        current_time = datetime.combine(date.date(), self.open_time)
        close_datetime = datetime.combine(date.date(), self.close_time)
        
        while current_time < close_datetime:
            available_tables = self.find_available_tables(party_size, current_time, 90)  # 90 min default
            if available_tables:
                available_times.append(current_time)
            
            current_time += timedelta(minutes=time_interval_minutes)
        
        return available_times
    
    # ========================================================================
    # RESERVATION MANAGEMENT
    # ========================================================================
    
    def make_reservation(self, customer_id: int, party_size: int, 
                        reservation_time: datetime, duration_minutes: int = 90) -> Optional[Reservation]:
        """
        Make a reservation for a customer.
        Returns Reservation if successful, None if no tables available.
        """
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Validation
        if party_size <= 0:
            raise ValueError("Party size must be positive")
        
        # Find available table
        available_tables = self.find_available_tables(party_size, reservation_time, duration_minutes)
        
        if not available_tables:
            return None
        
        # Choose the best fit table (smallest capacity that fits)
        chosen_table = available_tables[0]
        
        # Create reservation
        reservation_id = self.next_reservation_id
        self.next_reservation_id += 1
        
        reservation = Reservation(reservation_id, customer, chosen_table, 
                                 reservation_time, duration_minutes, party_size)
        
        # Store reservation
        self.reservations[reservation_id] = reservation
        date_key = reservation_time.date()
        self.reservations_by_date[date_key].append(reservation)
        customer.reservation_history.append(reservation)
        
        return reservation
    
    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancel a reservation"""
        if reservation_id not in self.reservations:
            return False
        
        reservation = self.reservations[reservation_id]
        reservation.status = "CANCELLED"
        return True
    
    def get_reservation(self, reservation_id: int) -> Optional[Reservation]:
        """Get reservation by ID (O(1) lookup)"""
        return self.reservations.get(reservation_id)
    
    # ========================================================================
    # WAITLIST MANAGEMENT (Priority Queue / Min-Heap)
    # ========================================================================
    
    def add_to_waitlist(self, customer_id: int, party_size: int, 
                       requested_time: datetime) -> WaitlistEntry:
        """
        Add customer to waitlist if no tables available.
        Uses priority queue (min-heap) where earlier wait times have higher priority.
        """
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Priority is based on how long they've been waiting (will update over time)
        priority = datetime.now().timestamp()
        entry = WaitlistEntry(customer, party_size, requested_time, priority)
        
        # Add to min-heap
        heapq.heappush(self.waitlist, entry)
        
        return entry
    
    def get_waitlist(self) -> List[WaitlistEntry]:
        """Get current waitlist (sorted by priority)"""
        # Create a sorted copy for display (don't modify heap)
        return sorted(self.waitlist, key=lambda x: x.priority)
    
    # ========================================================================
    # REPORTING AND ANALYTICS
    # ========================================================================
    
    def get_reservations_for_date(self, date: datetime) -> List[Reservation]:
        """Get all reservations for a specific date (sorted by time)"""
        reservations = self.reservations_by_date[date.date()]
        # Sorting algorithm
        reservations.sort(key=lambda r: r.reservation_time)
        return reservations
    
    def get_customer_history(self, customer_id: int) -> List[Reservation]:
        """Get reservation history for a customer"""
        customer = self.get_customer(customer_id)
        if not customer:
            return []
        return customer.reservation_history
    
    def get_occupancy_report(self, date: datetime) -> Dict:
        """Generate occupancy report for a date"""
        reservations = self.get_reservations_for_date(date)
        confirmed = [r for r in reservations if r.status == "CONFIRMED"]
        cancelled = [r for r in reservations if r.status == "CANCELLED"]
        
        total_covers = sum(r.party_size for r in confirmed)
        
        return {
            "date": date.date(),
            "total_reservations": len(confirmed),
            "total_cancellations": len(cancelled),
            "total_covers": total_covers,
            "average_party_size": total_covers / len(confirmed) if confirmed else 0,
            "occupancy_rate": (total_covers / (len(self.tables) * 2)) * 100 if self.tables else 0
        }
    
    def __str__(self):
        return f"RestaurantReservationSystem: {self.restaurant_name} ({len(self.tables)} tables, {len(self.reservations)} reservations)"


# ============================================================================
# INTERACTIVE USER INTERFACE
# ============================================================================

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_menu(options):
    """Print menu options"""
    for key, value in options.items():
        print(f"  {key}. {value}")


def get_valid_input(prompt, input_type=str, min_val=None, max_val=None):
    """Get and validate user input"""
    while True:
        try:
            user_input = input(f"\n{prompt}: ").strip()
            
            if input_type == int:
                value = int(user_input)
                if min_val is not None and value < min_val:
                    print(f"  ✗ Please enter a value >= {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"  ✗ Please enter a value <= {max_val}")
                    continue
                return value
            
            elif input_type == str:
                if not user_input:
                    print("  ✗ Input cannot be empty")
                    continue
                return user_input
            
            return input_type(user_input)
        
        except ValueError:
            print(f"  ✗ Invalid input. Please enter a valid {input_type.__name__}")


def get_date_input(prompt):
    """Get and validate date input"""
    while True:
        date_str = input(f"\n{prompt} (YYYY-MM-DD): ").strip()
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date.date() < datetime.now().date():
                print("  ✗ Please enter a future date")
                continue
            return date
        except ValueError:
            print("  ✗ Invalid date format. Please use YYYY-MM-DD")


def get_time_input(prompt):
    """Get and validate time input"""
    while True:
        time_str = input(f"\n{prompt} (HH:MM, 24-hour format): ").strip()
        try:
            time = datetime.strptime(time_str, "%H:%M").time()
            return time
        except ValueError:
            print("  ✗ Invalid time format. Please use HH:MM")


def main():
    """Main interactive application"""
    
    print_header("WELCOME TO RESTAURANT RESERVATION SYSTEM")
    print("\nThis system uses advanced data structures and algorithms:")
    print("  • Hash Maps for fast customer/reservation lookups (O(1))")
    print("  • Sorting for optimal table allocation")
    print("  • Interval checking for conflict detection")
    print("  • Priority Queues for fair waitlist management")
    
    # Initialize restaurant
    restaurant = RestaurantReservationSystem("Gourmet Haven", "11:00", "23:00")
    
    # Pre-populate with some tables
    print_header("INITIALIZING RESTAURANT")
    restaurant.add_table(1, 2, "Window")
    restaurant.add_table(2, 2, "Window")
    restaurant.add_table(3, 4, "Center")
    restaurant.add_table(4, 4, "Center")
    restaurant.add_table(5, 6, "Private")
    restaurant.add_table(6, 8, "Private")
    print(f"\n✓ Restaurant initialized with {len(restaurant.tables)} tables")
    print("  • Tables 1-2: 2-seater (Window)")
    print("  • Tables 3-4: 4-seater (Center)")
    print("  • Tables 5-6: 6-8 seater (Private)")
    
    # Main menu loop
    while True:
        print_header("MAIN MENU")
        menu_options = {
            "1": "Make a Reservation",
            "2": "Register New Customer",
            "3": "View Available Times",
            "4": "Check Reservation Status",
            "5": "View All Reservations for a Date",
            "6": "Cancel a Reservation",
            "7": "Exit"
        }
        print_menu(menu_options)
        
        choice = get_valid_input("Enter your choice", str)        
        # OPTION 1: MAKE A RESERVATION
        if choice == "1":
            print_header("MAKE A RESERVATION")
            
            # Get customer name
            customer_name = get_valid_input("Enter your name", str)
            
            # Check if customer exists
            customer = restaurant.get_customer_by_name(customer_name)
            
            if not customer:
                print("\n  ℹ Customer not found. Let's register you first!")
                phone = get_valid_input("Enter phone number", str)
                email = get_valid_input("Enter email address", str)
                customer = restaurant.register_customer(customer_name, phone, email)
                print(f"\n  ✓ Customer registered! ID: {customer.customer_id}")
            else:
                print(f"\n  ✓ Welcome back, {customer.name}!")
            
            # Get party size
            party_size = get_valid_input("How many people in your party?", int, min_val=1, max_val=20)
            
            # Get reservation date
            reservation_date = get_date_input("What date would you like?")
            
            # Show available times
            print("\n  🔍 Checking available times...")
            available_times = restaurant.get_next_available_times(party_size, reservation_date)
            
            if not available_times:
                print(f"\n  ✗ No available times for {party_size} people on {reservation_date.date()}")
                
                # Offer waitlist option
                waitlist_choice = input("\n  Would you like to be added to the waitlist? (yes/no): ").lower()
                if waitlist_choice == "yes":
                    requested_time = datetime.combine(reservation_date.date(), get_time_input("What time would you prefer?"))
                    restaurant.add_to_waitlist(customer.customer_id, party_size, requested_time)
                    print(f"\n  ✓ You've been added to the waitlist!")
                continue
            
            print(f"\n  Available times for {party_size} people:")
            for i, time in enumerate(available_times[:10], 1):  # Show first 10
                print(f"    {i}. {time.strftime('%H:%M')}")
            
            if len(available_times) > 10:
                print(f"    ... and {len(available_times) - 10} more times")
            
            # Let user choose time
            time_choice = get_valid_input("\nEnter the time number you prefer", int, min_val=1, max_val=len(available_times))
            chosen_time = available_times[time_choice - 1]
            
            # Get duration
            duration = get_valid_input("How long do you plan to stay? (minutes, default 90)", int, min_val=30, max_val=180)
            if not duration:
                duration = 90
            
            # Make reservation
            print(f"\n  📝 Processing your reservation...")
            reservation = restaurant.make_reservation(customer.customer_id, party_size, chosen_time, duration)
            
            if reservation:
                print_header("✓ RESERVATION CONFIRMED!")
                print(f"\n  Reservation ID:  {reservation.reservation_id}")
                print(f"  Name:            {reservation.customer.name}")
                print(f"  Party Size:      {reservation.party_size}")
                print(f"  Date:            {reservation.reservation_time.strftime('%A, %B %d, %Y')}")
                print(f"  Time:            {reservation.reservation_time.strftime('%H:%M')} - {reservation.get_end_time().strftime('%H:%M')}")
                print(f"  Table Number:    {reservation.table.table_id}")
                print(f"  Table Location:  {reservation.table.location}")
                print(f"  Duration:        {reservation.duration_minutes} minutes")
            else:
                print("\n  ✗ Failed to make reservation. Please try again.")
        
        # ====================================================================
        # OPTION 2: REGISTER NEW CUSTOMER
        # ====================================================================
        elif choice == "2":
            print_header("REGISTER NEW CUSTOMER")
            
            name = get_valid_input("Enter full name", str)
            phone = get_valid_input("Enter phone number", str)
            email = get_valid_input("Enter email address", str)
            
            customer = restaurant.register_customer(name, phone, email)
            print_header("✓ CUSTOMER REGISTERED")
            print(f"\n  Customer ID:  {customer.customer_id}")
            print(f"  Name:         {customer.name}")
            print(f"  Phone:        {customer.phone}")
            print(f"  Email:        {customer.email}")
        
        # ====================================================================
        # OPTION 3: VIEW AVAILABLE TIMES
        # ====================================================================
        elif choice == "3":
            print_header("CHECK AVAILABLE TIMES")
            
            party_size = get_valid_input("How many people?", int, min_val=1, max_val=20)
            check_date = get_date_input("What date?")
            
            print(f"\n  🔍 Checking availability...")
            available_times = restaurant.get_next_available_times(party_size, check_date)
            
            if available_times:
                print(f"\n  ✓ Available times for {party_size} people on {check_date.date()}:")
                for i, time in enumerate(available_times[:15], 1):
                    print(f"    {i}. {time.strftime('%H:%M')}")
                if len(available_times) > 15:
                    print(f"    ... and {len(available_times) - 15} more times")
            else:
                print(f"\n  ✗ No available times for {party_size} people on {check_date.date()}")
        
        # ====================================================================
        # OPTION 4: CHECK RESERVATION STATUS
        # ====================================================================
        elif choice == "4":
            print_header("CHECK RESERVATION STATUS")
            
            res_id = get_valid_input("Enter reservation ID", int)
            reservation = restaurant.get_reservation(res_id)
            
            if reservation:
                print_header("RESERVATION DETAILS")
                print(f"\n  Reservation ID:  {reservation.reservation_id}")
                print(f"  Status:          {reservation.status}")
                print(f"  Name:            {reservation.customer.name}")
                print(f"  Party Size:      {reservation.party_size}")
                print(f"  Date:            {reservation.reservation_time.strftime('%A, %B %d, %Y')}")
                print(f"  Time:            {reservation.reservation_time.strftime('%H:%M')} - {reservation.get_end_time().strftime('%H:%M')}")
                print(f"  Table:           {reservation.table.table_id} ({reservation.table.location})")
            else:
                print("\n  ✗ Reservation not found")
        
        # ====================================================================
        # OPTION 5: VIEW ALL RESERVATIONS FOR A DATE
        # ====================================================================
        elif choice == "5":
            print_header("VIEW RESERVATIONS FOR A DATE")
            
            check_date = get_date_input("Enter date")
            reservations = restaurant.get_reservations_for_date(check_date)
            
            if reservations:
                print_header(f"RESERVATIONS FOR {check_date.date()}")
                print(f"\n  Total reservations: {len(reservations)}\n")
                for res in reservations:
                    status_symbol = "✓" if res.status == "CONFIRMED" else "✗"
                    print(f"  {status_symbol} {res.reservation_time.strftime('%H:%M')}: "
                          f"{res.customer.name} ({res.party_size} people) - "
                          f"Table {res.table.table_id}")
            else:
                print(f"\n  No reservations for {check_date.date()}")
        
        # ====================================================================
        # OPTION 6: CANCEL A RESERVATION
        # ====================================================================
        elif choice == "6":
            print_header("CANCEL A RESERVATION")
            
            res_id = get_valid_input("Enter reservation ID to cancel", int)
            
            if restaurant.cancel_reservation(res_id):
                print(f"\n  ✓ Reservation {res_id} has been cancelled")
            else:
                print(f"\n  ✗ Reservation not found")
        
        # ====================================================================
        # OPTION 7: EXIT
        # ====================================================================
        elif choice == "7":
            print_header("THANK YOU FOR USING OUR SYSTEM!")
            print("\n  Final Statistics:")
            print(f"  • Total Customers: {len(restaurant.customers)}")
            print(f"  • Total Reservations: {len(restaurant.reservations)}")
            print(f"  • Waitlist Size: {len(restaurant.waitlist)}")
            print(f"  • Total Tables: {len(restaurant.tables)}")
            print("\n  Goodbye! \n")
            break
        
        else:
            print("\n  ✗ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
