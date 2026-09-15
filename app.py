
    import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
        paid_df = orders_df[orders_df["Durum"] == "Ödendi"]
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
            
            create_btn = st.form_submit_button("PDF Belgesi Oluştur")
            
            if create_btn:
                comp = settings_df.iloc[0] if not settings_df.empty else {"Firma Adi": "Zer Transport", "Adres": "Attnang-Puchheim", "Vergi No": "", "IBAN": "", "E-posta": "", "Telefon": ""}
                client_row = clients_df[clients_df["Müşteri Adı"] == inv_client].iloc[0]
                
                tarih_str = datetime.now().strftime('%Y-%m-%d')
                vade_str = (datetime.now() + timedelta(days=vade_gun)).strftime('%Y-%m-%d')
                
                new_order = pd.DataFrame([[inv_no, inv_client, inv_desc, inv_amount, tarih_str, vade_str, "Bekliyor", lang]], 
                                       columns=["Fatura No", "Müşteri", "Açıklama", "Tutar", "Tarih", "Vade Tarihi", "Durum", "Dil"])
                orders_df = pd.concat([orders_df, new_order], ignore_index=True)
                orders_df.to_csv(DB_ORDERS, index=False)
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                elements = []
                styles = getSampleStyleSheet()
                
                if os.path.exists(LOGO_PATH):
                    from reportlab.platypus import Image
                    elements.append(Image(LOGO_PATH, width=120, height=50))
                    elements.append(Spacer(1, 10))
                
                title_text = "RECHNUNG / FATURA" if "Fatura" in doc_type else "AUFTRAG / SEFER ONAYI"
                elements.append(Paragraph(f"<b>{comp.get('Firma Adi', 'Zer Transport')}</b>", styles['Heading1']))
                elements.append(Paragraph(f"{comp.get('Adres', '')} | Tel: {comp.get('Telefon', '')} | E-mail: {comp.get('E-posta', '')}", styles['Normal']))
                elements.append(Paragraph(f"Steuer-Nr / Vergi No: {comp.get('Vergi No', '')} | IBAN: {comp.get('IBAN', '')}", styles['Normal']))
                elements.append(Spacer(1, 20))
                
                elements.append(Paragraph(f"<b>{title_text}</b>", styles['Heading2']))
                elements.append(Paragraph(f"<b>Belge No:</b> {inv_no} | <b>Tarih:</b> {tarih_str} | <b>Vade:</b> {vade_str}", styles['Normal']))
                elements.append(Spacer(1, 15))
                
                elements.append(Paragraph(f"<b>Müşteri / Auftraggeber:</b>", styles['Heading3']))
                elements.append(Paragraph(f"<b>{client_row['Müşteri Adı']}</b><br/>Yetkili: {client_row['Yetkili']}<br/>Adres: {client_row['Adres']}<br/>E-posta: {client_row['E-posta']}", styles['Normal']))
                elements.append(Spacer(1, 20))
                
                data = [
                    ["Açıklama / Leistung", "Tutar / Betrag"],
                    [inv_desc, f"{inv_amount:.2f} €"],
                    ["Toplam / Gesamt", f"{inv_amount:.2f} €"]
                ]
                t = Table(data, colWidths=[380, 120])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9F9")),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 30))
                
                elements.append(Paragraph(f"Ödemeyi lütfen yukarıdaki IBAN numarasına {vade_gun} gün içinde gerçekleştiriniz. İyi çalışmalar dileriz!", styles['Normal']))
                
                doc.build(elements)
                pdf_data = buffer.getvalue()
                
                st.success(f"✅ Belge başarıyla oluşturuldu!")
                
                st.download_button(
                    label="📥 PDF Olarak İndir",
                    data=pdf_data,
                    file_name=f"{inv_no}.pdf",
                    mime="application/pdf"
                )
                
                wa_text = f"Merhaba {client_row['Yetkili']}, {inv_no} nolu ve {inv_amount} EUR tutarındaki taşıma belgeniz hazırdır. İyi çalışmalar dileriz - Zer Transport."
                st.markdown(f"📱 **WhatsApp ile Gönder:** [Tıklayın](https://wa.me/{client_row['Telefon'].replace(' ', '')}?text={urllib.parse.quote(wa_text)})", unsafe_allow_html=True)

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
    
    current = settings_df.iloc[0] if not settings_df.empty else {"Firma Adi": "Zer Transport", "Adres": "Attnang-Puchheim", "Vergi No": "", "IBAN": "", "E-posta": "", "Telefon": ""}
    
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
