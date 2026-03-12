# #main.py - 1
# import os
# import pdfplumber
# import easyocr
# from PIL import Image
# from pdf2image import convert_from_path
# import docx2txt
# import unicodedata

# from tender_engineer_crew.crew import TenderEngineerCrew
# from tender_engineer_crew.tools.custom_tool import match_tender_items_to_vendors

# reader = easyocr.Reader(['en'], gpu=False)

# def sanitize_text(text):
#     return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()

# def extract_text_from_pdf(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
#     return all_text.strip()

# def is_pdf_scanned(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             if page.extract_text():
#                 return False  # Has selectable text
#     return True

# def extract_text_from_scanned_pdf(pdf_path):
#     pages = convert_from_path(pdf_path)
#     text_lines = []
#     for page in pages:
#         lines = reader.readtext(page, detail=0, paragraph=True)
#         text_lines.extend(lines)
#     return "\n".join(text_lines)

# def extract_text_from_image(image_path):
#     lines = reader.readtext(image_path, detail=0, paragraph=True)
#     return "\n".join(lines)

# def extract_text_from_word(doc_path):
#     return docx2txt.process(doc_path).strip()

# def save_clean_text_to_file(text, txt_path):
#     cleaned = sanitize_text(text)
#     with open(txt_path, "w", encoding="utf-8") as f:
#         f.write(cleaned)

# def run():
#     file_path = input("Enter the full path to the tender file: ").strip()

#     if not os.path.isfile(file_path):
#         print("❌ Error: File not found at the specified path.")
#         return

#     ext = os.path.splitext(file_path)[-1].lower()
#     txt_path = "input/temp_tender_text.txt"
#     os.makedirs("input", exist_ok=True)

#     try:
#         # ADD THIS MISSING PART:
#         if ext == ".pdf":
#             if is_pdf_scanned(file_path):
#                 print("🔍 Detected scanned PDF. Running EasyOCR...")
#                 extracted_text = extract_text_from_scanned_pdf(file_path)
#             else:
#                 print("📄 Detected text-based PDF. Extracting text...")
#                 extracted_text = extract_text_from_pdf(file_path)

#         elif ext in [".png", ".jpg", ".jpeg"]:
#             print("🖼️ Detected image file. Running EasyOCR...")
#             extracted_text = extract_text_from_image(file_path)

#         elif ext in [".doc", ".docx"]:
#             print("📃 Detected Word document. Extracting text...")
#             extracted_text = extract_text_from_word(file_path)

#         else:
#             print("❌ Unsupported file type.")
#             return

#         save_clean_text_to_file(extracted_text, txt_path)
#         print(f"✅ Text extracted and saved at: {txt_path}")
#         # END OF MISSING PART

#         inputs = {
#             "file_path": txt_path
#         }

#         print("🚀 Starting the Tender Engineer Crew...\n")
#         result = TenderEngineerCrew().crew().kickoff(inputs=inputs)

#         # Automatically run vendor matching after CrewAI completes
#         print("\n🤖 Running semantic vendor matcher...")
#         try:
#             match_tender_items_to_vendors("output/tender_data.json", top_k=5)
#             print("✅ Vendor matching completed successfully!")
#         except Exception as e:
#             print(f"❌ Vendor matching failed: {e}")

#     except Exception as e:
#         print(f"❌ Error during processing: {e}")

# if __name__ == "__main__":
#     run()


#-------------------------------------------------------------------------------------------------------------------------------


# #main.py - 2
# import os
# import pdfplumber
# import easyocr
# from PIL import Image
# from pdf2image import convert_from_path
# import docx2txt
# import unicodedata
# import json

# from tender_engineer_crew.crew import TenderEngineerCrew
# from tender_engineer_crew.tools.custom_tool import match_tender_items_to_vendors

# # Import new utilities
# from tender_engineer_crew.tools.s3_utils import upload_tender_to_s3, test_s3_connection
# from tender_engineer_crew.tools.mongodb_utils import (
#     save_tender_upload_metadata, 
#     update_tender_status,
#     test_mongodb_connection,
#     TenderMetadataManager
# )

# reader = easyocr.Reader(['en'], gpu=False)

# def sanitize_text(text):
#     return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()

# def extract_text_from_pdf(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
#     return all_text.strip()

# def is_pdf_scanned(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             if page.extract_text():
#                 return False  # Has selectable text
#     return True

# def extract_text_from_scanned_pdf(pdf_path):
#     pages = convert_from_path(pdf_path)
#     text_lines = []
#     for page in pages:
#         lines = reader.readtext(page, detail=0, paragraph=True)
#         text_lines.extend(lines)
#     return "\n".join(text_lines)

# def extract_text_from_image(image_path):
#     lines = reader.readtext(image_path, detail=0, paragraph=True)
#     return "\n".join(lines)

# def extract_text_from_word(doc_path):
#     return docx2txt.process(doc_path).strip()

# def save_clean_text_to_file(text, txt_path):
#     cleaned = sanitize_text(text)
#     with open(txt_path, "w", encoding="utf-8") as f:
#         f.write(cleaned)

# def get_file_info(file_path):
#     """Extract file information for metadata"""
#     filename = os.path.basename(file_path)
#     file_size = os.path.getsize(file_path)
#     file_extension = os.path.splitext(filename)[1].lower()
    
#     # Determine file type
#     if file_extension == '.pdf':
#         file_type = 'PDF Document'
#     elif file_extension in ['.png', '.jpg', '.jpeg']:
#         file_type = 'Image Document'
#     elif file_extension in ['.doc', '.docx']:
#         file_type = 'Word Document'
#     else:
#         file_type = 'Unknown'
    
#     return {
#         "original_filename": filename,
#         "file_size": file_size,
#         "file_type": file_type,
#         "file_extension": file_extension
#     }

# def test_integrations():
#     """Test S3 and MongoDB connections before processing"""
#     print("🧪 Testing integrations...")
    
#     # Test S3 connection
#     print("📤 Testing S3 connection...")
#     s3_success = test_s3_connection()
    
#     # Test MongoDB connection
#     print("📊 Testing MongoDB connection...")
#     mongo_success = test_mongodb_connection()
    
#     if s3_success and mongo_success:
#         print("✅ All integrations working correctly!")
#         return True
#     else:
#         print("❌ Integration tests failed. Please check your configuration.")
#         return False

# def run():
#     file_path = input("Enter the full path to the tender file: ").strip()

#     if not os.path.isfile(file_path):
#         print("❌ Error: File not found at the specified path.")
#         return

#     # Test integrations first
#     if not test_integrations():
#         print("❌ Cannot proceed without working integrations.")
#         return

#     ext = os.path.splitext(file_path)[-1].lower()
#     txt_path = "input/temp_tender_text.txt"
#     os.makedirs("input", exist_ok=True)
    
#     # Initialize metadata manager
#     metadata_manager = TenderMetadataManager()
#     document_id = None

#     try:
#         print("\n" + "="*60)
#         print("🏗️ TENDER ENGINEER CREW - PROCESSING PIPELINE")
#         print("="*60)
        
#         # STEP 1: Upload to S3 and save metadata
#         print("\n📤 STEP 1: Uploading to S3 and saving metadata...")
        
#         # Get file information
#         file_info = get_file_info(file_path)
#         print(f"📁 File: {file_info['original_filename']} ({file_info['file_size']} bytes)")
        
#         # Upload to S3
#         s3_info = upload_tender_to_s3(file_path, file_info['original_filename'])
#         if not s3_info:
#             print("❌ Failed to upload file to S3. Aborting process.")
#             return
        
#         print(f"✅ Uploaded to S3: {s3_info['s3_url']}")
        
#         # Save metadata to MongoDB
#         document_id = save_tender_upload_metadata(file_info, s3_info)
#         if not document_id:
#             print("❌ Failed to save metadata to MongoDB. Aborting process.")
#             return
        
#         print(f"✅ Metadata saved with ID: {document_id}")
        
#         # STEP 2: Extract text from document
#         print("\n🔍 STEP 2: Extracting text from document...")
        
#         # Update status to processing
#         update_tender_status(document_id, "processing")
        
#         if ext == ".pdf":
#             if is_pdf_scanned(file_path):
#                 print("🔍 Detected scanned PDF. Running EasyOCR...")
#                 extracted_text = extract_text_from_scanned_pdf(file_path)
#             else:
#                 print("📄 Detected text-based PDF. Extracting text...")
#                 extracted_text = extract_text_from_pdf(file_path)

#         elif ext in [".png", ".jpg", ".jpeg"]:
#             print("🖼️ Detected image file. Running EasyOCR...")
#             extracted_text = extract_text_from_image(file_path)

#         elif ext in [".doc", ".docx"]:
#             print("📃 Detected Word document. Extracting text...")
#             extracted_text = extract_text_from_word(file_path)

#         else:
#             print("❌ Unsupported file type.")
#             update_tender_status(document_id, "failed")
#             return

#         save_clean_text_to_file(extracted_text, txt_path)
#         print(f"✅ Text extracted and saved at: {txt_path}")
        
#         # STEP 3: Process with CrewAI
#         print("\n🤖 STEP 3: Processing with AI agents...")
        
#         inputs = {
#             "file_path": txt_path
#         }

#         print("🚀 Starting the Tender Engineer Crew...\n")
#         result = TenderEngineerCrew().crew().kickoff(inputs=inputs)
        
#         print("✅ CrewAI processing completed!")
        
#         # STEP 4: Load and save processing results
#         print("\n📊 STEP 4: Saving processing results...")
        
#         tender_data = None
#         validation_results = None
        
#         # Load tender data
#         tender_data_path = "output/tender_data.json"
#         if os.path.exists(tender_data_path):
#             try:
#                 with open(tender_data_path, 'r', encoding='utf-8') as f:
#                     content = f.read().strip()
                    
#                     # Clean markdown formatting if present
#                     if content.startswith("```json"):
#                         content = content[7:]
#                     if content.endswith("```"):
#                         content = content[:-3]
#                     content = content.strip()
                    
#                     # Try to find JSON content within the text
#                     lines = content.split('\n')
#                     json_lines = []
#                     json_started = False
                    
#                     for line in lines:
#                         stripped_line = line.strip()
#                         if stripped_line.startswith('{') and not json_started:
#                             json_started = True
#                             json_lines.append(stripped_line)
#                         elif json_started:
#                             json_lines.append(stripped_line)
#                             if stripped_line.endswith('}') and stripped_line.count('}') >= stripped_line.count('{'):
#                                 break
                    
#                     if json_lines:
#                         json_content = '\n'.join(json_lines)
#                         tender_data = json.loads(json_content)
#                         print("✅ Tender data loaded")
#                     else:
#                         print("⚠️ No valid JSON found in tender data file")
#                         tender_data = None
                        
#             except json.JSONDecodeError as e:
#                 print(f"⚠️ Failed to parse tender data JSON: {e}")
#                 print("📝 Saving raw tender data for debugging...")
                
#                 # Save the problematic content for debugging
#                 debug_path = "output/tender_data_debug.txt"
#                 with open(debug_path, 'w', encoding='utf-8') as debug_file:
#                     debug_file.write(content)
#                 print(f"🔍 Raw content saved to: {debug_path}")
#                 tender_data = None
#             except Exception as e:
#                 print(f"⚠️ Error loading tender data: {e}")
#                 tender_data = None
        
#         # Load validation results
#         validation_path = "output/tender_validation.json"
#         if os.path.exists(validation_path):
#             try:
#                 with open(validation_path, 'r', encoding='utf-8') as f:
#                     content = f.read().strip()
                    
#                     # Debug: Print first few lines to see the content
#                     print(f"🔍 Validation file preview: {content[:200]}...")
                    
#                     # Clean markdown formatting if present
#                     if content.startswith("```json"):
#                         content = content[7:]
#                     if content.endswith("```"):
#                         content = content[:-3]
#                     content = content.strip()
                    
#                     # Try to find JSON content within the text
#                     lines = content.split('\n')
#                     json_lines = []
#                     json_started = False
                    
#                     for line in lines:
#                         stripped_line = line.strip()
#                         if stripped_line.startswith('{') and not json_started:
#                             json_started = True
#                             json_lines.append(stripped_line)
#                         elif json_started:
#                             json_lines.append(stripped_line)
#                             if stripped_line.endswith('}') and stripped_line.count('}') >= stripped_line.count('{'):
#                                 break
                    
#                     if json_lines:
#                         json_content = '\n'.join(json_lines)
#                         validation_results = json.loads(json_content)
#                         print("✅ Validation results loaded")
#                     else:
#                         print("⚠️ No valid JSON found in validation file, skipping...")
#                         validation_results = None
                        
#             except json.JSONDecodeError as e:
#                 print(f"⚠️ Failed to parse validation JSON: {e}")
#                 print("📝 Saving raw validation content for debugging...")
                
#                 # Save the problematic content for debugging
#                 debug_path = "output/validation_debug.txt"
#                 with open(debug_path, 'w', encoding='utf-8') as debug_file:
#                     debug_file.write(content)
#                 print(f"🔍 Raw content saved to: {debug_path}")
#                 validation_results = None
#             except Exception as e:
#                 print(f"⚠️ Error loading validation results: {e}")
#                 validation_results = None
        
#         # STEP 5: Match vendors
#         print("\n🎯 STEP 5: Running semantic vendor matcher...")
        
#         vendor_matches = None
#         try:
#             vendor_matches = match_tender_items_to_vendors("output/tender_data.json", top_k=5)
#             print("✅ Vendor matching completed successfully!")
#         except Exception as e:
#             print(f"❌ Vendor matching failed: {e}")
#             update_tender_status(document_id, "failed")
#             return
        
#         # STEP 6: Save all results to MongoDB
#         print("\n💾 STEP 6: Saving final results to database...")
        
#         success = metadata_manager.save_processing_results(
#             document_id,
#             tender_data=tender_data,
#             validation_results=validation_results,
#             vendor_matches=vendor_matches
#         )
        
#         if success:
#             print("✅ All processing results saved to database!")
#             update_tender_status(document_id, "completed")
#         else:
#             print("❌ Failed to save processing results")
#             update_tender_status(document_id, "failed")
        
#         # STEP 7: Display summary
#         print("\n" + "="*60)
#         print("🎉 PROCESSING COMPLETE!")
#         print("="*60)
#         print(f"📄 Document ID: {document_id}")
#         print(f"📤 S3 Location: {s3_info['s3_url']}")
#         print(f"📊 Tender Items: {len(tender_data.get('items', [])) if tender_data else 0}")
#         print(f"🎯 Vendor Matches: {len(vendor_matches.get('matches', [])) if vendor_matches else 0}")
#         print(f"📁 Local Files:")
#         print(f"   • Tender Data: output/tender_data.json")
#         print(f"   • Validation: output/tender_validation.json") 
#         print(f"   • Vendor Matches: output/tender_vendor_matches.json")
#         print("="*60)

#     except Exception as e:
#         print(f"❌ Error during processing: {e}")
#         if document_id:
#             update_tender_status(document_id, "failed")

# def run_with_existing_document():
#     """Alternative run mode for testing with existing S3 documents"""
#     print("🔍 Searching for existing tender documents...")
    
#     try:
#         metadata_manager = TenderMetadataManager()
#         documents = metadata_manager.list_tender_documents(limit=10)
        
#         if not documents:
#             print("📋 No existing documents found.")
#             return
        
#         print(f"\n📊 Found {len(documents)} recent documents:")
#         print("-" * 60)
        
#         for i, doc in enumerate(documents, 1):
#             filename = doc.get('original_filename', 'Unknown')
#             status = doc.get('processing_status', 'Unknown')
#             created = doc.get('created_at', 'Unknown')
#             print(f"{i}. {filename} | Status: {status} | Created: {created}")
        
#         print("-" * 60)
#         choice = input("Enter document number to reprocess (or 'q' to quit): ").strip()
        
#         if choice.lower() == 'q':
#             return
        
#         try:
#             doc_index = int(choice) - 1
#             if 0 <= doc_index < len(documents):
#                 selected_doc = documents[doc_index]
#                 document_id = selected_doc['_id']
#                 s3_key = selected_doc.get('s3_key')
                
#                 print(f"\n📄 Selected: {selected_doc['original_filename']}")
#                 print(f"🔄 Reprocessing document ID: {document_id}")
                
#                 # You could implement reprocessing logic here
#                 # For now, just show the document details
#                 print(f"📊 Document Details:")
#                 print(f"   • S3 URL: {selected_doc.get('s3_url', 'N/A')}")
#                 print(f"   • File Size: {selected_doc.get('file_size', 'N/A')} bytes")
#                 print(f"   • Status: {selected_doc.get('processing_status', 'N/A')}")
                
#             else:
#                 print("❌ Invalid selection.")
#         except ValueError:
#             print("❌ Please enter a valid number.")
            
#     except Exception as e:
#         print(f"❌ Error retrieving documents: {e}")

# def show_processing_stats():
#     """Show processing statistics"""
#     try:
#         metadata_manager = TenderMetadataManager()
#         stats = metadata_manager.get_processing_statistics()
        
#         print("\n📊 PROCESSING STATISTICS")
#         print("=" * 40)
#         print(f"Total Documents: {stats.get('total_documents', 0)}")
#         print("\nStatus Breakdown:")
        
#         status_breakdown = stats.get('status_breakdown', {})
#         for status, count in status_breakdown.items():
#             print(f"  • {status.title()}: {count}")
        
#         print("=" * 40)
        
#     except Exception as e:
#         print(f"❌ Error getting statistics: {e}")

# if __name__ == "__main__":
#     print("🏗️ Tender Engineer Crew - Enhanced with S3 & MongoDB")
#     print("=" * 55)
    
#     while True:
#         print("\nChoose an option:")
#         print("1. Process new tender document")
#         print("2. View existing documents") 
#         print("3. Show processing statistics")
#         print("4. Test integrations")
#         print("5. Exit")
        
#         choice = input("\nEnter your choice (1-5): ").strip()
        
#         if choice == "1":
#             run()
#         elif choice == "2":
#             run_with_existing_document()
#         elif choice == "3":
#             show_processing_stats()
#         elif choice == "4":
#             test_integrations()
#         elif choice == "5":
#             print("👋 Goodbye!")
#             break
#         else:
#             print("❌ Invalid choice. Please enter 1-5.")


#-------------------------------------------------------------------------------------------------------------------------------


#main.py - 3
import os
import pdfplumber
import easyocr
from PIL import Image
from pdf2image import convert_from_path
import docx2txt
import unicodedata
import json

from tender_engineer_crew.crew import TenderEngineerCrew
from tender_engineer_crew.tools.custom_tool import match_tender_items_to_vendors

# Import new utilities
from tender_engineer_crew.tools.s3_utils import upload_tender_to_s3, test_s3_connection
from tender_engineer_crew.tools.mongodb_utils import (
    save_tender_upload_metadata, 
    update_tender_status,
    test_mongodb_connection,
    TenderMetadataManager
)

reader = easyocr.Reader(['en'], gpu=False)

def sanitize_text(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").strip()

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return all_text.strip()

def is_pdf_scanned(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                return False  # Has selectable text
    return True

def extract_text_from_scanned_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    text_lines = []
    for page in pages:
        lines = reader.readtext(page, detail=0, paragraph=True)
        text_lines.extend(lines)
    return "\n".join(text_lines)

def extract_text_from_image(image_path):
    lines = reader.readtext(image_path, detail=0, paragraph=True)
    return "\n".join(lines)

def extract_text_from_word(doc_path):
    return docx2txt.process(doc_path).strip()

def save_clean_text_to_file(text, txt_path):
    cleaned = sanitize_text(text)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

def get_file_info(file_path):
    """Extract file information for metadata"""
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Determine file type
    if file_extension == '.pdf':
        file_type = 'PDF Document'
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        file_type = 'Image Document'
    elif file_extension in ['.doc', '.docx']:
        file_type = 'Word Document'
    else:
        file_type = 'Unknown'
    
    return {
        "original_filename": filename,
        "file_size": file_size,
        "file_type": file_type,
        "file_extension": file_extension
    }

def test_integrations():
    """Test S3 and MongoDB connections before processing"""
    print("🧪 Testing integrations...")
    
    # Test S3 connection
    print("📤 Testing S3 connection...")
    s3_success = test_s3_connection()
    
    # Test MongoDB connection
    print("📊 Testing MongoDB connection...")
    mongo_success = test_mongodb_connection()
    
    if s3_success and mongo_success:
        print("✅ All integrations working correctly!")
        return True
    else:
        print("❌ Integration tests failed. Please check your configuration.")
        return False

def run():
    file_path = input("Enter the full path to the tender file: ").strip()

    if not os.path.isfile(file_path):
        print("❌ Error: File not found at the specified path.")
        return

    # Test integrations first
    if not test_integrations():
        print("❌ Cannot proceed without working integrations.")
        return

    ext = os.path.splitext(file_path)[-1].lower()
    txt_path = "input/temp_tender_text.txt"
    os.makedirs("input", exist_ok=True)
    
    # Initialize metadata manager
    metadata_manager = TenderMetadataManager()
    document_id = None

    try:
        print("\n" + "="*60)
        print("🏗️ TENDER ENGINEER CREW - PROCESSING PIPELINE")
        print("="*60)
        
        # STEP 1: Upload to S3 and save metadata
        print("\n📤 STEP 1: Uploading to S3 and saving metadata...")

        # Get file information
        file_info = get_file_info(file_path)
        print(f"📁 File: {file_info['original_filename']} ({file_info['file_size']} bytes)")

        # Upload to S3
        s3_info = upload_tender_to_s3(file_path, file_info['original_filename'])
        if not s3_info:
            print("❌ Failed to upload file to S3. Aborting process.")
            return

        print(f"✅ Uploaded to S3: {s3_info['s3_url']}")

        # Save metadata to MongoDB
        document_id = save_tender_upload_metadata(file_info, s3_info)
        if not document_id:
            print("❌ Failed to save metadata to MongoDB. Aborting process.")
            return

        print(f"✅ Metadata saved with ID: {document_id}")
        
        # STEP 2: Extract text from document
        print("\n🔍 STEP 2: Extracting text from document...")
        
        # Update status to processing
        update_tender_status(document_id, "processing")
        
        if ext == ".pdf":
            if is_pdf_scanned(file_path):
                print("🔍 Detected scanned PDF. Running EasyOCR...")
                extracted_text = extract_text_from_scanned_pdf(file_path)
            else:
                print("📄 Detected text-based PDF. Extracting text...")
                extracted_text = extract_text_from_pdf(file_path)

        elif ext in [".png", ".jpg", ".jpeg"]:
            print("🖼️ Detected image file. Running EasyOCR...")
            extracted_text = extract_text_from_image(file_path)

        elif ext in [".doc", ".docx"]:
            print("📃 Detected Word document. Extracting text...")
            extracted_text = extract_text_from_word(file_path)

        else:
            print("❌ Unsupported file type.")
            update_tender_status(document_id, "failed")
            return

        save_clean_text_to_file(extracted_text, txt_path)
        print(f"✅ Text extracted and saved at: {txt_path}")
        
        # STEP 3: Process with CrewAI
        print("\n🤖 STEP 3: Processing with AI agents...")
        
        inputs = {
            "file_path": txt_path
        }

        print("🚀 Starting the Tender Engineer Crew...\n")
        result = TenderEngineerCrew().crew().kickoff(inputs=inputs)
        
        print("✅ CrewAI processing completed!")
        
        # STEP 4: Load and save processing results
        print("\n📊 STEP 4: Saving processing results...")
        
        tender_data = None
        validation_results = None
        
        # Load tender data
        tender_data_path = "output/tender_data.json"
        if os.path.exists(tender_data_path):
            try:
                with open(tender_data_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    # Clean markdown formatting if present
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Direct JSON parsing first (most files should work)
                    try:
                        tender_data = json.loads(content)
                        print("✅ Tender data loaded")
                    except json.JSONDecodeError:
                        # Fallback: Try to find JSON content within the text
                        lines = content.split('\n')
                        json_lines = []
                        json_started = False
                        brace_count = 0
                        
                        for line in lines:
                            stripped_line = line.strip()
                            if stripped_line.startswith('{') and not json_started:
                                json_started = True
                                json_lines.append(stripped_line)
                                brace_count += stripped_line.count('{') - stripped_line.count('}')
                            elif json_started:
                                json_lines.append(stripped_line)
                                brace_count += stripped_line.count('{') - stripped_line.count('}')
                                if brace_count <= 0:
                                    break
                        
                        if json_lines:
                            json_content = '\n'.join(json_lines)
                            tender_data = json.loads(json_content)
                            print("✅ Tender data loaded (fallback parsing)")
                        else:
                            print("⚠️ No valid JSON found in tender data file")
                            tender_data = None
                        
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse tender data JSON: {e}")
                print("📝 Saving raw tender data for debugging...")
                
                # Save the problematic content for debugging
                debug_path = "output/tender_data_debug.txt"
                with open(debug_path, 'w', encoding='utf-8') as debug_file:
                    debug_file.write(content)
                print(f"🔍 Raw content saved to: {debug_path}")
                tender_data = None
            except Exception as e:
                print(f"⚠️ Error loading tender data: {e}")
                tender_data = None
        
        # Load validation results
        validation_path = "output/tender_validation.json"
        if os.path.exists(validation_path):
            try:
                with open(validation_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    # Clean markdown formatting if present
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Direct JSON parsing first (most files should work)
                    try:
                        validation_results = json.loads(content)
                        print("✅ Validation results loaded")
                    except json.JSONDecodeError:
                        # Fallback: Try to find JSON content within the text
                        lines = content.split('\n')
                        json_lines = []
                        json_started = False
                        brace_count = 0
                        
                        for line in lines:
                            stripped_line = line.strip()
                            if stripped_line.startswith('{') and not json_started:
                                json_started = True
                                json_lines.append(stripped_line)
                                brace_count += stripped_line.count('{') - stripped_line.count('}')
                            elif json_started:
                                json_lines.append(stripped_line)
                                brace_count += stripped_line.count('{') - stripped_line.count('}')
                                if brace_count <= 0:
                                    break
                        
                        if json_lines:
                            json_content = '\n'.join(json_lines)
                            validation_results = json.loads(json_content)
                            print("✅ Validation results loaded (fallback parsing)")
                        else:
                            print("⚠️ No valid JSON found in validation file, skipping...")
                            validation_results = None
                        
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse validation JSON: {e}")
                print("📝 Saving raw validation content for debugging...")
                
                # Save the problematic content for debugging
                debug_path = "output/validation_debug.txt"
                with open(debug_path, 'w', encoding='utf-8') as debug_file:
                    debug_file.write(content)
                print(f"🔍 Raw content saved to: {debug_path}")
                validation_results = None
            except Exception as e:
                print(f"⚠️ Error loading validation results: {e}")
                validation_results = None
        
        # STEP 5: Match vendors
        print("\n🎯 STEP 5: Running semantic vendor matcher...")
        
        vendor_matches = None
        try:
            vendor_matches = match_tender_items_to_vendors("output/tender_data.json", top_k=5)
            print("✅ Vendor matching completed successfully!")
        except Exception as e:
            print(f"❌ Vendor matching failed: {e}")
            update_tender_status(document_id, "failed")
            return
        
        # STEP 6: Save all results to MongoDB
        print("\n💾 STEP 6: Saving final results to database...")
        
        success = metadata_manager.save_processing_results(
            document_id,
            tender_data=tender_data,
            validation_results=validation_results,
            vendor_matches=vendor_matches
        )
        
        if success:
            print("✅ All processing results saved to database!")
            update_tender_status(document_id, "completed")
        else:
            print("❌ Failed to save processing results")
            update_tender_status(document_id, "failed")
        
        # STEP 7: Display summary
        print("\n" + "="*60)
        print("🎉 PROCESSING COMPLETE!")
        print("="*60)
        print(f"📄 Document ID: {document_id}")
        print(f"📤 S3 Location: {s3_info['s3_url']}")
        
        # Display tender data summary if available
        if tender_data:
            items_count = len(tender_data.get('items', []))
            print(f"📊 Tender Items: {items_count}")
            print(f"🏢 Company: {tender_data.get('company_name', 'Not specified')}")
            print(f"📋 Title: {tender_data.get('title', 'N/A')}")
            print(f"🏭 Industry: {tender_data.get('industry', 'N/A')}")
        else:
            print(f"📊 Tender Items: Data parsing failed (check debug files)")
            
        print(f"🎯 Vendor Matches: {len(vendor_matches.get('matches', [])) if vendor_matches else 0}")
        
        # Display validation summary if available
        if validation_results:
            status = validation_results.get('status', 'Unknown')
            issues_count = len(validation_results.get('issues', []))
            print(f"✅ Validation: {status} ({issues_count} issues found)")
        else:
            print(f"⚠️ Validation: Data parsing failed (check debug files)")
            
        print(f"📁 Local Files:")
        print(f"   • Tender Data: output/tender_data.json")
        print(f"   • Validation: output/tender_validation.json") 
        print(f"   • Vendor Matches: output/tender_vendor_matches.json")
        print("="*60)

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        if document_id:
            update_tender_status(document_id, "failed")

def run_with_existing_document():
    """Alternative run mode for testing with existing S3 documents"""
    print("🔍 Searching for existing tender documents...")
    
    try:
        metadata_manager = TenderMetadataManager()
        documents = metadata_manager.list_tender_documents(limit=10)
        
        if not documents:
            print("📋 No existing documents found.")
            return
        
        print(f"\n📊 Found {len(documents)} recent documents:")
        print("-" * 60)
        
        for i, doc in enumerate(documents, 1):
            filename = doc.get('original_filename', 'Unknown')
            status = doc.get('processing_status', 'Unknown')
            created = doc.get('created_at', 'Unknown')
            print(f"{i}. {filename} | Status: {status} | Created: {created}")
        
        print("-" * 60)
        choice = input("Enter document number to reprocess (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            return
        
        try:
            doc_index = int(choice) - 1
            if 0 <= doc_index < len(documents):
                selected_doc = documents[doc_index]
                document_id = selected_doc['_id']
                s3_key = selected_doc.get('s3_key')
                
                print(f"\n📄 Selected: {selected_doc['original_filename']}")
                print(f"🔄 Reprocessing document ID: {document_id}")
                
                # You could implement reprocessing logic here
                # For now, just show the document details
                print(f"📊 Document Details:")
                print(f"   • S3 URL: {selected_doc.get('s3_url', 'N/A')}")
                print(f"   • File Size: {selected_doc.get('file_size', 'N/A')} bytes")
                print(f"   • Status: {selected_doc.get('processing_status', 'N/A')}")
                
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
            
    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")

def show_processing_stats():
    """Show processing statistics"""
    try:
        metadata_manager = TenderMetadataManager()
        stats = metadata_manager.get_processing_statistics()
        
        print("\n📊 PROCESSING STATISTICS")
        print("=" * 40)
        print(f"Total Documents: {stats.get('total_documents', 0)}")
        print("\nStatus Breakdown:")
        
        status_breakdown = stats.get('status_breakdown', {})
        for status, count in status_breakdown.items():
            print(f"  • {status.title()}: {count}")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

if __name__ == "__main__":
    print("🏗️ Tender Engineer Crew - Enhanced with S3 & MongoDB")
    print("=" * 55)
    
    while True:
        print("\nChoose an option:")
        print("1. Process new tender document")
        print("2. View existing documents") 
        print("3. Show processing statistics")
        print("4. Test integrations")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            run()
        elif choice == "2":
            run_with_existing_document()
        elif choice == "3":
            show_processing_stats()
        elif choice == "4":
            test_integrations()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")