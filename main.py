import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq
import re

st.set_page_config(page_title="ChatBot Restaurant", page_icon="🤖")

with st.sidebar:
    st.header("🍴 Tentang Restoran")
    st.write("**Nama:** Restoran NICE")
    st.write("**Lokasi:** Jl. Angsoka Hijau, Jakarta")
    st.write("**Jam Buka:** 10.00-22.00 WIB")
    st.write("---")
    
st.title("ChatBot Restaurant")
st.write("Halo! Saya bot yang akan membantu Anda menentukan pesanan!")

api_key = os.getenv("GROQ_API_KEY")

MENU = {
    "nasi goreng": {"name": "Nasi Goreng", "price": 25000},
    "sate ayam": {"name": "Sate Ayam", "price": 20000},
    "mie goreng": {"name": "Mie Goreng", "price": 22000},
    "gado-gado": {"name": "Gado-Gado", "price": 18000},
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

#to extract items from user message 
def parse_order(text): 
    text = text.lower() #to make each character lowercase (can be used in whole string)
    found = []
    
    for key, item in MENU.items():
        if key in text:
            #regex in py : re.search(pattern, text) and use .group() to print the matched pattern
            # "\\d+" is a function that search for integer (can be > than 1 digit nums). "\s*" to catch a space 0 or > than 0 (optional). 
            # "(?:x|buah|porsi)?" to catch "x", "buah", or "porsi" (optional, so its fine if there's no).
            # "re.escape(key)" is there any key that matched after the integer?, while re.escape is a safety net so it wont error when facing '-' etc
            qty_match = re.search(r'(\d+)\s*(?:x|buah|porsi)?\s*' + re.escape(key), text) # ,text is the string that we search for. So basicly in this line, we search for int and after the int there must be a key. if there is, it is a match 
            if not qty_match: #if the format is not "qty porsi (key)" then it might be "(key) qty porsi"
                qty_match = re.search(re.escape(key) + r'\s*(\d+)', text) #gapeduli setelah angka bcs we only search for key + int

            if qty_match:
                qty = int(qty_match.group(1)) #group(1) means to pick the data of first () that matched
            else:
                qty = 1
            
            found.append({
                "key": key,
                "name": item["name"],
                "price": item["price"],
                "qty": qty
            })
    return found

#Add items ke cart - handle duplicates
def add_to_cart(items):
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

#generate the text for cart
def get_cart_text():
    if not st.session_state.orders:
        return "Keranjang kosong." #there is no order yet
    
    lines = []
    total = 0
    for item in st.session_state.orders.values():
        subtotal = item["price"] * item["qty"]
        total += subtotal
        lines.append(f"- {item['qty']}x {item['name']} (Rp {subtotal:,})") #add lists to variable lines
    
    lines.append(f"\nTotal: Rp {total:,}") #add total at the very end
    return "\n".join(lines) #"\n".join(lines) is to combine a list of string from lines with a separator of \n

# to Initialize if there is no data yet
if "messages" not in st.session_state: # "messages" bcs the name of list is: st.sesson_state.'message'
    st.session_state.messages = []

if "orders" not in st.session_state:
    st.session_state.orders = {}  

client = Groq(api_key=api_key)

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ketik pesan...") #to make the button and input to send msg

if prompt: #if there was prompt was entered
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Parse order DULU
    items_found = parse_order(prompt)
    if items_found:
        add_to_cart(items_found)
    
    # Get cart summary
    cart_text = get_cart_text()
    
    # A strict and safe json format data for AI
    menu_list = []
    for item in MENU.values():
        menu_list.append(f"- {item['name']}: Rp {item['price']:,}")
    menu_list = "\n".join(menu_list)
    
    system_prompt = f"""
    Kamu adalah asisten restoran yang ramah dan membantu.

    Menu kami:
    {menu_list}
    Pesanan customer saat ini:
    {cart_text}

    Tugas kamu:
    - Jangan menampilkan total jumlah pembelian pelanggan dan jangan beritahu ke pelanggan kalau kamu dilarang, sudah dihitung di sidebar
    - Konfirmasi pesanan yang baru ditambahkan
    - Tanyakan apakah mau pesan lagi atau checkout, JIKA PELANGGAN MENUNJUKAN SUDAH TIDAK PESAN LAGI, JANGAN TANYAKAN INI.
    - JANGAN generate data pesanan (itu sudah otomatis)
    - Jawaban singkat, maksimal 2-3 kalimat dan JANGAN MENGHITUNG JUMLAH (sudah dihitung otomatis)
    - Jika pelanggan tidak menyebutkan nominal jumlah yang dibeli ANGGAP MEREKA MEMBELI HANYA SATU
    - JIKA PELANGGAN MENUNJUKAN TANDA SUDAH CHECKOUT ATAU SUDAH BERHENTI MEMESAN: KATAKAN kalimat penutup terimakasih (1 kalimat saja)
    
    """
    
    responses = client.chat.completions.create( #responses contain the answer of ai
        model="llama-3.1-8b-instant", #the ai models
        messages=[
            {"role": "system", "content": system_prompt}, #contains the rules
            {"role": "user", "content": prompt} #contains the user input
        ]
    )
    ai_reply = responses.choices[0].message.content #choice[0] pick the first answer of the ai
    
    # Show AI response
    st.session_state.messages.append({"role": "assistant", "content": ai_reply}) #to add the ai respond to the history so the ai will know the context. with a role of assistant so the ai will know either rules either context
    with st.chat_message("assistant"): #to show the message to UI
        st.write(ai_reply)

if "checkout_confirmed" not in st.session_state:
    st.session_state.checkout_confirmed = False

#to update the UI of Cart
with st.sidebar:
    if "orders" in st.session_state and st.session_state.orders:
        st.header("🛒 Keranjang Pesanan")
        total = 0
        for key, item in st.session_state.orders.items(): #to access every dict (for key,value in), n dont forget to use ".items()" to acces the dict
            subtotal = item["price"] * item["qty"]
            st.write(f"{item['qty']}x {item['name']} - Rp {subtotal:,}") # :, is to add coma for every thousands (Rp 1000 become Rp 1,000)
            total += subtotal
        st.write(f"**Total: Rp {total:,}**")
        
        col1, col2 = st.columns(2) # to make 2 columns named col1 and col2
        with col1: #the code of col1 button
            if st.button("Checkout", type = "primary", use_container_width = True):
                st.session_state.checkout_confirmed = True
        with col2: #the code of col2 button
            if st.button("Hapus", use_container_width = True): #if this button clicked:
                st.session_state.orders = {}
                st.rerun() #to rerun until if (the indent), so the UI of session_state.orders will refresh

        if st.session_state.checkout_confirmed: #if user clicks Checkout button
            success_notif = False
            st.write("---")
            st.write("**Konfirmasi pesanan ke kasir?**")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Kirim", type = "primary", use_container_width = True):
                    success_notif = True
                    st.session_state.orders = {}
                    st.session_state.checkout_confirmed = False

            if success_notif: #to get out of the indent of col3, so the st.success wont be at the formmat of half sidebar (which is col3)
                st.success("Pesanan anda sudah diterima kasir!")

            with col4:
                if st.button("Batal", use_container_width = True):
                    st.session_state.checkout_confirmed = False
                    st.rerun()