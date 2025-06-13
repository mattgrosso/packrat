#!/usr/bin/env python3

import sqlite3
import os

def inspect_workshop_db(db_path="workshop.db"):
    """Inspect the workshop database schema and contents"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"🔍 Inspecting database: {db_path}")
            print("=" * 50)
            
            # 1. Show schema
            print("\n📋 DATABASE SCHEMA:")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table_sql in tables:
                if table_sql[0]:
                    print(f"\n{table_sql[0]};")
            
            # 2. Show indexes
            print("\n🗂️  INDEXES:")
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
            indexes = cursor.fetchall()
            
            if indexes:
                for name, sql in indexes:
                    print(f"- {name}: {sql}")
            else:
                print("No custom indexes found")
            
            # 3. Show table contents
            print("\n📦 TABLE CONTENTS:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n🗃️  Table '{table_name}' has {count} rows")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    print(f"Columns: {', '.join(columns)}")
                    print("Sample data:")
                    for i, row in enumerate(rows, 1):
                        print(f"  {i}: {row}")
                    
                    if count > 5:
                        print(f"  ... and {count - 5} more rows")
    
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

def show_all_items():
    """Show all items in a nice format"""
    try:
        with sqlite3.connect("workshop.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT item_name, location, description, category, 
                       created_at, updated_at 
                FROM workshop_items 
                ORDER BY updated_at DESC
            """)
            
            items = cursor.fetchall()
            
            if not items:
                print("📭 No items in workshop database")
                return
            
            print(f"\n🔧 ALL WORKSHOP ITEMS ({len(items)} total):")
            print("=" * 60)
            
            for i, (name, location, desc, category, created, updated) in enumerate(items, 1):
                print(f"\n{i}. {name.upper()}")
                print(f"   📍 Location: {location}")
                if desc:
                    print(f"   📝 Description: {desc}")
                if category:
                    print(f"   🏷️  Category: {category}")
                print(f"   📅 Added: {created}")
                if updated != created:
                    print(f"   🔄 Updated: {updated}")
    
    except Exception as e:
        print(f"❌ Error showing items: {e}")

if __name__ == "__main__":
    inspect_workshop_db()
    show_all_items()