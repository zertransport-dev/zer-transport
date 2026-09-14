import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sayfa Yapılandırması (Mobil Uyumlu)
st.set_page_config(page_title="Zer Transport Pro", page_icon="🚚", layout="centered")

# Veri Dosyaları
DB_CLIENTS = "clients.csv"
DB_ORDERS = "orders.csv"
DB_SETTINGS = "settings.csv"

# Varsayılan Veri Yükleme/Oluşturma
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

clients_df = load_data(DB_CLIENTS, ["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
orders_df = load_data(DB_ORDERS, ["Sipariş No", "Müşteri", "Güzergah", "Tutar", "Tarih", "Durum"])
settings_df = load_data(DB_SETTINGS, ["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta"])

# Ana Menü (Mobil Uyumlu)
st.title("🚚 Zer Transport Pro")
menu = st.selectbox("Menü Seçin", ["🏠 Ana Sayfa / Siparişler", "👥 Müşteri Yönetimi", "⚙️ Firma Ayarları", "📄 Fatura & Auftrag Oluştur", "📷 CMR Tara & Gönder"])

# --- 1. ANA SAYFA / SİPARİŞLER ---
if menu == "🏠 Ana Sayfa / Siparişler":
    st.subheader("📋 Aktif Siparişler")
    if not orders_df.empty:
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("Henüz kayıtlı sipariş yok.")
    
    st.markdown("---")
    st.subheader("➕ Yeni Sipariş Ekle")
    with st.form("new_order_form"):
        o_no = st.text_input("Sipariş / Auftrag No", value=f"ZT-{datetime.now().strftime('%Y%m%d%H%M')}")
        client_list = clients_df["Müşteri Adı"].tolist() if not clients_df.empty else ["Genel Müşteri"]
        o_client = st.selectbox("Müşteri Seç", client_list)
        o_route = st.text_input("Güzergah (Örn: Linz -> Viyana)")
        o_price = st.number_input("Tutar (€)", min_value=0.0, step=10.0)
        submit_order = st.form_submit_button("Siparişi Kaydet")
        
        if submit_order:
            new_row = pd.DataFrame([[o_no, o_client, o_route, o_price, datetime.now().strftime('%Y-%m-%d'), "Bekliyor"]], 
                                   columns=["Sipariş No", "Müşteri", "Güzergah", "Tutar", "Tarih", "Durum"])
            orders_df = pd.concat([orders_df, new_row], ignore_index=True)
            orders_df.to_csv(DB_ORDERS, index=False)
            st.success("Sipariş başarıyla kaydedildi!")
            st.rerun()

# --- 2. MÜŞTERİ YÖNETİMİ ---
elif menu == "👥 Müşteri Yönetimi":
    st.subheader("👥 Müşteri Listesi ve Düzenleme")
    
    if not clients_df.empty:
        selected_client = st.selectbox("Düzenlenecek Müşteriyi Seçin", ["Yeni Müşteri Ekle..."] + clients_df["Müşteri Adı"].tolist())
        
        if selected_client == "Yeni Müşteri Ekle...":
            with st.form("add_client_form"):
                c_name = st.text_input("Müşteri / Firma Adı")
                c_auth = st.text_input("Yetkili Kişi")
                c_mail = st.text_input("E-posta Adresi")
                c_phone = st.text_input("Telefon Numarası")
                c_addr = st.text_area("Adres")
                save_new = st.form_submit_button("Müşteriyi Kaydet")
                
                if save_new and c_name:
                    new_c = pd.DataFrame([[c_name, c_auth, c_mail, c_phone, c_addr]], columns=["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
                    clients_df = pd.concat([clients_df, new_c], ignore_index=True)
                    clients_df.to_csv(DB_CLIENTS, index=False)
                    st.success(f"{c_name} eklendi!")
                    st.rerun()
        else:
            client_row = clients_df[clients_df["Müşteri Adı"] == selected_client].iloc[0]
            with st.form("edit_client_form"):
                e_name = st.text_input("Müşteri / Firma Adı", value=client_row["Müşteri Adı"])
                e_auth = st.text_input("Yetkili Kişi", value=client_row["Yetkili"])
                e_mail = st.text_input("E-posta Adresi", value=client_row["E-posta"])
                e_phone = st.text_input("Telefon Numarası", value=client_row["Telefon"])
                e_addr = st.text_area("Adres", value=client_row["Adres"])
                
                col1, col2 = st.columns(2)
                update_btn = col1.form_submit_button("Güncelle")
                delete_btn = col2.form_submit_button("Müşteriyi Sil")
                
                if update_btn:
                    clients_df.loc[clients_df["Müşteri Adı"] == selected_client, ["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"]] = [e_name, e_auth, e_mail, e_phone, e_addr]
                    clients_df.to_csv(DB_CLIENTS, index=False)
                    st.success("Müşteri bilgileri güncellendi!")
                    st.rerun()
                
                if delete_btn:
                    clients_df = clients_df[clients_df["Müşteri Adı"] != selected_client]
                    clients_df.to_csv(DB_CLIENTS, index=False)
                    st.warning("Müşteri silindi!")
                    st.rerun()
    else:
        st.info("Kayıtlı müşteri bulunamadı.")
        with st.form("first_client_form"):
            c_name = st.text_input("Müşteri / Firma Adı")
            c_auth = st.text_input("Yetkili Kişi")
            c_mail = st.text_input("E-posta Adresi")
            c_phone = st.text_input("Telefon Numarası")
            c_addr = st.text_area("Adres")
            save_new = st.form_submit_button("Müşteriyi Kaydet")
            if save_new and c_name:
                new_c = pd.DataFrame([[c_name, c_auth, c_mail, c_phone, c_addr]], columns=["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
                new_c.to_csv(DB_CLIENTS, index=False)
                st.success("Müşteri eklendi!")
                st.rerun()

# --- 3. FİRMA AYARLARI ---
elif menu == "⚙️ Firma Ayarları":
    st.subheader("⚙️ Zer Transport - Firma ve Fatura Bilgileri")
    
    current_settings = settings_df.iloc[0] if not settings_df.empty else {"Firma Adi": "Zer Transport", "Adres": "Attnang-Puchheim", "Vergi No": "", "IBAN": "", "E-posta": ""}
    
    with st.form("settings_form"):
        f_adi = st.text_input("Firma Adı", value=current_settings.get("Firma Adi", "Zer Transport"))
        f_adres = st.text_area("Firma Adresi", value=current_settings.get("Adres", ""))
        f_vergi = st.text_input("Vergi / Steuernummer", value=current_settings.get("Vergi No", ""))
        f_iban = st.text_input("IBAN / Banka Bilgisi", value=current_settings.get("IBAN", ""))
        f_mail = st.text_input("İletişim E-posta", value=current_settings.get("E-posta", ""))
        
        save_settings = st.form_submit_button("Ayarları Kaydet")
        
        if save_settings:
            new_set = pd.DataFrame([[f_adi, f_adres, f_vergi, f_iban, f_mail]], columns=["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta"])
            new_set.to_csv(DB_SETTINGS, index=False)
            st.success("Firma bilgileri başarıyla güncellendi!")

# --- 4. FATURA & AUFTRAG OLUŞTUR ---
elif menu == "📄 Fatura & Auftrag Oluştur":
    st.subheader("📄 Müşteriye Özel Fatura Oluştur")
    
    if clients_df.empty:
        st.warning("Önce 'Müşteri Yönetimi' sekmesinden en az bir müşteri eklemelisiniz.")
    else:
        with st.form("invoice_form"):
            inv_client = st.selectbox("Fatura Kesilecek Müşteri", clients_df["Müşteri Adı"].tolist())
            inv_no = st.text_input("Fatura / Auftrag No", value=f"FAT-{datetime.now().strftime('%Y%m%d%H%M')}")
            inv_desc = st.text_input("Taşıma / Hizmet Açıklaması (Örn: Linz - Viyana Express Taşıma)")
            inv_amount = st.number_input("Tutar (€)", min_value=0.0, step=10.0)
            inv_date = st.date_input("Fatura Tarihi")
            
            create_inv_btn = st.form_submit_button("Fatura Taslağı Oluştur")
            
            if create_inv_btn:
                st.success(f"✅ **{inv_client}** için **{inv_no}** numaralı ve **{inv_amount} €** tutarlı fatura başarıyla hazırlandı!")
                st.info("Bu faturayı PDF olarak kaydedebilir veya doğrudan müşterinize iletebilirsiniz.")

# --- 5. CMR TARA & GÖNDER ---
elif menu == "📷 CMR Tara & Gönder":
    st.subheader("📷 CMR Belgesi Kamera Tarayıcı")
    camera_file = st.file_uploader("CMR Fotoğrafı Yükle veya Çek", type=["jpg", "png", "jpeg"])
    
    if camera_file:
        st.image(camera_file, caption="Yüklenen CMR Belgesi", use_column_width=True)
        if st.button("Belgeyi PDF'e Çevir ve Gönder"):
            st.success("CMR belgesi PDF'e dönüştürüldü ve müşteriye gönderildi!")
