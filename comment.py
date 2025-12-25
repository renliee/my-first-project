#note: every interaction, click, chat = system will rerun the code
import streamlit as st
from dotenv import load_dotenv
load_dotenv() #to read the variable from .env
import requests
import os #to access environment variable (.env)
from groq import Groq 
from difflib import get_close_matches #for fuzzy matching typo words
import re #python library for pattern matching

st.set_page_config(page_title="ChatBot Restaurant", page_icon="🤖")

with st.sidebar: #with is needed if there's someting to open (file, connection) and will close that automatically, grouping more than 1 comments to some context (code below)
    st.header("🍴 Tentang Restoran")
    st.write("**Nama:** Restoran NICE")
    st.write("**Lokasi:** Jl. Angsoka Hijau, Jakarta")
    st.write("**Jam Buka:** 10.00-22.00 WIB")
    st.write("---")

    st.subheader("Silahkan Pilih Meja")
    table_option = ["Pilih Meja..."] + [f"Meja {i}" for i in range(1, 16)] #make list of Pilih meja and meja 1-15 to be used in dropdown
    selected = st.selectbox("Anda duduk di meja berapa?", options=table_option) #st.selectbox: dropdown menu from streamlit, selected = box yg user pilih
    
    if selected != "Pilih Meja...":
        st.session_state.table_number = int(selected.split(" ")[1]) #"Meja 12" split -> ["Meja", "12"] then take index 1
        st.success(f"Meja {st.session_state.table_number}")
    else:
        st.session_state.table_number = None
    st.write("---")

# markdown: "#, ##, ###" is a hierarchy, the least #, larger the text
st.markdown("""
# Welcome to Restaurant NICE 
### Hai! Saya bot yang siap membantu Anda 😊  
Silakan ketik menu yang diinginkan, kemudian tekan tombol Checkout untuk mengirim pesanan ke kasir!
""")

api_keys = os.getenv("GROQ_API_KEY") #.getenv: method from os 
FASTAPI_URL = "http://127.0.0.1:8000"   #link to access backend

MENU = {
    "nasi goreng": {"name": "Nasi Goreng", "price": 25000},
    "sate ayam": {"name": "Sate Ayam", "price": 20000},
    "sate": {"name": "Sate Ayam", "price": 20000},
    "mie goreng": {"name": "Mie Goreng", "price": 22000},
    "gado-gado": {"name": "Gado-Gado", "price": 18000},
    "makaroni": {"name": "Makaroni", "price": 20000},
    "kopi": {"name": "Kopi", "price": 8000},
    "teh": {"name": "Teh", "price": 8000},
    "air mineral": {"name": "Air Mineral", "price": 5000},
    "es teler": {"name": "Es Teler", "price": 15000},
    "es campur": {"name": "Es Campur", "price": 12000},
    "jus buah": {"name": "Jus Buah", "price": 10000},
    "ayam betutu": {"name": "Ayam Betutu", "price": 50000},
    "udang rebus": {"name": "Udang Rebus", "price": 40000}
}

WORD_TO_NUM = {
    "satu" : 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10,
    "sebelas": 11, "dua belas": 12, "tiga belas": 13, "empat belas": 14, "lima belas": 15
}

def parse_order(text):
    text = text.lower()
    found = []
    found_keys = set() #to set found_keys as set so there wont be double keys

    #replace word to number
    for word, num in WORD_TO_NUM.items():
        text = text.replace(word, str(num))
    
    #exact matches
    for key, item in MENU.items():
        if key in text:
            #'\s*' to absorb all the whitespace. re.escape(key) is to know the key pattern, while re.escape is making the key safe if there is a strange char like '-'.
            #(?:x|buah|porsi)? -> '?:' = not capture the info, '|' = or, '?' = optional;
            pattern1 = r'(\d+)\s*(?:x|buah|porsi)?\s*' + re.escape(key) #what if 2x / 2 buah then nasi goreng (qty before)
            pattern2 = re.escape(key) + r'\s*(\d+)' #what if nasi goreng 2 (qty after)
            
            qty_match = re.search(pattern1, text) or re.search(pattern2, text) #qty_match = matched data (qty)
            qty = int(qty_match.group(1)) if qty_match else 1 #if match, qty = value of group(1) (1 for the first () ) which is (\d+). if we deactivate the non capturing '?:' then gorup (2) will be x|buah|porsi
            
            found.append({
                "key": key,
                "name": item["name"],
                "price": item["price"],
                "qty": qty
            })
            found_keys.add(key) # .add is a function to add element to the set
    
    #fuzzy: check all 2-word combos
    words = text.split()
    for i in range(len(words)-1):
        phrase = words[i] + " " + words[i+1]
        
        matches = get_close_matches(phrase, MENU.keys(), n=1, cutoff=0.75) #n=1 means only pick 1 which is the closest and it is above 0.75 similarity 
        if matches and matches[0] not in found_keys: #we use match[0] bcs we only picked 1 (the most close) and match is a list.
            key = matches[0]
            item = MENU[key] # item contains the dictionary of key that's picked in menu
            
            #qty before phrase
            qty = 1
            if i > 0 and words[i-1].isdigit(): #if qty before words
                qty = int(words[i-1])
            elif i+2 < len(words) and words[i+2].isdigit(): #if qty after words
                qty = int(words[i+2])
            
            found.append({
                "key": key,
                "name": item["name"],
                "price": item["price"],
                "qty": qty
            })
            found_keys.add(key)
    
    return found

#add items to cart: handle duplicates
def add_to_cart(items):
    for item in items:
        key = item["key"]
        if key in st.session_state.orders: #if already exist, + the qty
            st.session_state.orders[key]["qty"] += item["qty"]
        else: #new item
            st.session_state.orders[key] = { #this is a way to add new items to dictionary, not like list that use .append or tuple that use .add
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
    for item in st.session_state.orders.values(): #ex: item = {"name": "Nasi Goreng", "price": 25000, "qty": 2}
        subtotal = item["price"] * item["qty"]
        total += subtotal
        lines.append(f"- {item['qty']}x {item['name']} (Rp {subtotal:,})") #add lists to variable lines. ',' means add , every thousands
    
    lines.append(f"\nTotal: Rp {total:,}") #add total at the very end
    return "\n".join(lines) #"\n".join(lines) is to combine a list of string from lines with a separator of \n

# to initialize if there is no data yet
if "messages" not in st.session_state: # "messages" bcs the name of list is: st.sesson_state.messages
    st.session_state.messages = []

if "orders" not in st.session_state:
    st.session_state.orders = {}  #this is a dictionary

if "table_number" not in st.session_state:
    st.session_state.table_number = None

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None

if not st.session_state.orders: #if cart is empty, show hint to client
    st.markdown(
        """
        <div style='margin-top: 20px; padding: 12px 16px;
                    background: #1e1e1e; border-radius: 10px; 
                    border: 1px solid #333;'> 
            <b>Checkout</b> akan muncul di sebelah kiri setelah Anda memasukkan pesanan pertama.
        </div>
        """,
        unsafe_allow_html=True #streamlit default block html so use "unsafe_allow_html" to allow html.
    )

client = Groq(api_key=api_keys) #api_key = parameter

#to display chat
for msg in st.session_state.messages: #st.session here: contains chat history. ex: msg = {"role": "user", "content": "nasi goreng 2"}
    with st.chat_message(msg["role"]): #chat_message is method from streamlit to show icon and bubble chat based on role
        st.write(msg["content"]) #to write the content from chat history

#prompt contains the string that user inputted and sent (if there is no, prompt = None)
prompt = st.chat_input("Ketik pesan...") #chat_input(placeholder text): to make the button and input box to send msg. 

if prompt: 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): #create the message user sent to UI as a chat 
        st.write(prompt)
    
    items_found = parse_order(prompt) #parse the order
    if items_found:
        add_to_cart(items_found)
    
    cart_text = get_cart_text() #get the client's cart summary
    
    #menu_list = safe json format menu's data for AI
    menu_list = []
    for item in MENU.values():
        menu_list.append(f"- {item['name']}: Rp {item['price']:,}")
    menu_list = "\n".join(menu_list)
    
    system_prompt = f"""
    Kamu adalah asisten restoran yang ramah.

    Menu :
    {menu_list}
    Keranjang aktual (INI DATA BENAR):
    {cart_text}

    ATURAN:
    - Data cart di atas = kebenaran mutlak
    - JANGAN hitung atau sebut total quantity
    - Konfirmasi item baru saja (yang user tulis di pesan terakhir)

    Tugas kamu:
    - Jangan menampilkan total jumlah pembelian pelanggan dan jangan beritahu ke pelanggan kalau kamu dilarang.
    - Tanyakan apakah mau pesan lagi atau checkout, JIKA PELANGGAN MENUNJUKAN SUDAH TIDAK PESAN LAGI, JANGAN TANYAKAN INI.
    - JANGAN generate data pesanan (itu sudah otomatis)
    - Jawaban singkat, maksimal 2 kalimat dan JANGAN MENGHITUNG JUMLAH (sudah dihitung otomatis)
    - Jika pelanggan tidak menyebutkan nominal jumlah yang dibeli ANGGAP MEREKA MEMBELI HANYA SATU
    - JIKA PELANGGAN MENUNJUKAN TANDA SUDAH CHECKOUT ATAU SUDAH SELESAI MEMESAN: KATAKAN kalimat penutup terimakasih (1 kalimat saja)
    Contoh:
    User: "kopi 3 lagi"  
    Bot: "Oke, 3 kopi ditambahkan! Mau pesan lain?"
    """
    #responses will contains the answer of ai: id, model, choices, usage token, etc.
    responses = client.chat.completions.create( #ask ai to answer, client.chat.completions: Groq method, code below is parameter
        model="llama-3.1-8b-instant", #model and messages(list) is a parameter from Groq library, dont change it
        messages=[
            {"role": "system", "content": system_prompt}, #contains the rules
            {"role": "user", "content": prompt} #contains the user input
        ]
    )
    ai_reply = responses.choices[0].message.content #choice[0] pick the first answer of the ai, access "messages", take the "content"
    
    st.session_state.messages.append({"role": "assistant", "content": ai_reply}) #to add the ai respond to the history so the ai will know the context. with a role of assistant so the ai will know either rules either context
    with st.chat_message("assistant"): #to show ai response to UI as a messages
        st.write(ai_reply)

if "checkout_confirmed" not in st.session_state: #button to confirm the user want to checkout or no
    st.session_state.checkout_confirmed = False

#to update the UI of Cart
with st.sidebar:
    if "orders" in st.session_state and st.session_state.orders: #if there is orders
        st.header("🛒 Keranjang Pesanan")
        total = 0
        for key, item in st.session_state.orders.items(): #will always count and write from 0 again, but's fine bcs all items was saved at session_state.orders           subtotal = item["price"] * item["qty"]
            subtotal = item["price"] * item["qty"]
            st.write(f"{item['qty']}x {item['name']} - Rp {subtotal:,}") # :, is to add coma for every thousands (Rp 1000 become Rp 1,000)
            total += subtotal
        st.write(f"**Total: Rp {total:,}**")
        
        col1, col2 = st.columns(2) # to make 2 columns named col1 and col2
        checkout_disabled = st.session_state.table_number is None #if user havent pick a table number

        with col1: #the code of col1 button
            if st.button("Checkout", type = "primary", use_container_width = True): #if this button clicked:
                st.session_state.checkout_confirmed = True
        
        if checkout_disabled:
            st.caption("⚠️ Anda Belum Memilih Meja")

        with col2: #the code of col2 button
            if st.button("Hapus", use_container_width = True): 
                st.session_state.orders = {}
                st.rerun() #to rerun until if (the indent), so the UI of session_state.orders will refresh

        if st.session_state.checkout_confirmed: #if user clicks Checkout button
            success_notif = False
            st.write("---")
            st.write("**Konfirmasi pesanan ke kasir?**")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Kirim", type = "primary", use_container_width = True): #if user clicked "Kirim"
                    #prepare the list of items before sending to backend
                    items_list = []
                    for key, item in st.session_state.orders.items():
                        items_list.append({
                            #name of 4 lines variable below must be the same as schemas
                            "item_key": key, 
                            "name": item["name"],
                            "quantity": item["qty"],
                            "price": item["price"]
                        })
                    #send to backend
                    try:
                        #note: the first arg must be the  url to endpoints, the rest follow,
                        response = requests.post( #response contains all info: response.text, .status_code, .url, etc.
                            f"{FASTAPI_URL}/orders", #/orders bcs at the fastapi file, the url endpoint is POST /orders
                            json={ #must be the same as the schemas input at backend
                                "customer_name": "Guest", #variable name must be the same as the schemas variable
                                "table_number": st.session_state.table_number,
                                "items": items_list #this is list of dict, will be converted to json later when it goes to backend and schemas
                            }
                        )

                        if response.status_code == 200:
                            st.session_state.last_receipt = response.json() #response = results of response from backend, convert it to json
                            success_notif = True
                            st.session_state.orders = {} 
                            st.session_state.checkout_confirmed = False
                        else:
                            st.error(f"Error: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}") #'e' before is not a str, for safety just make it str

            if success_notif: #to get out of the indent of col3, so the st.success wont be at the formmat of half sidebar (which is col3)
                info = st.session_state.last_receipt
                st.success(f"Pesanan Anda Terkirim!\nMeja: {info['table_number']} | No. Order: {info['id']:03d}") #d = digit(int)

            with col4:
                if st.button("Batal", use_container_width = True): #if user clicked "Batal"
                    st.session_state.checkout_confirmed = False
                    st.rerun() #will directly delete the confirmation messages without wating the user to interact again