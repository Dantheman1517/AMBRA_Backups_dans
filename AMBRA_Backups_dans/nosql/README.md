# MongoDB Document Store Examples

This directory contains MongoDB hello world examples demonstrating the document store model.

## Files

### 1. `document_store_demo.py` 
**Run this first** - No dependencies required!

A standalone demonstration of MongoDB document store concepts that runs without requiring MongoDB installation. This shows:

- Flexible schema design
- Nested objects and arrays  
- Document relationships
- CRUD operations
- Query capabilities

```bash
python document_store_demo.py
```

### 2. `mongodb_hello_world.py`
Full MongoDB example with real database operations.

**Requirements:**
```bash
pip install -r requirements.txt
```

**Prerequisites:**
- MongoDB running on localhost:27017, OR
- MongoDB Atlas connection string

**Features demonstrated:**
- Real MongoDB CRUD operations
- Aggregation pipelines
- Index management
- Text search
- Complex queries with operators

```bash
python mongodb_hello_world.py
```

### 3. `requirements.txt`
Dependencies for the full MongoDB example.

## MongoDB Document Store Model Benefits

1. **Flexible Schema**: Documents can have different structures
2. **Rich Data Types**: Nested objects, arrays, dates, etc.
3. **Horizontal Scaling**: Designed for distributed systems
4. **Query Flexibility**: Search by any field or combination
5. **Aggregation**: Powerful data processing pipelines
6. **Indexing**: Performance optimization for queries

## Example Document Structure

```json
{
  "_id": "user_001",
  "name": "Dr. Sarah Wilson",
  "role": "radiologist", 
  "specialties": ["MRI", "CT", "Ultrasound"],
  "contact": {
    "email": "sarah.wilson@hospital.com",
    "phone": "+1-555-0123"
  },
  "certifications": [
    {"name": "Board Certified Radiologist", "year": 2015},
    {"name": "MRI Specialist", "year": 2018}
  ],
  "active": true,
  "_created_at": "2025-01-15T10:30:00"
}
```

## Getting Started

1. **Start with the demo** (no setup required):
   ```bash
   cd AMBRA_Backups_dans/nosql
   python document_store_demo.py
   ```

2. **Try the full MongoDB example**:
   ```bash
   # Install MongoDB locally or use MongoDB Atlas
   pip install -r requirements.txt
   python mongodb_hello_world.py
   ```

## MongoDB Installation Options

### Local Installation
- **macOS**: `brew install mongodb-community`
- **Ubuntu**: `sudo apt install mongodb`
- **Windows**: Download from MongoDB website

### Cloud Option
- **MongoDB Atlas**: Free cloud database at mongodb.com/atlas
- Update connection string in `mongodb_hello_world.py`

## Use Cases for Document Store Model

- **Content Management**: Articles, blogs, documentation
- **User Profiles**: Flexible user data with varying fields
- **Product Catalogs**: Items with different attributes
- **IoT Data**: Sensor readings with varying schemas
- **Medical Records**: Patient data with flexible structure
- **Social Media**: Posts, comments, user interactions
