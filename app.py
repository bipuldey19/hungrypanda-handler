import streamlit as st
import requests
import json
from datetime import datetime
import hashlib
import time
import uuid
from supabase import create_client
from streamlit.runtime.uploaded_file_manager import UploadedFile

# ===========================
# PAGE CONFIGURATION
# ===========================
st.set_page_config(
    page_title="Kitchen Manager",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================
# CUSTOM CSS
# ===========================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --background-color: #F7F7F7;
        --text-color: #2C3E50;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Menu card styling */
    .menu-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-left: 4px solid #667eea;
    }
    
    .menu-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .menu-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .menu-card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2C3E50;
        margin: 0;
    }
    
    .menu-card-price {
        font-size: 1.8rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .menu-card-body {
        margin-bottom: 1rem;
    }
    
    .menu-card-meta {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    
    .meta-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-active {
        background: #d4edda;
        color: #155724;
    }
    
    .badge-inactive {
        background: #f8d7da;
        color: #721c24;
    }
    
    .badge-popular {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge-category {
        background: #d1ecf1;
        color: #0c5460;
    }
    
    /* Stats cards */
    .stats-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-top: 4px solid #667eea;
    }
    
    .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .stats-label {
        font-size: 1rem;
        color: #7f8c8d;
        margin: 0.5rem 0 0 0;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }
    
    /* Success/Error messages */
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    /* Image preview */
    .image-preview {
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        max-height: 300px;
        object-fit: cover;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# ===========================
# AUTHENTICATION
# ===========================
def check_password():
    """Returns True if user has entered correct password."""
    
    def password_entered():
        """Checks whether password entered is correct."""
        password = st.session_state.get("secrets", {}).get("auth", {}).get("password", "admin123")
        
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(password.encode()).hexdigest():
            st.session_state["password_correct"] = True
            st.session_state["logged_in_time"] = time.time()
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Check if already logged in and session hasn't expired (24 hours)
    if st.session_state.get("password_correct", False):
        if time.time() - st.session_state.get("logged_in_time", 0) < 86400:  # 24 hours
            return True
        else:
            st.session_state["password_correct"] = False

    # Show login form
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h1>🍽️ Kitchen Manager</h1>
        <p style='color: #7f8c8d; font-size: 1.1rem;'>Please enter password to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            label_visibility="collapsed",
            placeholder="Enter password"
        )

        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Password incorrect")

    return False

# ===========================
# INITIALIZATION
# ===========================
def init_app():
    """Initialize app configuration and secrets."""
    if 'secrets_loaded' not in st.session_state:
        try:
            st.session_state.secrets = {
                'n8n': {
                    'add_item_webhook': st.secrets["n8n"]["add_item_webhook"],
                    'update_status_webhook': st.secrets["n8n"]["update_status_webhook"],
                    'delete_item_webhook': st.secrets["n8n"]["delete_item_webhook"]
                },
                'supabase': {
                    'url': st.secrets["supabase"]["url"],
                    'key': st.secrets["supabase"]["key"]
                },
                'auth': {
                    'password': st.secrets.get("auth", {}).get("password", "admin123")
                }
            }
            st.session_state.secrets_loaded = True
        except Exception as e:
            st.error(f"⚠️ Error loading secrets: {str(e)}")
            st.stop()

def get_supabase_client():
    """Get Supabase client."""
    return create_client(
        st.session_state.secrets['supabase']['url'],
        st.session_state.secrets['supabase']['key']
    )

def upload_file_to_supabase(file: UploadedFile, bucket_name: str = "kitchen-images") -> str | None:
    """Uploads a Streamlit file object to Supabase Storage and returns the public URL."""
    try:
        supabase = get_supabase_client()
        
        # Get the raw bytes from the file object
        file_bytes = file.getvalue()
        
        # Create a unique file path
        file_ext = file.name.split('.')[-1]
        file_path = f"public/{uuid.uuid4()}.{file_ext}"
        
        # Upload the bytes
        supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=file_path,
            file_options={"content-type": file.type}
        )
        
        # Return the public URL
        return supabase.storage.from_(bucket_name).get_public_url(file_path)
    except Exception as e:
        st.error(f"Storage Error: {str(e)}")
        return None

# ===========================
# API FUNCTIONS
# ===========================
def add_menu_item(item_data):
    """Add a new menu item via webhook."""
    try:
        response = requests.post(
            st.session_state.secrets['n8n']['add_item_webhook'],
            json=item_data,
            timeout=30
        )
        response.raise_for_status()
        return True, "Item added successfully! ✅"
    except requests.exceptions.RequestException as e:
        return False, f"Error adding item: {str(e)}"

def update_item_status(item_id, active, availability="available"):
    """Update menu item status via webhook."""
    try:
        response = requests.post(
            st.session_state.secrets['n8n']['update_status_webhook'],
            json={
                "item_id": item_id,
                "active": active,
                "availability": availability
            },
            timeout=30
        )
        response.raise_for_status()
        return True, "Status updated successfully! ✅"
    except requests.exceptions.RequestException as e:
        return False, f"Error updating status: {str(e)}"

def delete_menu_item(item_id):
    """Delete menu item via webhook."""
    try:
        response = requests.post(
            st.session_state.secrets['n8n']['delete_item_webhook'],
            json={"item_id": item_id},
            timeout=30
        )
        response.raise_for_status()
        return True, "Item deleted successfully! ✅"
    except requests.exceptions.RequestException as e:
        return False, f"Error deleting item: {str(e)}"

def fetch_menu_items():
    """Fetch all menu items from Supabase."""
    try:
        supabase = get_supabase_client()
        response = supabase.table('kitchen_data').select('*').eq('metadata->>type', 'menu').execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching menu items: {str(e)}")
        return []

# ===========================
# UI COMPONENTS
# ===========================
def render_header():
    """Render main header."""
    st.markdown("""
    <div class='main-header'>
        <h1>🍽️ Kitchen Manager</h1>
        <p>Manage your menu items and knowledge base with ease</p>
    </div>
    """, unsafe_allow_html=True)

def render_stats(items):
    """Render statistics cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(items)
    active_items = len([i for i in items if i.get('metadata', {}).get('active', False)])
    popular_items = len([i for i in items if i.get('metadata', {}).get('popular', False)])
    avg_price = sum([float(i.get('metadata', {}).get('price', 0)) for i in items]) / total_items if total_items > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class='stats-card'>
            <p class='stats-number'>{total_items}</p>
            <p class='stats-label'>Total Items</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='stats-card'>
            <p class='stats-number'>{active_items}</p>
            <p class='stats-label'>Active Items</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='stats-card'>
            <p class='stats-number'>{popular_items}</p>
            <p class='stats-label'>Popular Items</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='stats-card'>
            <p class='stats-number'>{avg_price:.0f}৳</p>
            <p class='stats-label'>Avg. Price</p>
        </div>
        """, unsafe_allow_html=True)

def render_menu_card(item):
    """Render a single menu card."""
    metadata = item.get('metadata', {})
    item_id = item.get('id')
    
    # Extract data
    name = metadata.get('item_name', 'Unnamed Item')
    price = metadata.get('price', 0)
    basket_price = metadata.get('basket_price')
    description = metadata.get('description', 'No description')
    category = metadata.get('category', 'general')
    active = metadata.get('active', False)
    popular = metadata.get('popular', False)
    main_image = metadata.get('main_image_url')
    
    # Card container
    with st.container():
        col1, col2 = st.columns([1, 3])
        
        # Image column
        with col1:
            if main_image:
                st.image(main_image, use_container_width=True)
            else:
                st.markdown("""
                <div style='background: #f0f0f0; padding: 3rem; text-align: center; border-radius: 10px;'>
                    <p style='font-size: 3rem; margin: 0;'>🍽️</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Details column
        with col2:
            # Header
            col_title, col_price = st.columns([3, 1])
            with col_title:
                st.markdown(f"### {name}")
            with col_price:
                st.markdown(f"<h3 style='color: #667eea; text-align: left; margin: 0;'>{price}৳</h3>", unsafe_allow_html=True)
                if basket_price:
                    st.markdown(f"<p style='text-align: right; color: #7f8c8d; margin: 0;'>Basket: {basket_price}৳</p>", unsafe_allow_html=True)
            
            # Description
            st.markdown(f"<p style='color: #555;'>{description}</p>", unsafe_allow_html=True)
            
            # Badges
            badge_html = "<div style='display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 1rem 0;'>"
            
            if active:
                badge_html += "<span class='meta-badge badge-active'>✓ Active</span>"
            else:
                badge_html += "<span class='meta-badge badge-inactive'>✗ Inactive</span>"
            
            if popular:
                badge_html += "<span class='meta-badge badge-popular'>⭐ Popular</span>"
            
            badge_html += f"<span class='meta-badge badge-category'>📂 {category.title()}</span>"
            badge_html += "</div>"
            
            st.markdown(badge_html, unsafe_allow_html=True)
            
            # Action buttons
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 2])
            
            with col_btn1:
                if st.button("👁️ View", key=f"view_{item_id}", use_container_width=True):
                    st.session_state[f'show_details_{item_id}'] = not st.session_state.get(f'show_details_{item_id}', False)
            
            with col_btn2:
                new_status = not active
                status_label = "🔴 Deactivate" if active else "🟢 Activate"
                if st.button(status_label, key=f"toggle_{item_id}", use_container_width=True):
                    success, message = update_item_status(item_id, new_status)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with col_btn3:
                if st.button("🗑️ Delete", key=f"delete_{item_id}", use_container_width=True):
                    st.session_state[f'confirm_delete_{item_id}'] = True
            
            # Show details if toggled
            if st.session_state.get(f'show_details_{item_id}', False):
                with st.expander("📋 Full Details", expanded=True):
                    st.json(metadata)
            
            # Confirmation dialog
            if st.session_state.get(f'confirm_delete_{item_id}', False):
                st.warning(f"⚠️ Are you sure you want to delete **{name}**? This action cannot be undone!")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Yes, Delete", key=f"confirm_yes_{item_id}", type="primary", use_container_width=True):
                        success, message = delete_menu_item(item_id)
                        if success:
                            st.success(message)
                            st.session_state[f'confirm_delete_{item_id}'] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                with col_no:
                    if st.button("❌ Cancel", key=f"confirm_no_{item_id}", use_container_width=True):
                        st.session_state[f'confirm_delete_{item_id}'] = False
                        st.rerun()
        
        st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

def render_add_item_form():
    """Render add new item form."""
    with st.expander("➕ Add New Menu Item", expanded=False):
        st.markdown("### 📝 Item Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Item Name *", placeholder="e.g., Kacchi Biryani")
            price = st.number_input("Price (৳) *", min_value=0, value=0, step=10)
            category = st.selectbox(
                "Category *",
                ["breakfast", "lunch", "dinner", "snacks", "drinks", "dessert"]
            )
            spice_level = st.selectbox(
                "Spice Level",
                ["None", "mild", "medium", "hot"]
            )
        
        with col2:
            basket_price = st.number_input("Basket Price (৳)", min_value=0, value=0, step=10)
            portion_size = st.text_input("Portion Size", placeholder="e.g., 1 person")
            preparation_time = st.text_input("Preparation Time", placeholder="e.g., 30 minutes")
            col_check1, col_check2 = st.columns(2)
            with col_check1:
                popular = st.checkbox("⭐ Popular Item")
            with col_check2:
                seasonal = st.checkbox("🌸 Seasonal")
        
        description = st.text_area("Description *", placeholder="Describe the dish...")
        ingredients = st.text_area("Ingredients", placeholder="List all ingredients...")
        allergens = st.text_input("Allergens", placeholder="e.g., Dairy, Nuts")
        
        st.markdown("### 🖼️ Images")
        
        # Main image upload
        main_image_file = st.file_uploader(
            "Main Image *",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload the main display image for this item",
            key="main_image_upload"
        )
        
        # Preview main image
        if main_image_file:
            st.image(main_image_file, caption="Main Image Preview", width=300)
        
        # Additional images upload
        other_image_files = st.file_uploader(
            "Additional Images (Optional)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            help="Upload additional images for this item",
            key="other_images_upload"
        )
        
        # Preview additional images
        if other_image_files:
            cols = st.columns(min(len(other_image_files), 4))
            for idx, img_file in enumerate(other_image_files):
                with cols[idx % 4]:
                    st.image(img_file, caption=f"Image {idx + 1}", use_container_width=True)
        
        st.markdown("---")
        
        if st.button("➕ Add Item to Menu", type="primary", use_container_width=True):
            # Validation
            if not name or not price or not description or not main_image_file:
                st.error("⚠️ Please fill in all required fields (marked with *)")
                return
            
            # Upload images
            with st.spinner("Uploading images..."):
                # Upload main image
                main_image_url = upload_file_to_supabase(main_image_file)
                if not main_image_url:
                    st.error("❌ Failed to upload main image. Please try again.")
                    return
                
                # Upload additional images
                other_image_urls = []
                if other_image_files:
                    for img_file in other_image_files:
                        url = upload_file_to_supabase(img_file)
                        if url:
                            other_image_urls.append(url)
                        else:
                            st.warning(f"⚠️ Failed to upload {img_file.name}")
            
            # Prepare data
            item_data = {
                "name": name,
                "price": float(price),
                "basket_price": float(basket_price) if basket_price > 0 else None,
                "description": description,
                "ingredients": ingredients if ingredients else None,
                "category": category,
                "spice_level": spice_level if spice_level != "None" else None,
                "allergens": allergens if allergens else None,
                "main_image_url": main_image_url,
                "other_image_urls": other_image_urls,
                "portion_size": portion_size if portion_size else None,
                "preparation_time": preparation_time if preparation_time else None,
                "popular": popular,
                "seasonal": seasonal
            }
            
            # Send to webhook
            with st.spinner("Adding item to menu..."):
                success, message = add_menu_item(item_data)
                if success:
                    st.success(message)
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(message)

# ===========================
# MAIN APP
# ===========================
def main():
    """Main application."""
    init_app()
    
    # Authentication check
    if not check_password():
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Navigation")
        page = st.radio(
            "Select Page",
            ["📋 Menu Items", "📚 Knowledge Base", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #7f8c8d; font-size: 0.85rem;'>
            <p>🍽️ Kitchen Manager v1.0</p>
            <p>Made with ❤️ using Streamlit</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    render_header()
    
    if page == "📋 Menu Items":
        # Add new item form
        render_add_item_form()
        
        st.markdown("## 🍴 Current Menu Items")
        
        # Fetch items
        with st.spinner("Loading menu items..."):
            items = fetch_menu_items()
        
        if not items:
            st.info("📭 No menu items found. Add your first item above!")
            return
        
        # Stats
        render_stats(items)
        
        st.markdown("---")
        
        # Filters
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            filter_status = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
        
        with col_filter2:
            categories = ["All"] + list(set([i.get('metadata', {}).get('category', 'general') for i in items]))
            filter_category = st.selectbox("Filter by Category", categories)
        
        with col_filter3:
            sort_by = st.selectbox("Sort by", ["Name", "Price (Low to High)", "Price (High to Low)", "Recently Added"])
        
        # Apply filters
        filtered_items = items
        
        if filter_status != "All":
            filtered_items = [i for i in filtered_items if i.get('metadata', {}).get('active', False) == (filter_status == "Active")]
        
        if filter_category != "All":
            filtered_items = [i for i in filtered_items if i.get('metadata', {}).get('category') == filter_category]
        
        # Apply sorting
        if sort_by == "Name":
            filtered_items = sorted(filtered_items, key=lambda x: x.get('metadata', {}).get('item_name', ''))
        elif sort_by == "Price (Low to High)":
            filtered_items = sorted(filtered_items, key=lambda x: float(x.get('metadata', {}).get('price', 0)))
        elif sort_by == "Price (High to Low)":
            filtered_items = sorted(filtered_items, key=lambda x: float(x.get('metadata', {}).get('price', 0)), reverse=True)
        elif sort_by == "Recently Added":
            filtered_items = sorted(filtered_items, key=lambda x: x.get('created_at', ''), reverse=True)
        
        st.markdown(f"### Showing {len(filtered_items)} items")
        
        # Render cards
        for item in filtered_items:
            render_menu_card(item)
    
    elif page == "📚 Knowledge Base":
        st.markdown("## 📚 Knowledge Base Management")
        st.info("🚧 Knowledge base management coming soon! You can upload PDFs via the form endpoint for now.")
        
        st.markdown("### 📤 Upload PDF")
        st.markdown(f"Use this form URL to upload FAQs and guides:")
        st.code("https://your-n8n-url.com/form/hungrypanda-knowledge-upload")
    
    elif page == "⚙️ Settings":
        st.markdown("## ⚙️ Settings")
        
        st.markdown("### 🔗 Webhook URLs")
        with st.expander("View Webhook URLs"):
            st.code(st.session_state.secrets['n8n']['add_item_webhook'])
            st.code(st.session_state.secrets['n8n']['update_status_webhook'])
            st.code(st.session_state.secrets['n8n']['delete_item_webhook'])
        
        st.markdown("### 🗄️ Database")
        with st.expander("Supabase Configuration"):
            st.code(st.session_state.secrets['supabase']['url'])
            st.text("Key: " + "*" * 20)
        
        st.markdown("### 🔒 Security")
        if st.button("🔄 Clear Session & Logout"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
