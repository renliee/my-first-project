import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq

st.set_page_config(page_title = "ChatBot Restaurant", page_icon = "🤖")

with st.sidebar:
    st.header("🍴 Tentang Restoran")
    st.write("**Nama:** Restoran Sedap Rasa")
    st.write("**Lokasi:** Jl. Angsoka Hijau V, Jakarta")
    st.write("**Jam Buka:** 10.00-22.00 WIB")
    st.write("---")
    st.subheader("👨‍💻 Developer")
    st.write("Dibuat oleh Ren Lie")
    st.write("Email: lierenatalie@email.com")

st.title("ChatBot Restaurant")
st.write("Halo! Saya bot yang akan membantu Anda menentukan pesanan!")

api_key = os.getenv("GROQ_API_KEY")

restaurant_info = """
Makanan
- Nasi Goreng Spesial: Nasi goreng dengan ayam, telur, dan sayuran, Rp 25.000
- Sate Ayam: Sate ayam dengan bumbu khas Jawa, Rp 20.000
- Mie Goreng: Mie goreng dengan ayam, telur, dan sayuran, Rp 22.000
- Gado-Gado: Sayuran tumis dengan tempe, tahu, dan bumbu khas, Rp 18.000
- Makaroni Salad: Makaroni dengan sayuran dan mayones, Rp 20.000

Minuman
- Kopi: Kopi khas arabika, Rp 8.000
- Teh: Teh hijau atau teh hitam, Rp 8.000
- Air Mineral: Air mineral segar dari sumber alami, Rp 5.000
- Es Teler: Es buah segar dengan sayuran, Rp 15.000
- Es Campur: Es buah dengan sirup, Rp 12.000
- Jus Buah: Jus buah segar dengan pilihan rasa, Rp 10.000

Menu Istimewa
- Ayam Betutu: Ayam betutu khas Bali, Rp 50.000
- Udang Rebus: Udang rebus dengan bumbu khas, Rp 40.000

Best Seller
- Nasi Goreng
- Kopi

Aturan kesimpulan pesanan (SANGAT PENTING. HARUS DIIKUTI!!!) :
JIKA KAMU YAKIN PELANGGAN MEMESAN MAKANAN, TULIS ORDER DENGAN KESIMPULAN INI:
- Pesanan harus ditulis PER BARIS. LANGSUNG ENTER UNTUK SETIAP PESANAN, format: {jumlah}x {nama} → Rp {harga} \n
- JANGAN tambahkan penjelasan di baris yang sama dengan pesanan
- Jika menu promo/gratis, tulis HANYA: {jumlah}x {nama}
- Total harga JANGAN ditulis, parser akan hitung sendiri

Aturan berbicara (PENTING):
- Jawaban harus singkat, ramah, dan mudah dipahami pelanggan.
- Jika pelanggan ragu, bantu mereka memilih menu populer.
- Jangan menyebut bahwa kamu adalah AI atau chatbot.
"""

#check if there is no chat history yet, making a list to store the next chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "orders" not in st.session_state:
    st.session_state.orders = []

def client_order(bot_msg):
    orders = []
    failed_lines = [] 
    lines = bot_msg.split("\n") #split is a function to make a string split to a list. ex: "saya makan ikan" become [saya,makan,ikan]
    for line in lines:
        if "x" in line:
            parts = line.split("x") # ex: "2x nasi goreng -> Rp 50.000" so parts[0] will be the amount
            try:
                jumlah = int(parts[0].strip()) #convert the "2" to integer. strip() is a function to erase the space before and after the string. " 2 " to "2" so the data will be clean
                rest = parts[1].strip()
                if "→" in rest:
                    nama, harga = rest.split("→") #the left one is name and the right one is price
                    harga = int(harga.replace("Rp", "").replace(".", "").strip()) #erase the Rp and . so it will be a clean data
                else:
                    nama = rest #incase there is a discount or error, system wont collapse
                    harga = 0
                orders.append({"nama" : nama.strip(), "jumlah" : jumlah, "harga" : harga}) #the format clean data
            except:
                failed_lines.append(line)
                continue
    return orders, failed_lines

chat_container = st.empty()

#Tulis semua history chat di dalam container yang berada di placeholder chat_container
with chat_container.container():
    for bot in st.session_state.chat_history:
        with st.chat_message(bot["role"]): #for every role icon massage, write the content next to it
            st.write(bot["content"]) 

client = Groq(api_key=api_key) #declare client as groq that has connected to Groq API server

user_input = st.text_input("Tanya pertanyaan tentang restoran:") #st.text_input is a function to store user's input
if st.button("Kirim") and user_input: #if button clicked and there is user_input
    with st.spinner("Sedang memikirkan jawaban..."):
        try:
            st.session_state.chat_history.append({"role" : "user", "content" : user_input}) #to save every user input in st.session_state.chat_history
            messages = [{
                            "role": "system",
                            "content": f"""Kamu adalah asisten restoran yang ramah dan profesional. Gunakan bahasa Indonesia yang alami dan sopan.
                            Berikut informasi restoran yang kamu tahu: {restaurant_info}"""}]
            
            messages += st.session_state.chat_history #to add the rules for system
            resp = client.chat.completions.create( #resp store the answer of Groq
                model = "llama-3.1-8b-instant", 
                messages = messages
            )
            answer = resp.choices[0].message.content #answer store the first answer of groq, bcs it can be multiple

            st.session_state.chat_history.append({"role" : "system", "content" : answer}) # to store every answer of groq to st.session_state.chat_history

            orders, failed = client_order(answer)
            st.session_state.orders = orders

            if st.session_state.orders:
                st.subheader("📋 Ringkasan Pesanan")
                total = 0
                for item in st.session_state.orders:
                    harga = item["harga"]
                    st.write(f'{item["jumlah"]}x {item["nama"]} → Rp {harga * item["jumlah"]}')
                    total += harga * item["jumlah"]
                st.write(f"**Total :** Rp {total}")

            with chat_container.container():
                for bot in st.session_state.chat_history: #for every chat in st.session, write it
                    with st.chat_message(bot["role"]): #st.chat_message only write every chat once, so wont be any doubled chat
                        st.write(bot["content"])

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")