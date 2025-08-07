"""
MongoDB Document Store Model - Demo Script
==========================================

This script demonstrates MongoDB document store concepts without requiring
an actual MongoDB connection. It shows the flexibility of document-based storage.

Run this to understand MongoDB document store concepts:
    python document_store_demo.py
"""

import json
from datetime import datetime
from typing import Dict, List, Any


class DocumentStoreDemo:
    """
    Simulates MongoDB document store operations to demonstrate concepts.
    """
    
    def __init__(self):
        """Initialize with empty document store."""
        self.documents = []
        self.indexes = {}
    
    def insert_document(self, document: Dict[str, Any]) -> str:
        """
        Insert a document into the store.
        
        Args:
            document: Dictionary representing the document
            
        Returns:
            Document ID
        """
        # Generate ID if not provided
        if '_id' not in document:
            document['_id'] = len(self.documents) + 1
        
        # Add timestamp
        document['_created_at'] = datetime.now().isoformat()
        
        self.documents.append(document)
        return str(document['_id'])
    
    def find_documents(self, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find documents matching the query.
        
        Args:
            query: Search criteria
            
        Returns:
            List of matching documents
        """
        if query is None:
            return self.documents
        
        results = []
        for doc in self.documents:
            if self._matches_query(doc, query):
                results.append(doc)
        return results
    
    def _matches_query(self, document: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if document matches query criteria."""
        for key, value in query.items():
            if key not in document:
                return False
            
            # Handle nested field queries (e.g., "profile.location")
            if '.' in key:
                nested_value = self._get_nested_value(document, key)
                if nested_value != value:
                    return False
            elif document[key] != value:
                return False
        
        return True
    
    def _get_nested_value(self, document: Dict[str, Any], key: str) -> Any:
        """Get value from nested document structure."""
        keys = key.split('.')
        value = document
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
    
    def update_document(self, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update documents matching query.
        
        Args:
            query: Search criteria
            update: Update operations
            
        Returns:
            Number of documents updated
        """
        updated_count = 0
        for doc in self.documents:
            if self._matches_query(doc, query):
                # Apply update operations
                if '$set' in update:
                    for key, value in update['$set'].items():
                        if '.' in key:
                            self._set_nested_value(doc, key, value)
                        else:
                            doc[key] = value
                
                if '$push' in update:
                    for key, value in update['$push'].items():
                        if key in doc and isinstance(doc[key], list):
                            doc[key].append(value)
                
                doc['_updated_at'] = datetime.now().isoformat()
                updated_count += 1
        
        return updated_count
    
    def _set_nested_value(self, document: Dict[str, Any], key: str, value: Any) -> None:
        """Set value in nested document structure."""
        keys = key.split('.')
        current = document
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def delete_documents(self, query: Dict[str, Any]) -> int:
        """
        Delete documents matching query.
        
        Args:
            query: Search criteria
            
        Returns:
            Number of documents deleted
        """
        original_count = len(self.documents)
        self.documents = [doc for doc in self.documents if not self._matches_query(doc, query)]
        return original_count - len(self.documents)
    
    def print_documents(self, documents: List[Dict[str, Any]] = None) -> None:
        """Print documents in a readable format."""
        if documents is None:
            documents = self.documents
        
        for doc in documents:
            print(json.dumps(doc, indent=2, default=str))
            print("-" * 40)


def demonstrate_document_store():
    """Demonstrate MongoDB document store concepts."""
    print("MongoDB Document Store Model Demonstration")
    print("=" * 50)
    
    # Initialize document store
    store = DocumentStoreDemo()
    
    print("\n1. INSERTING DOCUMENTS (Flexible Schema)")
    print("-" * 30)
    
    # Insert documents with different schemas - demonstrates flexibility
    user1 = {
        "_id": "user_001",
        "name": "Dr. Sarah Wilson",
        "role": "radiologist",
        "department": "Radiology",
        "specialties": ["MRI", "CT", "Ultrasound"],
        "contact": {
            "email": "sarah.wilson@hospital.com",
            "phone": "+1-555-0123"
        },
        "certifications": [
            {"name": "Board Certified Radiologist", "year": 2015},
            {"name": "MRI Specialist", "year": 2018}
        ],
        "active": True
    }
    
    user2 = {
        "_id": "user_002",
        "name": "John Smith",
        "role": "technician",
        "department": "Radiology",
        "skills": ["X-Ray", "CT Operation", "Patient Care"],
        "contact": {
            "email": "john.smith@hospital.com"
            # Note: No phone number - demonstrates schema flexibility
        },
        "shift": "night",
        "hire_date": "2020-03-15",
        "active": True
    }
    
    study1 = {
        "_id": "study_001",
        "patient_id": "PAT_001",
        "study_type": "MRI",
        "body_part": "Brain",
        "date": "2025-01-15",
        "radiologist": "user_001",
        "technician": "user_002",
        "findings": {
            "summary": "Normal brain anatomy",
            "details": "No acute findings. Normal brain parenchyma.",
            "recommendations": "No follow-up needed"
        },
        "images": ["img_001.dcm", "img_002.dcm", "img_003.dcm"],
        "status": "completed"
    }
    
    # Insert documents
    store.insert_document(user1)
    store.insert_document(user2)
    store.insert_document(study1)
    
    print(f"✓ Inserted {len(store.documents)} documents")
    
    print("\n2. QUERYING DOCUMENTS")
    print("-" * 20)
    
    # Find all radiologists
    radiologists = store.find_documents({"role": "radiologist"})
    print(f"Found {len(radiologists)} radiologist(s):")
    for doc in radiologists:
        print(f"  - {doc['name']} ({doc['department']})")
    
    # Find documents with nested field query
    mri_specialists = store.find_documents({"specialties": "MRI"})
    print(f"\nFound {len(mri_specialists)} MRI specialist(s):")
    for doc in mri_specialists:
        print(f"  - {doc['name']}")
    
    # Find studies by type
    mri_studies = store.find_documents({"study_type": "MRI"})
    print(f"\nFound {len(mri_studies)} MRI study/studies:")
    for doc in mri_studies:
        print(f"  - Study {doc['_id']}: {doc['body_part']} ({doc['date']})")
    
    print("\n3. UPDATING DOCUMENTS")
    print("-" * 20)
    
    # Update user information
    updated_count = store.update_document(
        {"name": "John Smith"},
        {"$set": {"contact.phone": "+1-555-0456", "experience_years": 5}}
    )
    print(f"✓ Updated {updated_count} document(s)")
    
    # Add new certification
    updated_count = store.update_document(
        {"name": "Dr. Sarah Wilson"},
        {"$push": {"certifications": {"name": "AI in Radiology", "year": 2024}}}
    )
    print(f"✓ Added certification to {updated_count} document(s)")
    
    print("\n4. DOCUMENT RELATIONSHIPS (References)")
    print("-" * 40)
    
    # Show how documents can reference each other
    studies = store.find_documents({"study_type": "MRI"})
    for study in studies:
        # Find radiologist who read the study
        radiologist = store.find_documents({"_id": study["radiologist"]})
        technician = store.find_documents({"_id": study["technician"]})
        
        print(f"Study {study['_id']}:")
        print(f"  - Type: {study['study_type']} ({study['body_part']})")
        print(f"  - Radiologist: {radiologist[0]['name'] if radiologist else 'Unknown'}")
        print(f"  - Technician: {technician[0]['name'] if technician else 'Unknown'}")
        print(f"  - Status: {study['status']}")
    
    print("\n5. AGGREGATION-LIKE OPERATIONS")
    print("-" * 30)
    
    # Count documents by type
    roles = {}
    for doc in store.documents:
        if 'role' in doc:
            role = doc['role']
            roles[role] = roles.get(role, 0) + 1
    
    print("Staff by role:")
    for role, count in roles.items():
        print(f"  - {role}: {count}")
    
    # Show document with all fields
    print("\n6. FULL DOCUMENT EXAMPLE (showing schema flexibility)")
    print("-" * 50)
    
    user_docs = store.find_documents({"name": "Dr. Sarah Wilson"})
    if user_docs:
        store.print_documents([user_docs[0]])
    
    print("\n7. CLEANUP")
    print("-" * 10)
    
    # Delete inactive users
    deleted_count = store.delete_documents({"active": False})
    print(f"✓ Deleted {deleted_count} inactive user(s)")
    
    print(f"✓ Final document count: {len(store.documents)}")
    
    print("\n" + "=" * 50)
    print("KEY MONGODB DOCUMENT STORE BENEFITS DEMONSTRATED:")
    print("1. ✓ Flexible Schema - Documents can have different fields")
    print("2. ✓ Nested Objects - Rich data structures within documents") 
    print("3. ✓ Arrays - Multiple values in single field")
    print("4. ✓ Document References - Relationships between documents")
    print("5. ✓ Dynamic Updates - Add/modify fields without schema changes")
    print("6. ✓ Query Flexibility - Search by any field or nested field")


if __name__ == "__main__":
    demonstrate_document_store()
