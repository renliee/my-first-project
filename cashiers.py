import streamlit as st
import requests

st.set_page_config(page_title="Cashier's Dashboard", page_icon="🧾", layout="wide")

FASTAPI_URL = "http://127.0.0.1:8000"

st.title("🧾 Cashier's Dashboard")

filter_status = st.selectbox(
    "Filter Status", options = ["semua", "pending", "processing", "completed"]
)
st.write("---")

@st.fragment(run_every=10) #a decoration method from streamlit to refresh only function below every 10 secs
def show_orders():
    response = requests.get(f"{FASTAPI_URL}/orders")

    if response.status_code == 200:
        orders = response.json() #orders now contains the response of get all orders in backend
        if not orders: #if no response 
            st.info("Belum ada pesanan")
        else:
            if filter_status == "semua":
                filtered_orders = orders
            else:
                filtered_orders = []
                for order in orders:
                    if order['status'] == filter_status:
                        filtered_orders.append(order)

            for order in filtered_orders: #for every order
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"**Order: {order['id']:03d}** | Meja {order['table_number']} | Status: {order['status']} | Rp {order['total']:,}")
                    with st.expander("Lihat detail"): #st.expander: to expand the info of code below when clicked
                        for item in order['items']: #for each item in order items list
                            st.write(f"- {item['quantity']}x {item['name']} Rp {item['price']:,}")
                with col2:
                    if order['status'] == "pending":
                        if st.button("Proses", key=f"process_{order['id']}"): #"key" is a unique key, so if user clicked button with a key of "process_3" then streamlit will request to patch status of order's id == 3
                            requests.patch(f"{FASTAPI_URL}/orders/{order['id']}/status", json={"status":"processing"}) #the url endpoints, then json = the body to be sent to backend
                            st.rerun()
                with col3:
                    if order['status'] == "pending" or order['status'] == "processing":
                        if st.button("Selesai", key=f"done_{order['id']}"):
                            requests.patch(f"{FASTAPI_URL}/orders/{order['id']}/status", json={"status":"completed"})
                            st.rerun()
                st.write("---")
    else:
        st.error("Gagal mengambil data order")

show_orders()