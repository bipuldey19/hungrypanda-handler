import streamlit as st
import requests
from supabase import create_client, Client
import uuid  # To create unique file names
import io      # To handle file bytes

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kitchen Menu Manager",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. LOAD SECRETS & INITIALIZE CLIENTS ---
# These must be in your Streamlit secrets (.streamlit/secrets.toml)
try:
    N8N_ADD_ITEM_URL = st.secrets["n8n"]["add_item_webhook"]
    N8N_UPDATE_STATUS_URL = st.secrets["n8n"]["update_status_webhook"]
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    # The name of your Supabase Storage bucket
    SUPABASE_BUCKET = "menu-images" 

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except KeyError:
    st.error("🚨 Critical Error: Supabase or n8n secrets are not set in st.secrets.")
    st.stop()

# --- 3. HELPER FUNCTIONS (Back-end Logic) ---

def upload_file_to_supabase(file: io.BytesIO, file_name: str) -> str:
    """Uploads a file to Supabase Storage and returns the public URL."""
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            file=file,
            path=file_name,
            file_options={"content-type": file.type}
        )
        # Return the public URL
        return supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
    except Exception as e:
        st.error(f"Storage Error: {str(e)}")
        return None

def update_item_status(item_id: int, new_status: str):
    """Callback function to trigger the n8n webhook for status update."""
    try:
        payload = {"item_id": item_id, "active": (new_status == "Active")}
        response = requests.post(N8N_UPDATE_STATUS_URL, json=payload)
        if response.status_code != 200:
             st.toast(f"Error updating item {item_id}", icon="🔥")
        else:
            st.toast(f"Item {item_id} set to {new_status}", icon="✅")
    except Exception as e:
        st.error(f"Connection error to n8n: {e}")

@st.cache_data(ttl=60) # Cache menu for 60 seconds
def get_menu_items():
    """Fetches all menu items from the Supabase database."""
    try:
        response = supabase.table('menu_items').select('id, metadata').execute()
        return response.data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return []

# --- 4. "ADD NEW ITEM" FORM (Requirement #3) ---
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
            # --- Form Validation ---
            if not main_image_file or not item_name or item_price <= 0:
                st.error("Please fill in all required fields (*).")
            else:
                with st.spinner("Processing... Uploading image and calling n8n..."):
                    try:
                        # 1. Upload Main Image to Supabase Storage
                        file_ext = main_image_file.name.split('.')[-1]
                        file_path = f"public/{uuid.uuid4()}.{file_ext}"
                        main_image_url = upload_file_to_supabase(main_image_file, file_path)

                        # 2. (Optional) Upload Other Images
                        other_image_urls = []
                        for file in other_image_files:
                            other_file_ext = file.name.split('.')[-1]
                            other_file_path = f"public/{uuid.uuid4()}.{other_file_ext}"
                            other_image_urls.append(upload_file_to_supabase(file, other_file_path))

                        # 3. Prepare data payload for n8n
                        n8n_payload = {
                            "name": item_name,
                            "price": item_price,
                            "description": item_desc,
                            "ingredients": item_ingredients,
                            "main_image_url": main_image_url,
                            "other_image_urls": other_image_urls
                        }

                        # 4. Call n8n Webhook to process data
                        response = requests.post(N8N_ADD_ITEM_URL, json=n8n_payload)
                        
                        if response.status_code == 200:
                            st.success(f"Item '{item_name}' added successfully!")
                            st.cache_data.clear() # Clear cache to show new item
                        else:
                            st.error(f"Error from n8n (Status {response.status_code}): {response.text}")
                    
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

# --- 5. "MANAGE EXISTING ITEMS" DISPLAY (Requirement #1 & #2) ---
st.divider()
st.header("Manage Existing Menu")

items = get_menu_items()

if not items:
    st.info("No menu items found. Add one using the form above.")
else:
    # Create 3 responsive columns
    cols = st.columns(3)
    
    for i, item in enumerate(items):
        meta = item['metadata']
        item_id = item['id']
        
        # Place each card in the next available column
        with cols[i % 3]:
            with st.container(border=True):
                
                # 1. Ad Image
                st.image(
                    meta.get('main_image_url', 'https://placehold.co/600x400?text=No+Image'), 
                    use_column_width=True
                )
                
                # 2. Item Name
                st.subheader(meta.get('item_name', 'Unnamed Item'))
                
                # 3. Price
                st.markdown(f"**Price:** {meta.get('price', 0)} BDT")
                
                # 4. Active Status Dropdown
                current_status = "Active" if meta.get('active', True) else "Inactive"
                
                st.selectbox(
                    "Status",
                    ("Active", "Inactive"),
                    index=0 if current_status == "Active" else 1,
                    key=f"status_{item_id}", # Unique key for this widget
                    on_change=update_item_status,
                    args=(item_id, st.session_state[f"status_{item_id}"]) # Passes the NEW value
                )
