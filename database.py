#!/usr/bin/env python3

import sqlite3
import os
from typing import List, Dict, Optional


class WorkshopDatabase:
    def __init__(self, db_path: str = "workshop.db"):
        """
        Initialize workshop inventory database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create main items table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workshop_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT NOT NULL,
                        location TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create index for faster searches
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_item_name
                    ON workshop_items(item_name)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_location
                    ON workshop_items(location)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_category
                    ON workshop_items(category)
                """
                )

                conn.commit()
                print(f"✅ Database initialized: {self.db_path}")

        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise

    def store_item(
        self,
        item_name: str,
        location: str,
        description: str = None,
        category: str = None,
    ) -> bool:
        """
        Store or update an item in the workshop

        Args:
            item_name: Name of the item
            location: Where the item is stored
            description: Optional description
            category: Optional category (e.g., "tool", "hardware", "material")

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if item already exists
                cursor.execute(
                    "SELECT id, location FROM workshop_items WHERE LOWER(item_name) = LOWER(?)",
                    (item_name,),
                )
                existing = cursor.fetchone()

                if existing:
                    # Update existing item
                    cursor.execute(
                        """
                        UPDATE workshop_items
                        SET location = ?, description = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (location, description, category, existing[0]),
                    )

                    print(f"📦 Updated {item_name}: {existing[1]} → {location}")
                    return True
                else:
                    # Insert new item
                    cursor.execute(
                        """
                        INSERT INTO workshop_items (item_name, location, description, category)
                        VALUES (?, ?, ?, ?)
                    """,
                        (item_name, location, description, category),
                    )

                    print(f"📦 Stored new item: {item_name} in {location}")
                    return True

        except Exception as e:
            print(f"❌ Error storing item: {e}")
            return False

    def find_item(self, item_name: str) -> Optional[Dict]:
        """
        Find an item in the workshop

        Args:
            item_name: Name of the item to find

        Returns:
            Dict with item details or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Search for exact match first, then partial match
                cursor.execute(
                    """
                    SELECT item_name, location, description, category, created_at, updated_at
                    FROM workshop_items
                    WHERE LOWER(item_name) = LOWER(?)
                    ORDER BY updated_at DESC
                    LIMIT 1
                """,
                    (item_name,),
                )

                result = cursor.fetchone()

                if not result:
                    # Try partial match
                    cursor.execute(
                        """
                        SELECT item_name, location, description, category, created_at, updated_at
                        FROM workshop_items
                        WHERE LOWER(item_name) LIKE LOWER(?)
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """,
                        (f"%{item_name}%",),
                    )

                    result = cursor.fetchone()

                if result:
                    return {
                        "item_name": result[0],
                        "location": result[1],
                        "description": result[2],
                        "category": result[3],
                        "created_at": result[4],
                        "updated_at": result[5],
                    }

                return None

        except Exception as e:
            print(f"❌ Error finding item: {e}")
            return None

    def list_items(self, category: str = None, location: str = None) -> List[Dict]:
        """
        List items in the workshop

        Args:
            category: Filter by category (optional)
            location: Filter by location (optional)

        Returns:
            List of item dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT item_name, location, description, category, created_at, updated_at
                    FROM workshop_items
                """
                params = []

                conditions = []
                if category:
                    conditions.append("LOWER(category) LIKE LOWER(?)")
                    params.append(f"%{category}%")

                if location:
                    conditions.append("LOWER(location) LIKE LOWER(?)")
                    params.append(f"%{location}%")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY updated_at DESC"

                cursor.execute(query, params)
                results = cursor.fetchall()

                items = []
                for result in results:
                    items.append(
                        {
                            "item_name": result[0],
                            "location": result[1],
                            "description": result[2],
                            "category": result[3],
                            "created_at": result[4],
                            "updated_at": result[5],
                        }
                    )

                return items

        except Exception as e:
            print(f"❌ Error listing items: {e}")
            return []

    def delete_item(self, item_name: str) -> bool:
        """
        Delete an item from the workshop

        Args:
            item_name: Name of the item to delete

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if item exists
                cursor.execute(
                    "SELECT id FROM workshop_items WHERE LOWER(item_name) = LOWER(?)",
                    (item_name,),
                )

                if cursor.fetchone():
                    cursor.execute(
                        "DELETE FROM workshop_items WHERE LOWER(item_name) = LOWER(?)",
                        (item_name,),
                    )
                    print(f"🗑️ Deleted {item_name} from inventory")
                    return True
                else:
                    print(f"❓ Item '{item_name}' not found")
                    return False

        except Exception as e:
            print(f"❌ Error deleting item: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total items
                cursor.execute("SELECT COUNT(*) FROM workshop_items")
                total_items = cursor.fetchone()[0]

                # Items by category
                cursor.execute(
                    """
                    SELECT category, COUNT(*)
                    FROM workshop_items
                    WHERE category IS NOT NULL
                    GROUP BY category
                    ORDER BY COUNT(*) DESC
                """
                )
                categories = cursor.fetchall()

                # Items by location
                cursor.execute(
                    """
                    SELECT location, COUNT(*)
                    FROM workshop_items
                    GROUP BY location
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """
                )
                locations = cursor.fetchall()

                return {
                    "total_items": total_items,
                    "categories": dict(categories),
                    "top_locations": dict(locations),
                }

        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}


def test_database():
    """Test database functionality"""
    print("🧪 Testing Workshop Database")
    print("=" * 30)

    # Initialize database
    db = WorkshopDatabase("test_workshop.db")

    # Test storing items
    print("\n📦 Testing storage:")
    db.store_item("hammer", "toolbox drawer 3", "claw hammer", "tool")
    db.store_item("screwdriver", "pegboard", "phillips head", "tool")
    db.store_item("nails", "parts bin A", "various sizes", "hardware")

    # Test finding items
    print("\n🔍 Testing retrieval:")
    hammer = db.find_item("hammer")
    if hammer:
        print(f"Found: {hammer['item_name']} in {hammer['location']}")

    missing = db.find_item("wrench")
    if not missing:
        print("Wrench not found (expected)")

    # Test listing
    print("\n📋 Testing list:")
    all_tools = db.list_items(category="tool")
    print(f"Found {len(all_tools)} tools")

    # Test stats
    print("\n📊 Database stats:")
    stats = db.get_stats()
    print(f"Total items: {stats['total_items']}")
    print(f"Categories: {stats['categories']}")

    # Clean up test database
    os.remove("test_workshop.db")
    print("\n✅ Database tests completed")


if __name__ == "__main__":
    test_database()
