import streamlit as st
import requests
from supabase import create_client, Client
import uuid  # For unique file names
import io      # To handle file bytes
from streamlit.runtime.uploaded_file_manager import UploadedFile # For type hints
from streamlit_cookies_manager import CookieManager # <-- NEW: Import cookie manager

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kitchen Menu Manager",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS FOR UNIFORM CARDS ---
st.markdown("""
<style>
    /* ... (Your CSS for uniform cards) ... */
    [data-testid="stVerticalBlockBorderWrapper"] {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-image-container {
        position: relative;
        width: 100%;
        padding-bottom: 66.66%; /* 3:2 Aspect Ratio */
        overflow: hidden;
        border-radius: 7px; 
    }
    .card-image-container img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    [data-testid="stVerticalBlockBorderWrapper"] h3 {
         font-size: 1.25rem; 
         min-height: 2.4em; 
         max-height: 2.4em;
         overflow: hidden;
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p {
        min-height: 3.6em; 
        max-height: 3.6em;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOAD SECRETS & INITIALIZE CLIENTS ---
try:
    N8N_ADD_ITEM_URL = st.secrets["n8n"]["add_item_webhook"]
    N8N_UPDATE_STATUS_URL = st.secrets["n8n"]["update_status_webhook"]
    N8N_DELETE_ITEM_URL = st.secrets["n8n"]["delete_item_webhook"]
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    SUPABASE_BUCKET = "menu-images" 
    APP_PASSWORD = st.secrets["app"]["password"]

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except KeyError as e:
    st.error(f"🚨 Critical Error: A secret is missing! Check your secrets.toml file. Missing key: {e}")
    st.stop()

# --- 4. AUTHENTICATION LOGIC WITH COOKIES ---

# Initialize the cookie manager
cookies = CookieManager(key="auth_cookie_key")
if not cookies.ready():
    # This is a one-time setup on the first page load
    st.stop()

# Check for the cookie first when initializing session_state
if "authenticated" not in st.session_state:
    auth_cookie = cookies.get("auth_cookie")
    if auth_cookie == APP_PASSWORD:
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

def login_form():
    """Displays a login form in the center of the page."""
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            st.title("Admin Login")
            with st.form("login_form"):
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if password == APP_PASSWORD:
                        st.session_state.authenticated = True
                        # Set the cookie to remember the login
                        cookies.set("auth_cookie", APP_PASSWORD, key="set_cookie")
                        st.rerun()
                    else:
                        st.error("Incorrect password")

# If not authenticated, show login form and stop
if not st.session_state.authenticated:
    login_form()
    st.stop()

# --- 5. HELPER FUNCTIONS (Main App) ---

def upload_file_to_supabase(file: UploadedFile) -> str | None:
    try:
        file_bytes = file.getvalue()
        file_ext = file.name.split('.')[-1]
        file_path = f"public/{uuid.uuid4()}.{file_ext}"
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            file=file_bytes, 
            path=file_path,
            file_options={"content-type": file.type}
        )
        return supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
    except Exception as e:
        st.error(f"Storage Error: {str(e)}")
        return None

def update_item_status(item_id: int):
    key = f"status_{item_id}"
    new_status = st.session_state[key]
    try:
        payload = {"item_id": item_id, "active": (new_status == "Active")}
        response = requests.post(N8N_UPDATE_STATUS_URL, json=payload)
        if response.status_code == 200:
            st.toast(f"Item {item_id} set to {new_status}", icon="✅")
        else:
             st.error(f"Error updating item {item_id}. n8n said: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Connection error to n8n: {e}")

def delete_item(item_id: int):
    try:
        payload = {"item_id": item_id}
        response = requests.post(N8N_DELETE_ITEM_URL, json=payload)
        if response.status_code == 200:
            st.toast(f"Item {item_id} deleted!", icon="🗑️")
            st.cache_data.clear() 
            st.rerun() 
        else:
             st.error(f"Error deleting item {item_id}. n8n said: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Connection error to n8n: {e}")

@st.cache_data(ttl=60)
def get_menu_items():
    try:
        response = supabase.table('menu_items').select('id, metadata').order('id').execute()
        return response.data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return []

# --- 6. "ADD NEW ITEM" FORM (Main App) ---
st.sidebar.title("Admin")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    # Delete the cookie on logout
    cookies.delete("auth_cookie", key="delete_cookie")
    st.rerun()

st.title("Cloud Kitchen Menu Manager")

with st.expander("➕ Add a New Menu Item"):
    with st.form("new_item_form", clear_on_submit=True):
        st.subheader("Item Details")
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("Item Name*")
        with col2:
            item_price = st.number_input("Price (BDT)*", min_value=0, step=1)
        item_desc = st.text_area("Description")
        item_ingredients = st.text_area("Ingredients (e.g., chicken, onion, spices)")
        st.subheader("Images")
        main_image_file = st.file_uploader("Main Ad Image*", type=["jpg", "png", "jpeg"])
        other_image_files = st.file_uploader("Other Images (Optional)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        submitted = st.form_submit_button("Save New Item")

        if submitted:
            if not main_image_file or not item_name or item_price <= 0:
                st.error("Please fill in all required fields (*).")
            else:
                with st.spinner("Processing... Uploading image and calling n8n..."):
                    try:
                        main_image_url = upload_file_to_supabase(main_image_file)
                        other_image_urls = []
                        if other_image_files:
                            for file in other_image_files:
                                other_image_urls.append(upload_file_to_supabase(file))
                        if not main_image_url:
                            st.error("Main image failed to upload. Aborting.")
                        else:
                            n8n_payload = {
                                "name": item_name,
                                "price": item_price,
                                "description": item_desc,
                                "ingredients": item_ingredients,
                                "main_image_url": main_image_url,
                                "other_image_urls": other_image_urls
                            }
                            response = requests.post(N8N_ADD_ITEM_URL, json=n8n_payload)
                            if response.status_code == 200:
                                st.success(f"Item '{item_name}' added successfully!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"Error from n8n (Status {response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

# --- 7. "MANAGE EXISTING ITEMS" DISPLAY (Main App) ---
st.divider()
st.header("Manage Existing Menu")

@st.dialog("Confirm Deletion")
def show_delete_dialog():
    item_id = st.session_state.item_to_delete
    item_name = st.session_state.item_name_to_delete
    st.error(f"Are you sure you want to delete **{item_name}** (ID: {item_id})?")
    st.warning("This will delete the item from the database and all its images from storage. This action cannot be undone.")
    col1, col2 = st.columns(2)
    if col1.button("Cancel", use_container_width=True):
        st.session_state.item_to_delete = None
        st.session_state.item_name_to_delete = ""
        st.rerun()
    if col2.button("Confirm Delete", type="primary", use_container_width=True):
        delete_item(item_id)
        st.session_state.item_to_delete = None
        st.session_state.item_name_to_delete = ""

if "item_to_delete" not in st.session_state:
    st.session_state.item_to_delete = None
    st.session_state.item_name_to_delete = ""

if st.session_state.item_to_delete:
    show_delete_dialog()

items = get_menu_items()

if not items:
    st.info("No menu items found. Add one using the form above.")
else:
    cols = st.columns(3)
    for i, item in enumerate(items):
        meta = item['metadata']
        item_id = item['id']
        item_name_alt = meta.get('item_name', 'Unnamed Item')
        
        with cols[i % 3]:
            with st.container(border=True): 
                image_url = meta.get('main_image_url', 'https://placehold.co/600x400?text=No+Image')
                st.markdown(
                    f'<div class="card-image-container"><img src="{image_url}" alt="{item_name_alt}"></div>',
                    unsafe_allow_html=True
                )
                st.subheader(item_name_alt)
                st.markdown(f"**Price:** {meta.get('price', 0)} BDT")
                description = meta.get('full_description', '')
                if len(description) > 100:
                    description = description[:100] + "..."
                st.caption(description)
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    current_status = "Active" if meta.get('active', True) else "Inactive"
                    selectbox_key = f"status_{item_id}"
                    st.selectbox(
                        "Status",
                        ("Active", "Inactive"),
                        index=0 if current_status == "Active" else 1,
                        key=selectbox_key,
                        on_change=update_item_status,
                        args=(item_id,)
                    )
                with c2:
                    st.write("") 
                    st.write("") 
                    if st.button("Delete", key=f"delete_{item_id}", type="primary"):
                        st.session_state.item_to_delete = item_id
                        st.session_state.item_name_to_delete = item_name_alt
                        st.rerun()
