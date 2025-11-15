import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq
import re

st.set_page_config(page_title="ChatBot Restaurant", page_icon="🤖")

with st.sidebar:
    st.header("🍴 Tentang Restoran")
    st.write("**Nama:** Restoran Sedap Rasa")
    st.write("**Lokasi:** Jl. Angsoka Hijau V, Jakarta")
    st.write("**Jam Buka:** 10.00-22.00 WIB")
    st.write("---")
    st.subheader("👨‍💻 Developer")
    st.write("Dibuat oleh Ren Lie")
    st.write("---")
    
    # CART DISPLAY
    if "orders" in st.session_state and st.session_state.orders:
        st.subheader("🛒 Keranjang")
        total = 0
        for key, item in st.session_state.orders.items():
            subtotal = item["price"] * item["qty"]
            st.write(f"{item['qty']}x {item['name']} - Rp {subtotal:,}")
            total += subtotal
        st.write(f"**Total: Rp {total:,}**")
        
        if st.button("🗑️ Kosongkan"):
            st.session_state.orders = {}
            st.rerun()

st.title("ChatBot Restaurant")
st.write("Halo! Saya bot yang akan membantu Anda menentukan pesanan!")

api_key = os.getenv("GROQ_API_KEY")

# MENU - lowercase keys untuk matching
MENU = {
    "nasi goreng": {"name": "Nasi Goreng", "price": 25000},
    "sate ayam": {"name": "Sate Ayam", "price": 20000},
    "mie goreng": {"name": "Mie Goreng", "price": 22000},
    "gado-gado": {"name": "Gado-Gado", "price": 18000},
    "gado gado": {"name": "Gado-Gado", "price": 18000},
    "makaroni salad": {"name": "Makaroni Salad", "price": 20000},
    "kopi": {"name": "Kopi", "price": 8000},
    "teh": {"name": "Teh", "price": 8000},
    "air mineral": {"name": "Air Mineral", "price": 5000},
    "es teler": {"name": "Es Teler", "price": 15000},
    "es campur": {"name": "Es Campur", "price": 12000},
    "jus buah": {"name": "Jus Buah", "price": 10000},
    "ayam betutu": {"name": "Ayam Betutu", "price": 50000},
    "udang rebus": {"name": "Udang Rebus", "price": 40000}
}

def parse_order(text):
    """Extract items dari user message - PYTHON ONLY"""
    text = text.lower()
    found = []
    
    for key, item in MENU.items():
        if key in text:
            # Cek quantity (default 1)
            qty_match = re.search(r'(\d+)\s*(?:x|buah|porsi)?\s*' + re.escape(key), text)
            if not qty_match:
                qty_match = re.search(r'' + re.escape(key) + r'\s*(\d+)', text)
            
            qty = int(qty_match.group(1)) if qty_match else 1
            
            found.append({
                "key": key,
                "name": item["name"],
                "price": item["price"],
                "qty": qty
            })
    
    return found

def add_to_cart(items):
    """Add items ke cart - handle duplicates"""
    for item in items:
        key = item["key"]
        if key in st.session_state.orders:
            # Sudah ada - tambah quantity
            st.session_state.orders[key]["qty"] += item["qty"]
        else:
            # Item baru
            st.session_state.orders[key] = {
                "name": item["name"],
                "price": item["price"],
                "qty": item["qty"]
            }

def get_cart_text():
    """Generate cart summary untuk AI"""
    if not st.session_state.orders:
        return "Keranjang kosong."
    
    lines = []
    total = 0
    for item in st.session_state.orders.values():
        subtotal = item["price"] * item["qty"]
        total += subtotal
        lines.append(f"- {item['qty']}x {item['name']} (Rp {subtotal:,})")
    
    lines.append(f"\nTotal: Rp {total:,}")
    return "\n".join(lines)

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []

if "orders" not in st.session_state:
    st.session_state.orders = {}  # Dict by menu key

client = Groq(api_key=api_key)

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ketik pesan...")

if prompt:
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Parse order DULU (Python)
    items_found = parse_order(prompt)
    if items_found:
        add_to_cart(items_found)
    
    # Get cart summary
    cart_text = get_cart_text()
    
    # AI response (hanya untuk UX, bukan data)
    menu_list = "\n".join([f"- {item['name']}: Rp {item['price']:,}" for item in MENU.values()])
    
    system_prompt = f"""
    Kamu adalah asisten restoran yang ramah dan membantu.

    Menu kami:
    {menu_list}
    Pesanan customer saat ini:
    {cart_text}

    Tugas kamu:
    - Jawab dengan natural dan ramah
    - Konfirmasi pesanan yang baru ditambahkan
    - Tanya apakah mau pesan lagi atau checkout
    - JANGAN generate data pesanan (itu sudah otomatis)
    - Jawaban singkat, maksimal 2-3 kalimat
    - Jika pelanggan tidak menyebutkan nominal jumlah yang dibeli ANGGAP MEREKA MEMBELI HANYA SATU
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    
    ai_reply = response.choices[0].message.content
    
    # Show AI response
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.write(ai_reply)