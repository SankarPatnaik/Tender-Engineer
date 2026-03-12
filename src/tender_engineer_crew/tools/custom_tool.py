import os
import json
import logging
import chromadb
from typing import List, Dict, Optional
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- ENV CONFIG --- #
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")  # Default fallback

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- GLOBAL CONNECTIONS --- #
mongo_client = None
mongo_collection = None
chroma_client = None
collection = None
model = None

def initialize_connections():
    """Initialize all connections (MongoDB, ChromaDB, and embedding model)"""
    global mongo_client, mongo_collection, chroma_client, collection, model
    
    # Initialize embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logging.info("✅ Loaded embedding model")
    
    # Initialize MongoDB
    try:
        if MONGODB_URI:
            mongo_client = MongoClient(MONGODB_URI)
            mongo_collection = mongo_client[MONGODB_DB][MONGODB_COLLECTION]
            # Test connection
            mongo_client.admin.command('ping')
            logging.info("✅ Connected to MongoDB")
        else:
            logging.error("❌ MONGODB_URI not found in environment variables")
            mongo_collection = None
    except Exception as e:
        logging.error(f"❌ Error connecting to MongoDB: {e}")
        mongo_collection = None
    
    # Initialize ChromaDB
    try:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Try to get existing collection
        try:
            collection = chroma_client.get_collection(name="company_embeddings")
            count = collection.count()
            logging.info(f"✅ Connected to existing ChromaDB collection with {count} embeddings")
        except:
            collection = chroma_client.create_collection(name="company_embeddings")
            logging.info("✅ Created new ChromaDB collection")
            
    except Exception as e:
        logging.error(f"❌ Failed to initialize ChromaDB: {e}")
        chroma_client, collection = None, None

def check_embeddings_exist():
    """Check if embeddings exist in ChromaDB"""
    global collection
    
    if collection is None:
        return False
    
    try:
        count = collection.count()
        return count > 0
    except Exception as e:
        logging.error(f"❌ Error checking embeddings: {e}")
        return False

def ensure_embeddings_exist(auto_create=True):
    """Check if embeddings exist, and optionally create them if they don't"""
    global collection, mongo_collection, model
    
    if mongo_collection is None or collection is None:
        logging.error("❌ Required services not available")
        return False
    
    try:
        count = collection.count()
        if count > 0:
            logging.info(f"✅ Found {count} existing embeddings")
            return True
        else:
            if auto_create:
                logging.info("📊 No embeddings found, creating them now...")
                return create_embeddings_from_mongodb()
            else:
                logging.warning("⚠️ No embeddings found and auto_create is disabled")
                return False
    except Exception as e:
        logging.error(f"❌ Error checking embeddings: {e}")
        return False

def create_embeddings_from_mongodb(batch_size: int = 100):
    """Create embeddings for all vendors in MongoDB and store in ChromaDB"""
    global mongo_collection, collection, model
    
    if mongo_collection is None or collection is None or model is None:
        logging.error("❌ Required services not available")
        return False
    
    try:
        # Get total count
        total_companies = mongo_collection.count_documents({})
        logging.info(f"📊 Found {total_companies} companies in MongoDB")
        
        if total_companies == 0:
            logging.warning("⚠️ No companies found in MongoDB")
            return False
        
        # Reset collection for fresh embeddings
        try:
            chroma_client.delete_collection(name="company_embeddings")
            collection = chroma_client.create_collection(name="company_embeddings")
            logging.info("🔄 Reset ChromaDB collection")
        except:
            pass
        
        # Process in batches
        processed = 0
        batch_embeddings = []
        batch_metadatas = []
        batch_ids = []
        batch_docs = []
        
        for company in mongo_collection.find({}):
            try:
                company_name = company.get("companyName", "Unknown")
                segment = company.get("segment", "")
                product_name = company.get("product_name", "")
                service_name = company.get("service_name", "")
                description = company.get("description", "")
                
                # Create text for embedding
                text_to_embed = f"{company_name} {segment} {product_name} {service_name} {description}".strip()
                
                if not text_to_embed or text_to_embed == company_name:
                    logging.warning(f"⚠️ Skipping {company_name} - insufficient text")
                    continue
                
                # Create embedding
                embedding = model.encode(text_to_embed, convert_to_tensor=False).tolist()
                
                # Prepare batch data
                batch_embeddings.append(embedding)
                batch_metadatas.append({
                    "companyName": company_name,
                    "segment": segment,
                    "product_name": product_name,
                    "service_name": service_name,
                    "description": description
                })
                batch_ids.append(str(company.get("_id", f"company_{processed}")))
                batch_docs.append(text_to_embed)
                
                processed += 1
                
                # Process batch when full
                if len(batch_embeddings) >= batch_size:
                    collection.add(
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        documents=batch_docs
                    )
                    batch_embeddings.clear()
                    batch_metadatas.clear()
                    batch_ids.clear()
                    batch_docs.clear()
                    
                    logging.info(f"✅ Processed {processed}/{total_companies} companies")
            
            except Exception as e:
                logging.warning(f"⚠️ Error processing company {company.get('companyName', 'Unknown')}: {e}")
                continue
        
        # Process remaining batch
        if batch_embeddings:
            collection.add(
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids,
                documents=batch_docs
            )
        
        final_count = collection.count()
        logging.info(f"🎉 Successfully created embeddings for {final_count} companies")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating embeddings: {e}")
        return False

def recommend_companies(query: str, top_k: int = 5) -> List[Dict]:
    """
    Fetch top-K recommended companies based on a user query.
    
    :param query: The natural language query.
    :param top_k: Number of top matches to return.
    :return: List of company documents.
    """
    global mongo_collection, collection, model
    
    if not query.strip():
        logging.warning("⚠️ Empty query received.")
        return []

    # Ensure all services are available
    if mongo_collection is None or collection is None or model is None:
        logging.error("❌ Services not available")
        return []
    
    # Check if embeddings exist (don't auto-create during queries)
    if not check_embeddings_exist():
        logging.error("❌ No embeddings found. Please create embeddings first.")
        return []

    try:
        # Encode the query
        query_embedding = model.encode(query, convert_to_tensor=False).tolist()

        # Search in ChromaDB
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

        if not results or not results.get("metadatas") or not results["metadatas"][0]:
            logging.info("ℹ️ No companies matched the query.")
            return []

        # Extract matching company names
        matched_names = [meta["companyName"] for meta in results["metadatas"][0] if "companyName" in meta]

        if not matched_names:
            return []

        # Fetch full records from MongoDB
        matched_docs = list(mongo_collection.find({"companyName": {"$in": matched_names}}))

        # Sort to maintain match order
        matched_docs_sorted = sorted(matched_docs, key=lambda x: matched_names.index(x["companyName"]))

        return matched_docs_sorted

    except Exception as e:
        logging.error(f"❌ Error during recommendation: {e}")
        return []

def match_tender_items_to_vendors(tender_json_path: str, top_k: int = 5) -> Dict:
    """
    Match tender items to vendors using local embeddings
    Automatically creates embeddings if they don't exist (first-time setup)
    """
    global mongo_collection, collection
    
    if not os.path.exists(tender_json_path):
        raise FileNotFoundError(f"Tender JSON not found at: {tender_json_path}")

    with open(tender_json_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove markdown code block formatting
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]  # Remove ```json
    if content.endswith("```"):
        content = content[:-3]  # Remove ```
    content = content.strip()
    
    tender_data = json.loads(content)


    tender_id = tender_data.get("title", "TENDER-UNKNOWN")
    items = tender_data.get("items", [])

    result = {
        "tender_id": tender_id,
        "matches": []
    }

    # Initialize connections if not already done
    if mongo_collection is None or collection is None:
        print("🔧 Initializing connections...")
        initialize_connections()

    # Check if services are available
    if mongo_collection is None:
        logging.error("❌ MongoDB not available")
        print("❌ MongoDB not available")
        print("   - Check your .env file for correct MongoDB credentials")
        print("   - Required: MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION")
        return result

    if collection is None:
        logging.error("❌ ChromaDB not available")
        print("❌ ChromaDB not available")
        return result

    # Check if embeddings exist, create if needed (first-time setup)
    print("🔍 Checking embeddings...")
    if not check_embeddings_exist():
        print("📊 No embeddings found - this appears to be first-time setup.")
        print("🚀 Creating embeddings from MongoDB data...")
        
        if create_embeddings_from_mongodb():
            print("✅ Embeddings created successfully!")
        else:
            print("❌ Failed to create embeddings")
            print("   - Ensure MongoDB contains company data")
            print("   - Check MongoDB connection and credentials")
            return result

    # Get final count
    try:
        count = collection.count()
        print(f"✅ Ready with {count} company embeddings")
    except:
        print("❌ Error accessing embeddings")
        return result

    # Process each tender item
    for item in items:
        item_name = item.get("item_name", "").strip()
        spec = item.get("specification", "").strip()

        # Create search query
        query = f"{item_name} {spec}".strip()
        print(f"\n🔍 Matching vendors for item: '{item_name}'")

        # Get recommendations
        top_vendors = recommend_companies(query, top_k=top_k)

        # Clean result for output
        clean_vendors = []
        for v in top_vendors:
            clean_vendors.append({
                "companyName": v.get("companyName", "Unknown"),
                "segment": v.get("segment", ""),
                "product_name": v.get("product_name", ""),
                "service_name": v.get("service_name", ""),
                "description": v.get("description", ""),
                "contact_email": v.get("companyEmail", ""),
                "phone": v.get("phone", "")
            })

        if clean_vendors:
            print(f"✅ Top {len(clean_vendors)} vendors:")
            for idx, vendor in enumerate(clean_vendors, 1):
                print(f"{idx}. {vendor['companyName']} — {vendor['segment']}")
        else:
            print("⚠️ No vendors found for this item")

        result["matches"].append({
            "item": item_name,
            "top_vendors": clean_vendors
        })

    # Save result
    os.makedirs("output", exist_ok=True)
    output_path = "output/tender_vendor_matches.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n📦 Final vendor matches saved to: {output_path}")
    return result

def test_embeddings(query: str = "steel pipes", top_k: int = 3):
    """Test the embedding system with a sample query"""
    global mongo_collection, collection
    
    if mongo_collection is None or collection is None:
        initialize_connections()
    
    if not check_embeddings_exist():
        print("❌ No embeddings found!")
        print("   Use option 2 to create embeddings first.")
        return False
    
    print(f"🧪 Testing embeddings with query: '{query}'")
    results = recommend_companies(query, top_k=top_k)
    
    if results:
        print(f"✅ Found {len(results)} matches:")
        for i, company in enumerate(results, 1):
            print(f"  {i}. {company.get('companyName', 'Unknown')} - {company.get('segment', '')}")
        return True
    else:
        print("❌ No matches found")
        return False

def force_recreate_embeddings():
    """Force recreation of all embeddings"""
    global mongo_collection, collection
    
    if mongo_collection is None or collection is None:
        initialize_connections()
    
    print("🔄 Force recreating all embeddings...")
    success = create_embeddings_from_mongodb()
    
    if success:
        count = collection.count()
        print(f"✅ Successfully recreated {count} embeddings")
        
        # Test with a sample query
        test_embeddings()
    else:
        print("❌ Failed to recreate embeddings")
    
    return success

# Initialize connections when module is imported
initialize_connections()

# --- FOR TESTING AND MANUAL MANAGEMENT --- #
if __name__ == "__main__":
    print("🚀 Tender-to-Vendor Matcher - Manual Management")
    print("=" * 55)
    print("💡 Note: For normal usage, just run 'crewai run'")
    print("   This script handles first-time setup automatically!")
    print("=" * 55)
    
    while True:
        print("\nChoose an option:")
        print("1. Test embeddings with sample query")
        print("2. Force recreate all embeddings")
        print("3. Check current embedding count")
        print("4. Test tender matching (requires tender_data.json)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            if check_embeddings_exist():
                query = input("Enter test query (or press Enter for 'steel pipes'): ").strip()
                if not query:
                    query = "steel pipes"
                test_embeddings(query)
            else:
                print("❌ No embeddings found!")
                create = input("Create embeddings now? (y/N): ").strip().lower()
                if create in ['y', 'yes']:
                    if force_recreate_embeddings():
                        query = input("Enter test query (or press Enter for 'steel pipes'): ").strip()
                        if not query:
                            query = "steel pipes"
                        test_embeddings(query)
        
        elif choice == "2":
            if check_embeddings_exist():
                print("⚠️ Embeddings already exist!")
                recreate = input("Do you want to recreate them? (y/N): ").strip().lower()
                if recreate in ['y', 'yes']:
                    force_recreate_embeddings()
                else:
                    print("ℹ️ Keeping existing embeddings.")
            else:
                print("📊 No embeddings found. Creating new ones...")
                force_recreate_embeddings()
        
        elif choice == "3":
            if collection is not None:
                try:
                    count = collection.count()
                    print(f"📊 Current embedding count: {count}")
                    if count == 0:
                        print("   💡 Run 'crewai run' to automatically create embeddings")
                except Exception as e:
                    print(f"❌ Error checking count: {e}")
            else:
                print("❌ ChromaDB not available")
        
        elif choice == "4":
            tender_path = "output/tender_data.json"
            if os.path.exists(tender_path):
                print(f"📁 Testing with {tender_path}")
                match_tender_items_to_vendors(tender_path)
            else:
                print(f"❌ File not found: {tender_path}")
                print("   Run 'crewai run' first to process a tender document")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")