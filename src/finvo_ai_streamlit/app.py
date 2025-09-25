import streamlit as st
from pathlib import Path
import sys
import os
import httpx
import json
from typing import Optional

# Add the src directory to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
project_root = src_dir.parent
sys.path.append(str(src_dir))
sys.path.append(str(project_root))

# Configuration for API
API_BASE_URL = "http://localhost:8000"

def check_api_health() -> bool:
    """Check if the API is available and healthy."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False

def extract_invoice_via_api(file_bytes: bytes, filename: str) -> Optional[dict]:
    """Extract invoice data using the API endpoint."""
    try:
        with httpx.Client(timeout=60.0) as client:
            files = {"file": (filename, file_bytes)}
            data = {
                "extract_fuel_info": "true",
                "extract_line_items": "true"
            }
            
            response = client.post(
                f"{API_BASE_URL}/api/v1/extract/upload",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Try to parse JSON error response
                try:
                    error_data = response.json()
                    return error_data  # Return the structured error for proper handling
                except:
                    st.error(f"API Error {response.status_code}: {response.text}")
                    return None
                
    except httpx.TimeoutException:
        st.error("Request timed out. The API might be processing a large file.")
        return None
    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")
        st.error(f"Exception type: {type(e).__name__}")
        return None

# Check API availability on startup
API_AVAILABLE = check_api_health()

def main():
    # Page configuration
    st.set_page_config(
        page_title="Finvo AI Platform",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Main header with logo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Display logo centered
        logo_path = Path(__file__).parent.parent.parent / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=400)
        else:
            st.title("🤖 Finvo AI Platform")
    
    st.markdown("---")
    
    # Sidebar menu for AI modules/agents
    with st.sidebar:
        st.title("🤖 AI Modules")
        st.markdown("---")
        
        # AI Agent/Module selection
        selected_module = st.selectbox(
            "Select AI Agent:",
            ["Invoice Extractor", "Financial Advisor"],
            index=0
        )
        
        st.markdown("---")
        
        # Additional options
        st.subheader("Options")
        api_mode = st.checkbox("API Mode", value=False)
        debug_mode = st.checkbox("Debug Mode", value=False)
        
        if debug_mode:
            st.info("Debug mode enabled")
    
    # Main content area based on selected module
    if selected_module == "Invoice Extractor":
        show_invoice_extractor()
    elif selected_module == "Financial Advisor":
        show_financial_advisor()

def show_invoice_extractor():
    st.header("📄 Invoice Extractor")
    st.markdown("Extract and analyze invoice data using AI")
    
    # Show API status with refresh option
    col1, col2 = st.columns([3, 1])
    with col1:
        if API_AVAILABLE:
            st.success("🟢 API Connection: Healthy")
        else:
            st.error("🔴 API Connection: Unavailable")
            st.warning("Please start the FastAPI server: `uv run python app.py`")
    
    with col2:
        if st.button("🔄 Refresh", help="Check API status"):
            # Update global API status
            if check_api_health():
                st.success("API is now available!")
                st.rerun()
            else:
                st.error("API is still unavailable")
    
    if not API_AVAILABLE and not check_api_health():
        return
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Invoice Document",
        type=['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif'],
        help="Upload a PDF or image file containing invoice data (WebP not supported by Streamlit uploader)"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Document Preview")
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="Uploaded Invoice", width="stretch")
            else:
                st.info("PDF uploaded successfully")
        
        with col2:
            st.subheader("Extraction Options")
            extract_vendor = st.checkbox("Extract Vendor Information", value=True)
            extract_items = st.checkbox("Extract Line Items", value=True)
            extract_totals = st.checkbox("Extract Totals", value=True)
            
            if st.button("Extract Invoice Data", type="primary"):
                with st.spinner("Processing invoice via API..."):
                    # Process the uploaded file via API
                    file_bytes = uploaded_file.read()
                    result = extract_invoice_via_api(file_bytes, uploaded_file.name)
                    
                    if result:
                        st.success("✅ Invoice data extracted successfully!")
                        
                        # Display extraction metadata
                        if 'processing_time' in result:
                            st.info(f"⏱️ Processing time: {result['processing_time']:.2f}s")
                        
                        # Display the extracted data
                        if result.get('status') == 'success' and 'data' in result:
                            st.subheader("📊 Extracted Data")
                            st.json(result['data'])
                            
                            # Display file info if available
                            if 'file_info' in result:
                                with st.expander("📁 File Information"):
                                    st.json(result['file_info'])
                                    
                        elif result.get('status') == 'error':
                            st.error("❌ Extraction Failed")
                            
                            if 'error' in result:
                                error_info = result['error']
                                
                                # Display error message
                                st.error(f"**Error**: {error_info.get('message', 'Unknown error')}")
                                
                                # Display error category and code
                                col1, col2 = st.columns(2)
                                with col1:
                                    if 'category' in error_info:
                                        st.warning(f"**Category**: {error_info['category']}")
                                with col2:
                                    if 'code' in error_info and error_info['code']:
                                        st.warning(f"**Code**: {error_info['code']}")
                                
                                # Display additional details
                                if 'details' in error_info:
                                    with st.expander("📋 Error Details"):
                                        st.json(error_info['details'])
                            
                            # Show file info for debugging
                            if 'file_info' in result:
                                with st.expander("📁 File Information"):
                                    st.json(result['file_info'])
                                    
                        else:
                            st.json(result)
                    else:
                        st.error("❌ Failed to extract data. Please check the API connection.")
                        
                # Reset file uploader after processing
                uploaded_file.seek(0)

def show_financial_advisor():
    st.header("💰 Financial Advisor")
    st.markdown("Get AI-powered financial advice and insights")
    st.info("Financial Advisor module - Coming Soon!")
    
    # Initialize session state for chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello Shahrukh! I'm your AI Financial Advisor. How can I help you with your finances today?"}
        ]
    
    # Chat interface
    st.subheader("💬 Chat with Financial Advisor")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your finances..."):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # TODO: Integrate with actual financial advisor AI agent
                # For now, provide sample responses based on common queries
                response = generate_sample_financial_response(prompt)
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # Sidebar options for chat
    with st.sidebar:
        st.markdown("### Chat Options")
        if st.button("Clear Chat History"):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Hello Shahrukh! I'm your AI Financial Advisor. How can I help you with your finances today?"}
            ]
            st.rerun()
        
        include_invoice_context = st.checkbox("Include invoice data in responses", value=True)
        include_trends = st.checkbox("Include spending trends", value=True)

def generate_sample_financial_response(user_input):
    """Generate sample financial advisor responses based on user input."""
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ["budget", "budgeting", "plan"]):
        return """Based on your spending patterns, here are some budgeting tips:

💡 **Budget Recommendations:**
- Allocate 50% for needs, 30% for wants, 20% for savings
- Track your monthly expenses using categories
- Set up automatic transfers to your savings account
- Review and adjust your budget monthly

Would you like me to help you create a personalized budget based on your invoice data?"""
    
    elif any(word in user_input_lower for word in ["save", "saving", "savings"]):
        return """Here are some effective saving strategies:

💰 **Saving Tips:**
- Start with the 1% rule - save 1% more each month
- Use the envelope method for discretionary spending
- Consider high-yield savings accounts
- Automate your savings to make it effortless

I can analyze your recent expenses to identify potential saving opportunities. Would that be helpful?"""
    
    elif any(word in user_input_lower for word in ["invest", "investment", "investing"]):
        return """Investment advice tailored to your situation:

📈 **Investment Considerations:**
- Start with an emergency fund (3-6 months expenses)
- Consider low-cost index funds for beginners
- Diversify across different asset classes
- Think long-term and avoid emotional decisions

*Note: This is general advice. Always consult with a qualified financial advisor for personalized investment strategies.*"""
    
    elif any(word in user_input_lower for word in ["tax", "taxes", "deduction"]):
        return """Tax optimization strategies:

🧾 **Tax Tips:**
- Keep detailed records of all business expenses
- Consider tax-advantaged accounts (401k, IRA)
- Track deductible expenses throughout the year
- Plan major purchases around tax implications

I can help identify potential tax deductions from your uploaded invoices. Would you like me to analyze them?"""
    
    else:
        return f"""Thank you for your question about: "{user_input}"

I'm here to help with various financial topics including:
- **Budgeting & Expense Management**
- **Saving Strategies**
- **Investment Basics**
- **Tax Planning**
- **Debt Management**
- **Financial Goal Setting**

Could you provide more specific details about what aspect of your finances you'd like to focus on? I can give you more targeted advice based on your situation."""

if __name__ == "__main__":
    main()