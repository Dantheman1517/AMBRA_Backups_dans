"""
MongoDB Hello World Example - Document Store Model
==================================================

This module demonstrates basic MongoDB operations using PyMongo.
It showcases the document store model with CRUD operations.

Requirements:
    pip install pymongo

Usage:
    python mongodb_hello_world.py
"""

from pymongo import MongoClient
from datetime import datetime
import json
from typing import List, Dict, Any


class MongoDBHelloWorld:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database_name: str = "hello_world_db"):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db.users
        
    def insert_sample_documents(self) -> None:
        """Insert sample documents to demonstrate document store model."""
        print("=== Inserting Sample Documents ===")
        
        # Sample documents with different schemas (document store flexibility)
        users = [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "age": 28,
                "role": "developer",
                "skills": ["Python", "JavaScript", "MongoDB"],
                "created_at": datetime.now(),
                "profile": {
                    "bio": "Full-stack developer with 5 years experience",
                    "location": "San Francisco, CA"
                }
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "age": 35,
                "role": "manager",
                "department": "Engineering",
                "created_at": datetime.now(),
                "team_size": 8,
                "projects": ["Project A", "Project B"]
            },
            {
                "name": "Carol Davis",
                "email": "carol@example.com",
                "role": "designer",
                "portfolio": "https://caroldesigns.com",
                "created_at": datetime.now(),
                "specialties": ["UI/UX", "Graphic Design"]
            }
        ]
        
        # Insert multiple documents
        result = self.collection.insert_many(users)
        print(f"Inserted {len(result.inserted_ids)} documents")
        print("Document IDs:", [str(id) for id in result.inserted_ids])
        users = [
            {
                "_id": 1,
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "age": 30,
                "created_at": datetime.now(),
                "profile": {
                    "bio": "Data scientist passionate about machine learning",
                    "location": "San Francisco, CA",
                    "interests": ["machine learning", "data visualization", "python"]
                },
                "projects": [
                    {"name": "ML Pipeline", "status": "active", "start_date": datetime(2024, 1, 15)},
                    {"name": "Data Dashboard", "status": "completed", "start_date": datetime(2023, 8, 1)}
                ]
            },
            {
                "_id": 2,
                "name": "Bob Smith",
                "email": "bob@example.com",
                "age": 25,
                "created_at": datetime.now(),
                "profile": {
                    "bio": "Full-stack developer",
                    "location": "New York, NY",
                    "interests": ["web development", "javascript", "react"]
                },
                "skills": ["JavaScript", "Python", "React", "Node.js"],  # Different schema structure
                "experience_years": 3
            },
            {
                "_id": 3,
                "name": "Carol Davis",
                "email": "carol@example.com",
                "age": 35,
                "created_at": datetime.now(),
                "profile": {
                    "bio": "DevOps engineer",
                    "location": "Austin, TX"
                },
                "certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
                "projects": [
                    {"name": "Infrastructure Automation", "status": "active", "start_date": datetime(2024, 3, 1)}
                ]
            }
        ]
        
        # Insert documents
        try:
            result = self.collection.insert_many(users)
            print(f"✓ Inserted {len(result.inserted_ids)} documents")
            print(f"  Inserted IDs: {result.inserted_ids}")
        except Exception as e:
            print(f"✗ Error inserting documents: {e}")
    
    def find_documents(self) -> None:
        """Demonstrate various query operations."""
        print("\n=== Finding Documents ===")
        
        # Find all documents
        print("All users:")
        for user in self.collection.find():
            print(f"  - {user['name']} ({user['email']})")
        
        # Find with filter
        print("\nDevelopers:")
        for user in self.collection.find({"role": "developer"}):
            print(f"  - {user['name']}: {user.get('skills', [])}")
        
        # Find with projection (only specific fields)
        print("\nNames and emails only:")
        for user in self.collection.find({}, {"name": 1, "email": 1, "_id": 0}):
            print(f"  - {user['name']}: {user['email']}")
        
        # Find one document
        alice = self.collection.find_one({"name": "Alice Johnson"})
        if alice:
            print(f"\nFound Alice: {alice['email']}")
        """Demonstrate various find operations."""
        print("\n=== Finding Documents ===")
        
        # Find all documents
        print("All users:")
        for user in self.collection.find():
            print(f"  - {user['name']} ({user['email']})")
        
        # Find with filter
        print("\nUsers older than 28:")
        for user in self.collection.find({"age": {"$gt": 28}}):
            print(f"  - {user['name']}, age: {user['age']}")
        
        # Find with projection (select specific fields)
        print("\nUser names and emails only:")
        for user in self.collection.find({}, {"name": 1, "email": 1, "_id": 0}):
            print(f"  - {user['name']}: {user['email']}")
        
        # Find nested field
        print("\nUsers from San Francisco:")
        for user in self.collection.find({"profile.location": {"$regex": "San Francisco"}}):
            print(f"  - {user['name']}")
        
        # Find array elements
        print("\nUsers with machine learning interest:")
        for user in self.collection.find({"profile.interests": "machine learning"}):
            print(f"  - {user['name']}")
    
    def update_documents(self) -> None:
        """Demonstrate update operations."""
        print("\n=== Updating Documents ===")
        
        # Update one document
        result = self.collection.update_one(
            {"name": "Alice Johnson"},
            {"$set": {"age": 29, "last_updated": datetime.now()}}
        )
        print(f"Updated {result.modified_count} document(s)")
        
        # Update many documents
        result = self.collection.update_many(
            {"role": "developer"},
            {"$push": {"skills": "Docker"}}
        )
        print(f"Added Docker skill to {result.modified_count} developer(s)")
        
        # Upsert (insert if not exists)
        result = self.collection.update_one(
            {"name": "David Wilson"},
            {
                "$set": {
                    "email": "david@example.com",
                    "role": "analyst",
                    "created_at": datetime.now()
                }
            },
            upsert=True
        )
        if result.upserted_id:
            print(f"Upserted new document with ID: {result.upserted_id}")
        """Demonstrate document updates."""
        print("\n=== Updating Documents ===")
        
        # Update one document
        result = self.collection.update_one(
            {"name": "Alice Johnson"},
            {"$set": {"age": 31, "profile.location": "San Jose, CA"}}
        )
        print(f"✓ Updated {result.modified_count} document(s)")
        
        # Add new field to document
        result = self.collection.update_one(
            {"name": "Bob Smith"},
            {"$set": {"last_login": datetime.now()}}
        )
        print(f"✓ Added last_login field to {result.modified_count} document(s)")
        
        # Update array element
        result = self.collection.update_one(
            {"name": "Alice Johnson", "projects.name": "ML Pipeline"},
            {"$set": {"projects.$.status": "completed"}}
        )
        print(f"✓ Updated project status for {result.modified_count} document(s)")
        
        # Add to array
        result = self.collection.update_one(
            {"name": "Carol Davis"},
            {"$push": {"certifications": "Docker Certified Associate"}}
        )
        print(f"✓ Added certification to {result.modified_count} document(s)")
    
    def aggregate_documents(self) -> None:
        """Demonstrate aggregation pipeline."""
        print("\n=== Aggregating Data ===")
        
        # Count documents by role
        pipeline = [
            {"$group": {"_id": "$role", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        print("Users by role:")
        for result in self.collection.aggregate(pipeline):
            print(f"  - {result['_id']}: {result['count']}")
        
        # Average age (where age exists)
        pipeline = [
            {"$match": {"age": {"$exists": True}}},
            {"$group": {"_id": None, "avg_age": {"$avg": "$age"}}}
        ]
        
        for result in self.collection.aggregate(pipeline):
            print(f"\nAverage age: {result['avg_age']:.1f}")
        """Demonstrate aggregation pipeline."""
        print("\n=== Aggregation Examples ===")
        
        # Group by age range
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$cond": [
                            {"$lt": ["$age", 30]},
                            "Under 30",
                            "30 and over"
                        ]
                    },
                    "count": {"$sum": 1},
                    "avg_age": {"$avg": "$age"}
                }
            }
        ]
        
        print("Users grouped by age range:")
        for result in self.collection.aggregate(pipeline):
            print(f"  - {result['_id']}: {result['count']} users, avg age: {result['avg_age']:.1f}")
        
        # Count interests
        pipeline = [
            {"$unwind": "$profile.interests"},
            {"$group": {"_id": "$profile.interests", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        print("\nMost popular interests:")
        for result in self.collection.aggregate(pipeline):
            print(f"  - {result['_id']}: {result['count']} users")
    
    def delete_documents(self) -> None:
        """Demonstrate delete operations."""
        print("\n=== Deleting Documents ===")
        
        # Delete one document
        result = self.collection.delete_one({"name": "David Wilson"})
        print(f"Deleted {result.deleted_count} document(s)")
        
        # Delete many documents (uncomment to test)
        # result = self.collection.delete_many({"role": "manager"})
        # print(f"Deleted {result.deleted_count} manager(s)")
        """Demonstrate document deletion."""
        print("\n=== Deleting Documents ===")
        
        # Delete one document
        result = self.collection.delete_one({"name": "Bob Smith"})
        print(f"✓ Deleted {result.deleted_count} document(s)")
        
        # Show remaining documents
        print("Remaining users:")
        for user in self.collection.find({}, {"name": 1, "_id": 0}):
            print(f"  - {user['name']}")
    
    def demonstrate_indexes(self) -> None:
        """Demonstrate index creation and usage."""
        print("\n=== Creating Indexes ===")
        
        # Create single field index
        self.collection.create_index("email")
        print("Created index on 'email' field")
        
        # Create compound index
        self.collection.create_index([("role", 1), ("age", -1)])
        print("Created compound index on 'role' and 'age'")
        
        # List indexes
        print("Current indexes:")
        for index in self.collection.list_indexes():
            print(f"  - {index['name']}: {index.get('key', {})}")
        """Demonstrate index creation for performance."""
        print("\n=== Index Management ===")
        
        # Create single field index
        self.collection.create_index("email")
        print("✓ Created index on 'email' field")
        
        # Create compound index
        self.collection.create_index([("age", 1), ("profile.location", 1)])
        print("✓ Created compound index on 'age' and 'profile.location'")
        
        # Create text index for search
        self.collection.create_index([("name", "text"), ("profile.bio", "text")])
        print("✓ Created text index on 'name' and 'profile.bio'")
        
        # List all indexes
        print("Current indexes:")
        for index in self.collection.list_indexes():
            print(f"  - {index['name']}: {index['key']}")
    
    def demonstrate_text_search(self) -> None:
        """Demonstrate text search capabilities."""
        print("\n=== Text Search ===")
        
        # Create text index
        try:
            self.collection.create_index([("name", "text"), ("profile.bio", "text")])
            print("Created text index")
            
            # Perform text search
            results = list(self.collection.find({"$text": {"$search": "developer"}}))
            print(f"Found {len(results)} documents matching 'developer'")
            
        except Exception as e:
            print(f"Text search error (may already exist): {e}")
        """Demonstrate text search capabilities."""
        print("\n=== Text Search ===")
        
        # Search for text
        results = self.collection.find({"$text": {"$search": "data scientist"}})
        print("Search results for 'data scientist':")
        for user in results:
            print(f"  - {user['name']}: {user['profile']['bio']}")
    
    def cleanup(self) -> None:
        """Clean up - drop the collection."""
        print("\n=== Cleanup ===")
        self.collection.drop()
        print("Dropped collection")
        self.client.close()
        print("Closed database connection")
        """Clean up - drop the collection."""
        print("\n=== Cleanup ===")
        self.collection.drop()
        print("✓ Dropped collection")
        self.client.close()
        print("✓ Closed database connection")


def main():
    """Main function to run the MongoDB hello world example."""
    print("MongoDB Hello World - Document Store Model")
    print("=" * 50)
    
    try:
        # Initialize MongoDB connection
        mongo_db = MongoDBHelloWorld()
        
        # Run demonstrations
        mongo_db.insert_sample_documents()
        mongo_db.find_documents()
        mongo_db.update_documents()
        mongo_db.aggregate_documents()
        mongo_db.demonstrate_indexes()
        mongo_db.demonstrate_text_search()
        mongo_db.delete_documents()
        
        # Cleanup
        mongo_db.cleanup()
        
        print("\n✓ MongoDB Hello World completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure MongoDB is running on localhost:27017")
        print("Install pymongo: pip install pymongo")


if __name__ == "__main__":
    main()
