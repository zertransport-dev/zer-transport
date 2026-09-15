import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime, timedelta

# Sayfa Yapılandırması (Mobil Uyumlu)
st.set_page_config(page_title="Zer Transport Pro", page_icon="🚚", layout="centered")

# Veri Dosyaları
DB_CLIENTS = "clients.csv"
DB_ORDERS = "orders.csv"
DB_SETTINGS = "settings.csv"
LOGO_PATH = "company_logo.png"

# Veri Yükleme Fonksiyonu
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

clients_df = load_data(DB_CLIENTS, ["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
orders_df = load_data(DB_ORDERS, ["Fatura No", "Müşteri", "Açıklama", "Tutar", "Tarih", "Vade Tarihi", "Durum", "Dil"])
settings_df = load_data(DB_SETTINGS, ["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta", "Telefon"])

# Ana Menü
st.title("🚚 Zer Transport Pro")
menu = st.selectbox("Menü Seçin", [
    "🏠 Ana Sayfa / Özet Pano", 
    "📄 Fatura & Auftrag Oluştur", 
    "👥 Müşteri Yönetimi", 
    "⚙️ Firma Ayarları", 
    "📷 CMR Tara & Gönder"
])

# --- 1. ANA SAYFA / ÖZET PANO ---
if menu == "🏠 Ana Sayfa / Özet Pano":
    st.subheader("📊 Finansal Özet & Bekleyenler")
    
    if not orders_df.empty:
        total_ciro = orders_df["Tutar"].sum()
        pending_df = orders_df[orders_df["Durum"] == "Bekliyor"]
        
        col1, col2 = st.columns(2)
        col1.metric("Toplam Ciro", f"{total_ciro:.2f} €")
        col2.metric("Bekleyen Alacak", f"{pending_df['Tutar'].sum():.2f} €")
        
        st.markdown("---")
        st.subheader("📋 Tüm Faturalar ve Durumları")
        
        for index, row in orders_df.iterrows():
            with st.expander(f"{row['Fatura No']} - {row['Müşteri']} ({row['Tutar']} €) [{row['Durum']}]"):
                st.write(f"**Açıklama:** {row['Açıklama']}")
                st.write(f"**Tarih:** {row['Tarih']} | **Vade:** {row['Vade Tarihi']}")
                st.write(f"**Dil:** {row['Dil']}")
                
                c1, c2 = st.columns(2)
                if row['Durum'] == "Bekliyor":
                    if c1.button("Ödendi Olarak İşaretle", key=f"pay_{index}"):
                        orders_df.loc[index, "Durum"] = "Ödendi"
                        orders_df.to_csv(DB_ORDERS, index=False)
                        st.success("Durum güncellendi!")
                        st.rerun()
                else:
                    if c1.button("Bekliyor Olarak Değiştir", key=f"wait_{index}"):
                        orders_df.loc[index, "Durum"] = "Bekliyor"
                        orders_df.to_csv(DB_ORDERS, index=False)
                        st.success("Durum güncellendi!")
                        st.rerun()
                        
                if c2.button("Faturayı Sil", key=f"del_{index}"):
                    orders_df = orders_df.drop(index).reset_index(drop=True)
                    orders_df.to_csv(DB_ORDERS, index=False)
                    st.warning("Fatura silindi!")
                    st.rerun()
    else:
        st.info("Henüz kayıtlı fatura veya işlem bulunmuyor.")

# --- 2. FATURA & AUFTRAG OLUŞTUR ---
elif menu == "📄 Fatura & Auftrag Oluştur":
    st.subheader("📄 Profesyonel Fatura / Auftrag Hazırla")
    
    if clients_df.empty:
        st.warning("Önce 'Müşteri Yönetimi' sekmesinden en az bir müşteri eklemelisiniz.")
    else:
        with st.form("invoice_form"):
            inv_client = st.selectbox("Müşteri Seç", clients_df["Müşteri Adı"].tolist())
            doc_type = st.selectbox("Belge Türü", ["Fatura (Rechnung)", "Auftrag / Sipariş Onayı"])
            lang = st.selectbox("Belge Dili", ["Almanca (Deutsch)", "Türkçe"])
            inv_no = st.text_input("Belge No", value=f"ZT-{datetime.now().strftime('%Y%m%d%H%M')}")
            inv_desc = st.text_area("Hizmet / Rota Açıklaması (Örn: Linz - Viyana Express Taşıma)")
            inv_amount = st.number_input("Tutar (€)", min_value=0.0, step=10.0)
            vade_gun = st.slider("Ödeme Vadesi (Gün)", 0, 30, 14)
            
            create_btn = st.form_submit_button("Modern Belgeyi Oluştur")
            
            if create_btn:
                comp = settings_df.iloc[0].to_dict() if not settings_df.empty else {
                    "Firma Adi": "Kaan Transport", "Adres": "Attnang-Puchheim, Austria", "Vergi No": "ATU12345678", "IBAN": "AT61 0000 0000 0000 0000", "E-posta": "office@kaantransport.at", "Telefon": "+43 676 0000000"
                }
                client_row = clients_df[clients_df["Müşteri Adı"] == inv_client].iloc[0]
                
                tarih_str = datetime.now().strftime('%Y-%m-%d')
                vade_str = (datetime.now() + timedelta(days=vade_gun)).strftime('%Y-%m-%d')
                
                new_order = pd.DataFrame([[inv_no, inv_client, inv_desc, inv_amount, tarih_str, vade_str, "Bekliyor", lang]], 
                                       columns=["Fatura No", "Müşteri", "Açıklama", "Tutar", "Tarih", "Vade Tarihi", "Durum", "Dil"])
                orders_df = pd.concat([orders_df, new_order], ignore_index=True)
                orders_df.to_csv(DB_ORDERS, index=False)
                
                st.session_state["last_doc"] = {
                    "type": doc_type,
                    "no": inv_no,
                    "client": inv_client,
                    "desc": inv_desc,
                    "amount": inv_amount,
                    "tarih": tarih_str,
                    "vade": vade_str,
                    "yetkili": str(client_row["Yetkili"]),
                    "telefon": str(client_row["Telefon"]),
                    "adres": str(client_row["Adres"]),
                    "comp_name": str(comp.get("Firma Adi", "Kaan Transport")),
                    "comp_addr": str(comp.get("Adres", "")),
                    "comp_tax": str(comp.get("Vergi No", "")),
                    "comp_iban": str(comp.get("IBAN", "")),
                    "comp_mail": str(comp.get("E-posta", "")),
                    "comp_tel": str(comp.get("Telefon", ""))
                }
                st.success("✅ Belge başarıyla oluşturuldu ve kaydedildi!")

    if "last_doc" in st.session_state:
        doc = st.session_state["last_doc"]
        st.markdown("---")
        
        # Modern Kurumsal Fatura HTML / CSS Şablonu
        modern_invoice_html = f"""
        <style>
            .invoice-box {{
                max-width: 800px;
                margin: auto;
                padding: 30px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #ffffff;
                color: #333333;
                border-radius: 8px;
            }}
            .invoice-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                border-bottom: 2px solid #2C3E50;
                padding-bottom: 20px;
                margin-bottom: 20px;
            }}
            .company-info h2 {{
                color: #2C3E50;
                margin: 0 0 5px 0;
                font-size: 24px;
            }}
            .company-info p, .invoice-details p, .client-info p {{
                margin: 3px 0;
                font-size: 14px;
                color: #555555;
            }}
            .invoice-title {{
                text-align: right;
            }}
            .invoice-title h1 {{
                color: #2C3E50;
                margin: 0;
                font-size: 26px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .invoice-grid {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }}
            .client-box, .meta-box {{
                width: 48%;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #2C3E50;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            .items-table th {{
                background-color: #2C3E50;
                color: white;
                text-align: left;
                padding: 12px;
                font-size: 14px;
            }}
            .items-table td {{
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
                font-size: 14px;
            }}
            .total-section {{
                text-align: right;
                margin-top: 20px;
            }}
            .total-section h3 {{
                color: #2C3E50;
                font-size: 22px;
                margin: 0;
            }}
            .footer-note {{
                margin-top: 40px;
                padding-top: 15px;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #777777;
                text-align: center;
            }}
            @media print {{
                body {{ background: transparent; }}
                .invoice-box {{ border: none; box-shadow: none; padding: 0; }}
            }}
        </style>

        <div class="invoice-box">
            <div class="invoice-header">
                <div class="company-info">
                    <h2>🚚 {doc['comp_name']}</h2>
                    <p>{doc['comp_addr']}</p>
                    <p>Tel: {doc['comp_tel']} | E-posta: {doc['comp_mail']}</p>
                    <p>Steuer-Nr: {doc['comp_tax']}</p>
                </div>
                <div class="invoice-title">
                    <h1>{doc['type']}</h1>
                    <p><b>Belge No:</b> {doc['no']}</p>
                    <p><b>Tarih:</b> {doc['tarih']}</p>
                    <p><b>Vade Tarihi:</b> {doc['vade']}</p>
                </div>
            </div>

            <div class="invoice-grid">
                <div class="client-box">
                    <p><b>Müşteri / Auftraggeber:</b></p>
                    <p style="font-size: 16px; font-weight: bold; color: #222;">{doc['client']}</p>
                    <p>Yetkili: {doc['yetkili']}</p>
                    <p>Adres: {doc['adres']}</p>
                </div>
                <div class="meta-box">
                    <p><b>Ödeme Bilgileri / Zahlung:</b></p>
                    <p><b>IBAN:</b> {doc['comp_iban']}</p>
                    <p><b>Vade Süresi:</b> {vade_gun} Gün</p>
                    <p><b>Durum:</b> Bekliyor / Offen</p>
                </div>
            </div>

            <table class="items-table">
                <thead>
                    <tr>
                        <th>Açıklama / Leistung & Beschreibung</th>
                        <th style="text-align: right;">Tutar / Betrag</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{doc['desc']}</td>
                        <td style="text-align: right;"><b>{doc['amount']:.2f} €</b></td>
                    </tr>
                </tbody>
            </table>

            <div class="total-section">
                <h3>Gesamtbetrag / Toplam: {doc['amount']:.2f} €</h3>
            </div>

            <div class="footer-note">
                <p>Ödemenin yukarıdaki IBAN adresine vade tarihine kadar havale edilmesi rica olunur. İyi çalışmalar dileriz!</p>
                <p>{doc['comp_name']} — Professional Transport & Express Logistics</p>
            </div>
        </div>
        """
        
        st.markdown(modern_invoice_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("💡 **PDF Olarak Kaydetmek İçin:** Klavyenizden **Ctrl + P** tuşlarına basın, açılan pencerede hedef olarak **'PDF olarak kaydet' (Save as PDF)** seçeneğini seçin. Sayfa tamamen şık bir kurumsal PDF faturaya dönüşecektir.")
        
        wa_text = f"Merhaba {doc['yetkili']}, {doc['no']} nolu ve {doc['amount']} EUR tutarındaki taşıma belgeniz hazırdır. İyi çalışmalar dileriz - {doc['comp_name']}."
        st.markdown(f"📱 **WhatsApp ile Gönder:** [Tıklayın](https://wa.me/{doc['telefon'].replace(' ', '')}?text={urllib.parse.quote(wa_text)})", unsafe_allow_html=True)

# --- 3. MÜŞTERİ YÖNETİMİ ---
elif menu == "👥 Müşteri Yönetimi":
    st.subheader("👥 Müşteri Listesi")
    with st.form("add_client_form"):
        c_name = st.text_input("Müşteri / Firma Adı")
        c_auth = st.text_input("Yetkili Kişi")
        c_mail = st.text_input("E-posta Adresi")
        c_phone = st.text_input("Telefon Numarası (Örn: +43676...)")
        c_addr = st.text_area("Adres")
        save_new = st.form_submit_button("Yeni Müşteri Kaydet")
        
        if save_new and c_name:
            new_c = pd.DataFrame([[c_name, c_auth, c_mail, c_phone, c_addr]], columns=["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
            clients_df = pd.concat([clients_df, new_c], ignore_index=True)
            clients_df.to_csv(DB_CLIENTS, index=False)
            st.success(f"{c_name} eklendi!")
            st.rerun()
            
    if not clients_df.empty:
        st.markdown("---")
        st.dataframe(clients_df, use_container_width=True)

# --- 4. FİRMA AYARLARI ---
elif menu == "⚙️ Firma Ayarları":
    st.subheader("⚙️ Firma Bilgileri & Logo")
    
    current = settings_df.iloc[0] if not settings_df.empty else {"Firma Adi": "Kaan Transport", "Adres": "Attnang-Puchheim", "Vergi No": "", "IBAN": "", "E-posta": "", "Telefon": ""}
    
    with st.form("settings_form"):
        f_adi = st.text_input("Firma Adı", value=current.get("Firma Adi", ""))
        f_adres = st.text_area("Firma Adresi", value=current.get("Adres", ""))
        f_vergi = st.text_input("Vergi / Steuernummer", value=current.get("Vergi No", ""))
        f_iban = st.text_input("IBAN", value=current.get("IBAN", ""))
        f_mail = st.text_input("E-posta", value=current.get("E-posta", ""))
        f_tel = st.text_input("Telefon", value=current.get("Telefon", ""))
        
        logo_file = st.file_uploader("Firma Logosu Yükle (PNG / JPG)", type=["png", "jpg", "jpeg"])
        
        save_set = st.form_submit_button("Ayarları Kaydet")
        
        if save_set:
            new_s = pd.DataFrame([[f_adi, f_adres, f_vergi, f_iban, f_mail, f_tel]], columns=["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta", "Telefon"])
            new_s.to_csv(DB_SETTINGS, index=False)
            if logo_file:
                with open(LOGO_PATH, "wb") as f:
                    f.write(logo_file.getbuffer())
            st.success("Ayarlar ve logo kaydedildi!")

# --- 5. CMR TARA & GÖNDER ---
elif menu == "📷 CMR Tara & Gönder":
    st.subheader("📷 CMR Belgesi Yükle")
    cmr_file = st.file_uploader("CMR Fotoğrafı", type=["jpg", "png", "jpeg"])
    if cmr_file:
        st.image(cmr_file, caption="Yüklenen Belge", use_column_width=True)
        st.success("CMR belgesi sisteme işlendi!")
