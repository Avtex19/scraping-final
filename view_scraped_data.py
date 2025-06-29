#!/usr/bin/env python3
"""
Script to view scraped data from the database
"""

import sqlite3
import sys
from datetime import datetime

def view_scraped_data(db_path="scraped_data.db"):
    """View all scraped data from the database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database. Run scraping first.")
            return
            
        print("=" * 80)
        print("SCRAPED DATA VIEWER")
        print("=" * 80)
        
        # Show jobs summary
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        jobs = cursor.fetchall()
        
        if jobs:
            print(f"\nJOBS SUMMARY ({len(jobs)} total):")
            print("-" * 50)
            for job in jobs:
                status_icon = "✅" if job['status'] == 'completed' else "⏳"
                print(f"{status_icon} Job {job['job_id']}: {job['search_term']} - {job['status']}")
                if job['completed_at']:
                    print(f"   Completed: {job['completed_at']}")
        
        # Show products by source
        cursor.execute("""
            SELECT 
                search_term,
                COUNT(*) as count,
                AVG(CASE WHEN price > 0 THEN price END) as avg_price,
                MIN(scrape_time) as first_scraped
            FROM products 
            WHERE name IS NOT NULL 
            GROUP BY search_term 
            ORDER BY count DESC
        """)
        
        summaries = cursor.fetchall()
        
        if summaries:
            print(f"\nPRODUCTS SUMMARY:")
            print("-" * 50)
            for summary in summaries:
                avg_price = f"${summary['avg_price']:.2f}" if summary['avg_price'] else "N/A"
                print(f"📊 {summary['search_term']}: {summary['count']} items (Avg price: {avg_price})")
        
        # Show recent products
        cursor.execute("""
            SELECT name, price, search_term, scrape_time 
            FROM products 
            WHERE name IS NOT NULL 
            ORDER BY rowid DESC 
            LIMIT 10
        """)
        
        recent_products = cursor.fetchall()
        
        if recent_products:
            print(f"\nRECENT PRODUCTS (last 10):")
            print("-" * 50)
            for i, product in enumerate(recent_products, 1):
                name = product['name'][:50] + "..." if len(product['name']) > 50 else product['name']
                price = f"${product['price']}" if product['price'] else "N/A"
                print(f"{i:2d}. {name}")
                print(f"    Price: {price} | Category: {product['search_term']}")
                if product['scrape_time']:
                    scrape_time = product['scrape_time'][:19]  # Remove microseconds
                    print(f"    Scraped: {scrape_time}")
                print()
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) as total FROM products WHERE name IS NOT NULL")
        total_products = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as with_price FROM products WHERE price > 0")
        with_price = cursor.fetchone()['with_price']
        
        cursor.execute("SELECT MIN(price) as min_price, MAX(price) as max_price FROM products WHERE price > 0")
        price_range = cursor.fetchone()
        
        print("STATISTICS:")
        print("-" * 50)
        print(f"Total products: {total_products}")
        print(f"Products with price: {with_price}")
        if price_range['min_price'] and price_range['max_price']:
            print(f"Price range: ${price_range['min_price']:.2f} - ${price_range['max_price']:.2f}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def search_products(query, db_path="scraped_data.db"):
    """Search for products by name."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, price, search_term, link 
            FROM products 
            WHERE name LIKE ? 
            ORDER BY price ASC
        """, (f"%{query}%",))
        
        results = cursor.fetchall()
        
        if results:
            print(f"\nSEARCH RESULTS for '{query}' ({len(results)} found):")
            print("-" * 50)
            for i, product in enumerate(results, 1):
                name = product['name'][:60] + "..." if len(product['name']) > 60 else product['name']
                price = f"${product['price']}" if product['price'] else "N/A"
                print(f"{i:2d}. {name}")
                print(f"    Price: {price} | Category: {product['search_term']}")
                if product['link']:
                    print(f"    Link: {product['link'][:80]}...")
                print()
        else:
            print(f"No products found matching '{query}'")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Search mode
        query = " ".join(sys.argv[1:])
        search_products(query)
    else:
        # View all data
        view_scraped_data()
        
    print("\nUsage:")
    print("  python view_scraped_data.py           # View all data")
    print("  python view_scraped_data.py laptop    # Search for 'laptop'") 