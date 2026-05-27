# Restaurant-Reservation-System
A Python restaurant reservation system using data structures and algorithms (Hash Maps, Priority Queues, Sorting)
### Data Structure #1: Hash Maps (Dictionaries)

First, hash maps.

When I store customers in a hash map with their ID as the key, finding a customer is instant - O(1) time complexity. That means whether I have 10 customers or 10 million customers, finding one takes the same tiny fraction of a second.

In my code, I use:
```python
self.customers: Dict[int, Customer] = {}  # Hash map for instant lookup
Data Structure #2: Sorting
Second, sorting. I use sorting to find the best table for a customer.

When someone wants a table for 4 people, I don't want to give them the huge 8-person table if a 4-person table is available. That wastes space. So I sort all available tables by capacity - smallest first - and pick the best fit.

In my code:

Python
suitable_tables.sort(key=lambda t: t.capacity)  # Sort by capacity
return suitable_tables[0]  # Pick smallest table that fits
This uses merge sort or quicksort, which is O(n log n). So sorting 1,000 tables takes about 10,000 operations. Instant.

Data Structure #3: Linked Lists Concept
Third, linked lists. I use them for customer reservation history.

Each customer has a list of their past reservations. This is like a chain where each reservation points to the next one. When I need to show a customer their booking history, I walk through this chain.

Python
customer.reservation_history = []  # Chain of reservations
customer.reservation_history.append(reservation)  # Add to chain
Data Structure #4: Priority Queue (Min-Heap)
Fourth, and this is the coolest one: a priority queue using a min-heap.

Imagine a waitlist of 100 customers. Who gets the next available table? Fair systems say: the person who's been waiting longest. That person has priority.

A min-heap is a tree structure that always keeps the highest priority item at the top. So when a table becomes free, I just pop from the top - O(log n) time - instead of searching through all 100 people.

In my code:

Python
heapq.heappush(self.waitlist, entry)  # Add to priority queue
entry = heapq.heappop(self.waitlist)  # Get highest priority person
With 1 million people on the waitlist, popping takes about 20 operations. Instant!

SECTION 5: CORE ALGORITHM - CONFLICT DETECTION (3 minutes)
[SCREEN SHARE - Show code, draw diagram if needed]

Now for the heart of my system: detecting booking conflicts. This is the algorithm that prevents double-booking.

Here's the problem: Alice books Table 3 from 7:00 PM to 8:30 PM. Bob wants Table 3 from 7:15 PM to 8:45 PM. These times overlap! The system must detect this conflict.

Here's how my algorithm works:

Step 1: Get all reservations for this table on this date

When checking availability, I get all confirmed reservations for that specific table on that specific date. This narrows down my search space.

Step 2: Sort by time

I sort these reservations by start time. So now they're in order: 6:00 PM, 7:00 PM, 8:30 PM, etc.

Step 3: Check for overlaps

Here's the key logic:

Python
for reservation in reservations_on_date:
    existing_end = reservation.get_end_time()
    
    # Check if requested time overlaps with existing reservation
    if (reservation_time < existing_end and 
        requested_end > reservation.reservation_time):
        return False  # CONFLICT!
