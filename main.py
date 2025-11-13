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
    st.write("Dibuat oleh Renata Lie")
    st.write("Email: lierenatalie@email.com")

st.title("ChatBot Restaurant")
st.write("Halo! Saya bot yang akan membantu Anda menentukan pesanan!")

api_key = os.getenv("GROQ_API_KEY")

restaurant_info = """
Selamat datang di restoran kami! Kami memiliki berbagai menu yang lezat dan segar untuk dipilih. Berikut beberapa opsi menu yang kami tawarkan:

🍛 Makanan Hangat
- Nasi Goreng Spesial: Nasi goreng dengan ayam, telur, dan sayuran, Rp 25.000
- Sate Ayam: Sate ayam dengan bumbu khas Jawa, Rp 20.000
- Mie Goreng: Mie goreng dengan ayam, telur, dan sayuran, Rp 22.000
- Gado-Gado: Sayuran tumis dengan tempe, tahu, dan bumbu khas, Rp 18.000

🍧 Makanan Non-Hangat
- Es Teler: Es buah segar dengan sayuran, Rp 15.000
- Es Campur: Es buah dengan sirup, Rp 12.000
- Jus Buah: Jus buah segar dengan pilihan rasa, Rp 10.000

☕ Minuman
- Kopi: Kopi khas arabika, Rp 8.000
- Teh: Teh hijau atau teh hitam, Rp 8.000
- Air Mineral: Air mineral segar dari sumber alami, Rp 5.000

🍝 Pasta dan Makaroni
- Spaghetti Aglio Olio: Pasta spaghetti dengan bumbu aglio olio, Rp 25.000
- Makaroni Salad: Makaroni dengan sayuran dan mayones, Rp 20.000

🌟 Menu Istimewa
- Ayam Betutu: Ayam betutu khas Bali, Rp 50.000
- Udang Rebus: Udang rebus dengan bumbu khas, Rp 40.000

💸 Harga Promo
- Makanan hangat 1+1 Rp 10.000
- Minuman 1+1 Rp 5.000

💸 Best Seller
- Nasi Goreng
- Kopi
"""

#check if there is no chat history yet, making a list to store the next chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_container = st.empty()

with chat_container.container():
    for bot in st.session_state.chat_history:
        with st.chat_message(bot["role"]):
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
                            Berikut informasi restoran yang kamu tahu: {restaurant_info}
                            Aturan berbicara:
                            - Jawaban harus singkat, ramah, dan mudah dipahami pelanggan.
                            - Jika ada promo seperti '1+1', jelaskan maksudnya dengan kata 'gratis' atau 'bonus', jangan gunakan kata seperti 'mencetak'.
                            - Jika pelanggan memesan makanan, tuliskan ringkasan pesanan dan total harga.
                            - Jika pelanggan ragu, bantu mereka memilih menu populer.
                            - Jangan menyebut bahwa kamu adalah AI atau chatbot.
                            """}]
            
            messages += st.session_state.chat_history #to add the rules for system
            resp = client.chat.completions.create( #resp store the answer of Groq
                model = "llama-3.1-8b-instant", 
                messages = messages
            )
            answer = resp.choices[0].message.content #answer store the first answer of groq, bcs it can be multiple

            st.session_state.chat_history.append({"role" : "system", "content" : answer}) # to store every answer of groq to st.session_state.chat_history
            with chat_container.container():
                for bot in st.session_state.chat_history: #for every chat in st.session, write it
                    with st.chat_message(bot["role"]): #st.chat_message only write every chat once, so wont be any doubled chat
                        st.write(bot["content"])

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")