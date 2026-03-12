# import streamlit as st
# import os
# import json
# import tempfile
# import shutil
# from pathlib import Path
# import pandas as pd
# from datetime import datetime
# import traceback

# # Import your existing modules
# import sys
# sys.path.append('src')

# try:
#     from src.tender_engineer_crew.crew import TenderEngineerCrew
#     from src.tender_engineer_crew.tools.custom_tool import (
#         match_tender_items_to_vendors, 
#         initialize_connections,
#         check_embeddings_exist,
#         create_embeddings_from_mongodb,
#         test_embeddings
#     )
#     from src.tender_engineer_crew.main import (
#         extract_text_from_pdf,
#         is_pdf_scanned,
#         extract_text_from_scanned_pdf,
#         extract_text_from_image,
#         extract_text_from_word,
#         save_clean_text_to_file,
#         sanitize_text
#     )
# except ImportError as e:
#     st.error(f"Error importing modules: {e}")
#     st.stop()

# # Configure Streamlit page
# st.set_page_config(
#     page_title="🏗️ Tender Engineer Crew",
#     page_icon="🏗️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for better styling
# st.markdown("""
# <style>
#     .main-header {
#         text-align: center;
#         padding: 2rem 0;
#         background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         border-radius: 10px;
#         margin-bottom: 2rem;
#     }
#     .status-box {
#         padding: 1rem;
#         border-radius: 10px;
#         margin: 1rem 0;
#     }
#     .success-box {
#         background-color: #d4edda;
#         border-left: 5px solid #28a745;
#     }
#     .error-box {
#         background-color: #f8d7da;
#         border-left: 5px solid #dc3545;
#     }
#     .info-box {
#         background-color: #d1ecf1;
#         border-left: 5px solid #17a2b8;
#     }
#     .warning-box {
#         background-color: #fff3cd;
#         border-left: 5px solid #ffc107;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Main header
# st.markdown("""
# <div class="main-header">
#     <h1>🏗️ Tender Engineer Crew</h1>
#     <p>AI-Powered Tender Processing & Vendor Matching System</p>
# </div>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'processing_complete' not in st.session_state:
#     st.session_state.processing_complete = False
# if 'tender_data' not in st.session_state:
#     st.session_state.tender_data = None
# if 'vendor_matches' not in st.session_state:
#     st.session_state.vendor_matches = None
# if 'embeddings_ready' not in st.session_state:
#     st.session_state.embeddings_ready = False

# # Sidebar for system status and controls
# with st.sidebar:
#     st.header("🔧 System Status")
    
#     # Initialize connections
#     with st.spinner("Initializing connections..."):
#         try:
#             initialize_connections()
#             st.success("✅ Connections initialized")
#         except Exception as e:
#             st.error(f"❌ Connection error: {e}")
    
#     # Check embeddings status
#     embeddings_exist = check_embeddings_exist()
#     if embeddings_exist:
#         st.success("✅ Embeddings ready")
#         st.session_state.embeddings_ready = True
#     else:
#         st.warning("⚠️ No embeddings found")
#         if st.button("🚀 Create Embeddings"):
#             with st.spinner("Creating embeddings from MongoDB..."):
#                 try:
#                     success = create_embeddings_from_mongodb()
#                     if success:
#                         st.success("✅ Embeddings created successfully!")
#                         st.session_state.embeddings_ready = True
#                         st.rerun()
#                     else:
#                         st.error("❌ Failed to create embeddings")
#                 except Exception as e:
#                     st.error(f"❌ Error creating embeddings: {e}")
    
#     # Test embeddings
#     if st.session_state.embeddings_ready:
#         st.subheader("🧪 Test Embeddings")
#         test_query = st.text_input("Test query:", value="steel pipes")
#         if st.button("Test Search"):
#             with st.spinner("Testing embeddings..."):
#                 try:
#                     results = test_embeddings(test_query, top_k=3)
#                     if results:
#                         st.success("✅ Test successful!")
#                     else:
#                         st.warning("⚠️ No results found")
#                 except Exception as e:
#                     st.error(f"❌ Test failed: {e}")

# # Main content area
# col1, col2 = st.columns([1, 1])

# with col1:
#     st.header("📄 Upload Tender Document")
    
#     uploaded_file = st.file_uploader(
#         "Choose a tender document",
#         type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
#         help="Upload PDF, image, or Word document containing tender information"
#     )
    
#     if uploaded_file is not None:
#         # Display file info
#         st.info(f"📁 **File:** {uploaded_file.name}")
#         st.info(f"📊 **Size:** {uploaded_file.size / 1024:.1f} KB")
#         st.info(f"📋 **Type:** {uploaded_file.type}")
        
#         # Process button
#         if st.button("🚀 Process Tender Document", type="primary"):
#             if not st.session_state.embeddings_ready:
#                 st.error("❌ Embeddings not ready. Please create embeddings first using the sidebar.")
#                 st.stop()
            
#             # Create progress bar
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             try:
#                 # Step 1: Save uploaded file
#                 status_text.text("📥 Saving uploaded file...")
#                 progress_bar.progress(10)
                
#                 # Create temporary file
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
#                     tmp_file.write(uploaded_file.getvalue())
#                     temp_file_path = tmp_file.name
                
#                 # Step 2: Extract text
#                 status_text.text("🔍 Extracting text from document...")
#                 progress_bar.progress(20)
                
#                 ext = os.path.splitext(uploaded_file.name)[-1].lower()
                
#                 if ext == ".pdf":
#                     if is_pdf_scanned(temp_file_path):
#                         status_text.text("🔍 Processing scanned PDF with OCR...")
#                         extracted_text = extract_text_from_scanned_pdf(temp_file_path)
#                     else:
#                         extracted_text = extract_text_from_pdf(temp_file_path)
#                 elif ext in [".png", ".jpg", ".jpeg"]:
#                     status_text.text("🖼️ Processing image with OCR...")
#                     extracted_text = extract_text_from_image(temp_file_path)
#                 elif ext in [".doc", ".docx"]:
#                     extracted_text = extract_text_from_word(temp_file_path)
#                 else:
#                     st.error("❌ Unsupported file type")
#                     st.stop()
                
#                 # Save extracted text
#                 os.makedirs("input", exist_ok=True)
#                 txt_path = "input/temp_tender_text.txt"
#                 save_clean_text_to_file(extracted_text, txt_path)
                
#                 progress_bar.progress(30)
                
#                 # Step 3: Process with CrewAI
#                 status_text.text("🤖 Processing with AI agents...")
#                 progress_bar.progress(40)
                
#                 inputs = {"file_path": txt_path}
#                 crew_result = TenderEngineerCrew().crew().kickoff(inputs=inputs)
                
#                 progress_bar.progress(70)
                
#                 # Step 4: Load processed data
#                 status_text.text("📊 Loading processed data...")
                
#                 tender_data_path = "output/tender_data.json"
#                 if os.path.exists(tender_data_path):
#                     with open(tender_data_path, 'r', encoding='utf-8') as f:
#                         content = f.read().strip()
#                         if content.startswith("```json"):
#                             content = content[7:]
#                         if content.endswith("```"):
#                             content = content[:-3]
#                         content = content.strip()
#                         st.session_state.tender_data = json.loads(content)
                
#                 progress_bar.progress(80)
                
#                 # Step 5: Match vendors
#                 status_text.text("🎯 Matching vendors...")
                
#                 vendor_matches = match_tender_items_to_vendors(tender_data_path, top_k=5)
#                 st.session_state.vendor_matches = vendor_matches
                
#                 progress_bar.progress(100)
#                 status_text.text("✅ Processing complete!")
                
#                 st.session_state.processing_complete = True
                
#                 # Cleanup
#                 os.unlink(temp_file_path)
                
#                 st.success("🎉 Tender processing completed successfully!")
                
#             except Exception as e:
#                 st.error(f"❌ Error during processing: {str(e)}")
#                 st.error(f"**Traceback:** {traceback.format_exc()}")
                
#                 # Cleanup on error
#                 if 'temp_file_path' in locals():
#                     try:
#                         os.unlink(temp_file_path)
#                     except:
#                         pass

# with col2:
#     st.header("📋 Processing Results")
    
#     if st.session_state.processing_complete and st.session_state.tender_data:
        
#         # Display tender summary
#         st.subheader("📊 Tender Summary")
#         tender_info = st.session_state.tender_data
        
#         col_a, col_b = st.columns(2)
#         with col_a:
#             st.metric("Company", tender_info.get('company_name', 'N/A'))
#             st.metric("Industry", tender_info.get('industry', 'N/A'))
#             st.metric("Total Items", len(tender_info.get('items', [])))
            
#         with col_b:
#             st.metric("Title", tender_info.get('title', 'N/A'))
#             st.metric("Product Type", tender_info.get('product_type', 'N/A'))
#             st.metric("Location", tender_info.get('location', 'N/A'))
        
#         # Display items in a table
#         st.subheader("📦 Tender Items")
#         if tender_info.get('items'):
#             items_df = pd.DataFrame(tender_info['items'])
#             st.dataframe(items_df, use_container_width=True)
        
#         # Display vendor matches
#         if st.session_state.vendor_matches:
#             st.subheader("🎯 Vendor Matches")
            
#             matches = st.session_state.vendor_matches.get('matches', [])
            
#             for match in matches:
#                 item_name = match.get('item', 'Unknown Item')
#                 vendors = match.get('top_vendors', [])
                
#                 with st.expander(f"🔧 **{item_name}** - {len(vendors)} vendor(s) found"):
#                     if vendors:
#                         for i, vendor in enumerate(vendors, 1):
#                             col_vendor, col_contact = st.columns([2, 1])
                            
#                             with col_vendor:
#                                 st.markdown(f"**{i}. {vendor.get('companyName', 'Unknown')}**")
#                                 st.markdown(f"*Segment:* {vendor.get('segment', 'N/A')}")
#                                 st.markdown(f"*Product:* {vendor.get('product_name', 'N/A')}")
#                                 st.markdown(f"*Service:* {vendor.get('service_name', 'N/A')}")
#                                 if vendor.get('description'):
#                                     st.markdown(f"*Description:* {vendor['description'][:100]}...")
                            
#                             with col_contact:
#                                 if vendor.get('contact_email'):
#                                     st.markdown(f"📧 {vendor['contact_email']}")
#                                 if vendor.get('phone'):
#                                     st.markdown(f"📞 {vendor['phone']}")
                            
#                             st.divider()
#                     else:
#                         st.warning("No vendors found for this item")
    
#     else:
#         st.info("👆 Upload and process a tender document to see results here")

# # Download section
# if st.session_state.processing_complete:
#     st.header("💾 Download Results")
    
#     col_dl1, col_dl2 = st.columns(2)
    
#     with col_dl1:
#         # Download structured tender data
#         if st.session_state.tender_data:
#             tender_json = json.dumps(st.session_state.tender_data, indent=2)
#             st.download_button(
#                 label="📄 Download Tender Data (JSON)",
#                 data=tender_json,
#                 file_name=f"tender_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#                 mime="application/json"
#             )
    
#     with col_dl2:
#         # Download vendor matches
#         if st.session_state.vendor_matches:
#             matches_json = json.dumps(st.session_state.vendor_matches, indent=2)
#             st.download_button(
#                 label="🎯 Download Vendor Matches (JSON)",
#                 data=matches_json,
#                 file_name=f"vendor_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#                 mime="application/json"
#             )

# # Footer
# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; color: #666;'>
#     <p>🏗️ Tender Engineer Crew - AI-Powered Tender Processing & Vendor Matching</p>
#     <p>Built with Streamlit, CrewAI, and MongoDB</p>
# </div>
# """, unsafe_allow_html=True)


#--------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------

import streamlit as st
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
import traceback

# Import your existing modules
import sys
sys.path.append('src')

try:
    from src.tender_engineer_crew.crew import TenderEngineerCrew
    from src.tender_engineer_crew.tools.custom_tool import (
        match_tender_items_to_vendors, 
        initialize_connections,
        check_embeddings_exist,
        create_embeddings_from_mongodb,
        test_embeddings
    )
    from src.tender_engineer_crew.tools.mongodb_utils import (
        TenderMetadataManager,
        test_mongodb_connection
    )
    from src.tender_engineer_crew.tools.s3_utils import (
        upload_tender_to_s3,
        test_s3_connection
    )
    from src.tender_engineer_crew.main import (
        extract_text_from_pdf,
        is_pdf_scanned,
        extract_text_from_scanned_pdf,
        extract_text_from_image,
        extract_text_from_word,
        save_clean_text_to_file,
        sanitize_text,
        get_file_info
    )
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="🗃️ Tender Admin Panel",
    page_icon="🗃️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for admin panel styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .admin-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-align: center;
        display: inline-block;
    }
    .status-completed { background-color: #d4edda; color: #155724; }
    .status-processing { background-color: #fff3cd; color: #856404; }
    .status-failed { background-color: #f8d7da; color: #721c24; }
    .status-uploaded { background-color: #d1ecf1; color: #0c5460; }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .vendor-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .tender-header {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_tender' not in st.session_state:
    st.session_state.selected_tender = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'  # 'dashboard' or 'tender_detail'
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'metadata_manager' not in st.session_state:
    try:
        st.session_state.metadata_manager = TenderMetadataManager()
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()

def get_status_badge(status):
    """Generate HTML badge for tender status"""
    status_classes = {
        'completed': 'status-completed',
        'processing': 'status-processing', 
        'failed': 'status-failed',
        'uploaded': 'status-uploaded'
    }
    class_name = status_classes.get(status.lower(), 'status-uploaded')
    return f'<span class="{class_name} status-badge">{status.upper()}</span>'

def format_datetime(dt_string):
    """Format datetime for display"""
    try:
        if isinstance(dt_string, str):
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            dt = dt_string
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt_string)

def send_tender_details_to_vendor(vendor_info, tender_data, item_name):
    """Function to handle sending tender details to vendor"""
    # This would typically integrate with email service
    # For demo, we'll show a success message
    
    vendor_name = vendor_info.get('companyName', 'Unknown')
    vendor_email = vendor_info.get('contact_email', 'No email')
    
    # Create tender summary for vendor
    tender_summary = {
        "tender_title": tender_data.get('title', 'N/A'),
        "company": tender_data.get('company_name', 'N/A'),
        "item_requested": item_name,
        "contact_person": tender_data.get('contact_person', 'N/A'),
        "email": tender_data.get('email', 'N/A'),
        "location": tender_data.get('location', 'N/A')
    }
    
    return vendor_email, tender_summary

def dashboard_view():
    """Main dashboard view showing all tenders"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🗃️ Tender Management Admin Panel</h1>
        <p>Manage tender processing and vendor matching operations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # System status and quick actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add New Tender", type="primary", use_container_width=True):
            st.session_state.view_mode = 'add_tender'
            st.rerun()
    
    with col2:
        # System status
        try:
            initialize_connections()
            embeddings_ready = check_embeddings_exist()
            if embeddings_ready:
                st.success("✅ System Ready", icon="✅")
            else:
                st.error("❌ Embeddings Missing", icon="❌")
        except:
            st.error("❌ System Error", icon="❌")
    
    with col3:
        # Quick stats
        try:
            stats = st.session_state.metadata_manager.get_processing_statistics()
            total = stats.get('total_documents', 0)
            st.info(f"📊 Total Tenders: {total}", icon="📊")
        except:
            st.info("📊 Total Tenders: 0", icon="📊")
    
    with col4:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Tender listing table
    st.subheader("📋 All Processed Tenders")
    
    try:
        # Get tender documents from MongoDB
        documents = st.session_state.metadata_manager.list_tender_documents(limit=50)
        
        if documents:
            # Create a more detailed table
            table_data = []
            for doc in documents:
                table_data.append({
                    "ID": str(doc['_id'])[:8] + "...",
                    "Filename": doc.get('original_filename', 'N/A'),
                    "Status": doc.get('processing_status', 'unknown'),
                    "Created": format_datetime(doc.get('created_at', 'N/A')),
                    "Company": doc.get('tender_data', {}).get('company_name', 'N/A') if doc.get('tender_data') else 'N/A',
                    "Items": len(doc.get('tender_data', {}).get('items', [])) if doc.get('tender_data') else 0,
                    "Vendors": len(doc.get('vendor_matches', {}).get('matches', [])) if doc.get('vendor_matches') else 0,
                    "Full_ID": str(doc['_id'])  # Hidden field for reference
                })
            
            df = pd.DataFrame(table_data)
            
            # Display table with custom styling
            for idx, row in df.iterrows():
                with st.container():
                    col_a, col_b, col_c, col_d, col_e = st.columns([2, 2, 1, 2, 1])
                    
                    with col_a:
                        st.write(f"**{row['Filename']}**")
                        st.caption(f"ID: {row['ID']}")
                    
                    with col_b:
                        st.write(f"Company: {row['Company']}")
                        st.caption(f"Created: {row['Created']}")
                    
                    with col_c:
                        st.markdown(get_status_badge(row['Status']), unsafe_allow_html=True)
                    
                    with col_d:
                        st.write(f"Items: {row['Items']} | Vendors: {row['Vendors']}")
                    
                    with col_e:
                        if st.button("👁️ View Details", key=f"view_{idx}", use_container_width=True):
                            st.session_state.selected_tender = row['Full_ID']
                            st.session_state.view_mode = 'tender_detail'
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("📝 No tender documents found. Start by adding a new tender!")
            
    except Exception as e:
        st.error(f"Error loading tender data: {e}")

def add_tender_view():
    """View for adding and processing new tenders"""
    
    st.markdown("""
    <div class="tender-header">
        <h2>➕ Add New Tender Document</h2>
        <p>Upload and process a new tender document</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.view_mode = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    
    # Check system readiness
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 System Status")
        
        # MongoDB status
        try:
            test_mongodb_connection()
            st.success("✅ MongoDB Connected")
        except:
            st.error("❌ MongoDB Connection Failed")
        
        # S3 status  
        try:
            test_s3_connection()
            st.success("✅ S3 Storage Ready")
        except:
            st.error("❌ S3 Storage Not Available")
        
        # Embeddings status
        try:
            embeddings_ready = check_embeddings_exist()
            if embeddings_ready:
                st.success("✅ Vendor Embeddings Ready")
            else:
                st.warning("⚠️ Vendor Embeddings Missing")
                if st.button("🚀 Create Embeddings Now"):
                    with st.spinner("Creating embeddings..."):
                        try:
                            success = create_embeddings_from_mongodb()
                            if success:
                                st.success("✅ Embeddings created!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to create embeddings")
                        except Exception as e:
                            st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"❌ Embeddings Check Failed: {e}")
    
    with col2:
        st.subheader("📄 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a tender document",
            type=['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
            help="Upload PDF, image, or Word document containing tender information"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"📄 **File:** {uploaded_file.name}")
            st.info(f"📊 **Size:** {uploaded_file.size / 1024:.1f} KB")
            st.info(f"📋 **Type:** {uploaded_file.type}")
            
            # Process button
            if st.button("🚀 Process Tender Document", type="primary", use_container_width=True):
                process_new_tender(uploaded_file)

def process_new_tender(uploaded_file):
    """Process the uploaded tender document"""
    
    # Create progress tracking
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Save and upload to S3
            status_text.text("📤 Uploading to S3...")
            progress_bar.progress(10)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name
            
            # Get file info and upload to S3
            file_info = get_file_info(temp_file_path)
            file_info['original_filename'] = uploaded_file.name
            
            s3_info = upload_tender_to_s3(temp_file_path, uploaded_file.name)
            if not s3_info:
                st.error("❌ Failed to upload to S3")
                return
            
            progress_bar.progress(20)
            
            # Step 2: Save metadata to MongoDB
            status_text.text("💾 Saving metadata...")
            document_id = st.session_state.metadata_manager.save_tender_metadata(file_info, s3_info, "processing")
            if not document_id:
                st.error("❌ Failed to save metadata")
                return
                
            progress_bar.progress(30)
            
            # Step 3: Extract text
            status_text.text("📝 Extracting text from document...")
            
            ext = os.path.splitext(uploaded_file.name)[-1].lower()
            
            if ext == ".pdf":
                if is_pdf_scanned(temp_file_path):
                    status_text.text("🔍 Processing scanned PDF with OCR...")
                    extracted_text = extract_text_from_scanned_pdf(temp_file_path)
                else:
                    extracted_text = extract_text_from_pdf(temp_file_path)
            elif ext in [".png", ".jpg", ".jpeg"]:
                status_text.text("🖼️ Processing image with OCR...")
                extracted_text = extract_text_from_image(temp_file_path)
            elif ext in [".doc", ".docx"]:
                extracted_text = extract_text_from_word(temp_file_path)
            else:
                st.error("❌ Unsupported file type")
                return
            
            # Save extracted text
            os.makedirs("input", exist_ok=True)
            txt_path = "input/temp_tender_text.txt"
            save_clean_text_to_file(extracted_text, txt_path)
            
            progress_bar.progress(40)
            
            # Step 4: Process with CrewAI
            status_text.text("🤖 Processing with AI agents...")
            
            inputs = {"file_path": txt_path}
            crew_result = TenderEngineerCrew().crew().kickoff(inputs=inputs)
            
            progress_bar.progress(70)
            
            # Step 5: Load and save processing results
            status_text.text("📊 Loading processed data...")
            
            tender_data = None
            validation_results = None
            
            # Load tender data
            tender_data_path = "output/tender_data.json"
            if os.path.exists(tender_data_path):
                with open(tender_data_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    tender_data = json.loads(content)
            
            progress_bar.progress(80)
            
            # Step 6: Match vendors
            status_text.text("🎯 Matching vendors...")
            
            vendor_matches = match_tender_items_to_vendors(tender_data_path, top_k=5)
            
            progress_bar.progress(90)
            
            # Step 7: Save all results to MongoDB
            status_text.text("💾 Saving final results...")
            
            success = st.session_state.metadata_manager.save_processing_results(
                document_id,
                tender_data=tender_data,
                validation_results=validation_results,
                vendor_matches=vendor_matches
            )
            
            if success:
                st.session_state.metadata_manager.update_processing_status(document_id, "completed")
            else:
                st.session_state.metadata_manager.update_processing_status(document_id, "failed")
            
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Cleanup
            os.unlink(temp_file_path)
            
            st.success("🎉 Tender processing completed successfully!")
            
            # Show option to view details
            if st.button("👁️ View Tender Details"):
                st.session_state.selected_tender = document_id
                st.session_state.view_mode = 'tender_detail'
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.error(f"**Details:** {traceback.format_exc()}")
            
            # Cleanup on error
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

def tender_detail_view():
    """Detailed view of a specific tender"""
    
    if not st.session_state.selected_tender:
        st.error("No tender selected")
        st.session_state.view_mode = 'dashboard'
        st.rerun()
        return
    
    # Get tender details
    try:
        tender_doc = st.session_state.metadata_manager.get_tender_metadata(st.session_state.selected_tender)
        if not tender_doc:
            st.error("Tender not found")
            st.session_state.view_mode = 'dashboard'
            st.rerun()
            return
    except Exception as e:
        st.error(f"Error loading tender: {e}")
        st.session_state.view_mode = 'dashboard'
        st.rerun()
        return
    
    # Header
    tender_data = tender_doc.get('tender_data', {})
    company_name = tender_data.get('company_name', 'Unknown Company')
    tender_title = tender_data.get('title', 'Untitled Tender')
    
    st.markdown(f"""
    <div class="tender-header">
        <h2>📋 {tender_title}</h2>
        <p><strong>Company:</strong> {company_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.view_mode = 'dashboard'
        st.rerun()
    
    # Tender overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(tender_data.get('items', []))}</h3>
            <p>Total Items</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        vendor_matches = tender_doc.get('vendor_matches', {})
        total_matches = sum(len(match.get('top_vendors', [])) for match in vendor_matches.get('matches', []))
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_matches}</h3>
            <p>Vendor Matches</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        status = tender_doc.get('processing_status', 'unknown')
        st.markdown(f"""
        <div class="metric-card">
            <h3>{status.upper()}</h3>
            <p>Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tender Information
    st.subheader("📄 Tender Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**Industry:** {tender_data.get('industry', 'N/A')}")
        st.write(f"**Product Type:** {tender_data.get('product_type', 'N/A')}")
        st.write(f"**Location:** {tender_data.get('location', 'N/A')}")
        st.write(f"**Contact Person:** {tender_data.get('contact_person', 'N/A')}")
    
    with info_col2:
        st.write(f"**Email:** {tender_data.get('email', 'N/A')}")
        st.write(f"**Phone:** {tender_data.get('phone', 'N/A')}")
        st.write(f"**Description:** {tender_data.get('description', 'N/A')}")
        st.write(f"**Created:** {format_datetime(tender_doc.get('created_at', 'N/A'))}")
    
    # Items and Vendor Matches
    st.subheader("🎯 Items & Vendor Matches")
    
    if vendor_matches and vendor_matches.get('matches'):
        for match in vendor_matches['matches']:
            item_name = match.get('item', 'Unknown Item')
            vendors = match.get('top_vendors', [])
            
            with st.expander(f"🔧 **{item_name}** - {len(vendors)} vendor(s) matched", expanded=True):
                
                # Find the original item details
                item_details = None
                for item in tender_data.get('items', []):
                    if item.get('item_name') == item_name:
                        item_details = item
                        break
                
                if item_details:
                    st.markdown("**Item Details:**")
                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        st.write(f"**Quantity:** {item_details.get('quantity', 'N/A')}")
                        st.write(f"**Unit:** {item_details.get('unit', 'N/A')}")
                    with detail_col2:
                        st.write(f"**Specification:** {item_details.get('specification', 'N/A')}")
                        st.write(f"**Delivery Date:** {item_details.get('delivery_date', 'N/A')}")
                
                st.markdown("---")
                st.markdown("**Matched Vendors:**")
                
                if vendors:
                    for i, vendor in enumerate(vendors, 1):
                        vendor_col1, vendor_col2, vendor_col3 = st.columns([3, 2, 1])
                        
                        with vendor_col1:
                            st.markdown(f"**{i}. {vendor.get('companyName', 'Unknown')}**")
                            st.markdown(f"*Segment:* {vendor.get('segment', 'N/A')}")
                            st.markdown(f"*Product:* {vendor.get('product_name', 'N/A')}")
                            if vendor.get('description'):
                                st.markdown(f"*Description:* {vendor['description'][:150]}...")
                        
                        with vendor_col2:
                            st.markdown("**Contact Information:**")
                            if vendor.get('contact_email'):
                                st.markdown(f"📧 {vendor['contact_email']}")
                            if vendor.get('phone'):
                                st.markdown(f"📞 {vendor['phone']}")
                        
                        with vendor_col3:
                            if st.button(f"📧 Send Details", key=f"send_{item_name}_{i}", type="primary"):
                                vendor_email, tender_summary = send_tender_details_to_vendor(vendor, tender_data, item_name)
                                
                                # Show success message with details
                                st.success(f"✅ Tender details sent to {vendor.get('companyName')}")
                                st.info(f"📧 Sent to: {vendor_email}")
                                
                                # Show what was sent
                                with st.expander("📋 Details Sent"):
                                    st.json(tender_summary)
                        
                        if i < len(vendors):
                            st.divider()
                else:
                    st.warning("No vendors found for this item")
    else:
        st.info("No vendor matches available for this tender.")

# Main app routing
def main():
    # Route to appropriate view
    if st.session_state.view_mode == 'dashboard':
        dashboard_view()
    elif st.session_state.view_mode == 'add_tender':
        add_tender_view()
    elif st.session_state.view_mode == 'tender_detail':
        tender_detail_view()
    else:
        st.session_state.view_mode = 'dashboard'
        st.rerun()

if __name__ == "__main__":
    main()

