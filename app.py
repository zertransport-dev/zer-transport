import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Zer Transport Pro", page_icon="🚚", layout="centered")

DB_CLIENTS = "clients.csv"
DB_ORDERS = "orders.csv"
DB_SETTINGS = "settings.csv"
LOGO_PATH = "company_logo.png"

def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

clients_df = load_data(DB_CLIENTS, ["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
orders_df = load_data(DB_ORDERS, ["Fatura No", "Müşteri", "Açıklama", "Netto", "MwSt (%)", "Brutto", "Tarih", "Vade Tarihi", "Durum"])
settings_df = load_data(DB_SETTINGS, ["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta", "Telefon"])

st.title("🚚 Zer Transport Pro")
menu = st.selectbox("Menü Seçin", [
    "🏠 Ana Sayfa / Özet Pano", 
    "📄 Fatura & Auftrag Oluştur", 
    "👥 Müşteri Yönetimi", 
    "⚙️ Firma Ayarları", 
    "📷 CMR Tara & Gönder"
])

if menu == "🏠 Ana Sayfa / Özet Pano":
    st.subheader("📊 Finanzübersicht / Finansal Özet")
    if not orders_df.empty:
        total_ciro = orders_df["Brutto"].sum()
        pending_df = orders_df[orders_df["Durum"] == "Offen (Bekliyor)"]
        
        col1, col2 = st.columns(2)
        col1.metric("Gesamtumsatz (Toplam Brüt Ciro)", f"{total_ciro:.2f} €")
        col2.metric("Offene Forderungen (Bekleyen)", f"{pending_df['Brutto'].sum():.2f} €")
        
        st.markdown("---")
        st.subheader("📋 Rechnungen & Aufträge")
        
        for index, row in orders_df.iterrows():
            with st.expander(f"{row['Fatura No']} - {row['Müşteri']} ({row['Brutto']} €) [{row['Durum']}]"):
                st.write(f"**Beschreibung / Açıklama:** {row['Açıklama']}")
                st.write(f"**Netto:** {row['Netto']} € | **MwSt:** {row['MwSt (%)']}% | **Brutto:** {row['Brutto']} €")
                st.write(f"**Datum:** {row['Tarih']} | **Fälligkeit:** {row['Vade Tarihi']}")
                
                c1, c2 = st.columns(2)
                if row['Durum'] == "Offen (Bekliyor)":
                    if c1.button("Als Bezahlt Markieren", key=f"pay_{index}"):
                        orders_df.loc[index, "Durum"] = "Bezahlt (Ödendi)"
                        orders_df.to_csv(DB_ORDERS, index=False)
                        st.success("Status aktualisiert!")
                        st.rerun()
                else:
                    if c1.button("Als Offen Markieren", key=f"wait_{index}"):
                        orders_df.loc[index, "Durum"] = "Offen (Bekliyor)"
                        orders_df.to_csv(DB_ORDERS, index=False)
                        st.success("Status aktualisiert!")
                        st.rerun()
                        
                if c2.button("Löschen (Sil)", key=f"del_{index}"):
                    orders_df = orders_df.drop(index).reset_index(drop=True)
                    orders_df.to_csv(DB_ORDERS, index=False)
                    st.warning("Dokument gelöscht!")
                    st.rerun()
    else:
        st.info("Noch keine Rechnungen vorhanden.")

elif menu == "📄 Fatura & Auftrag Oluştur":
    st.subheader("📄 Rechnung / Auftragsbestätigung Erstellen")
    
    if clients_df.empty:
        st.warning("Bitte fügen Sie zuerst einen Kunden im Menü 'Kundenverwaltung' hinzu.")
    else:
        with st.form("invoice_form"):
            inv_client = st.selectbox("Kunde / Müşteri Seç", clients_df["Müşteri Adı"].tolist())
            doc_type = st.selectbox("Dokumententyp / Belge Türü", ["Rechnung (Fatura)", "Auftragsbestätigung (Sipariş Onayı)"])
            inv_no = st.text_input("Dokumenten-Nr / Belge No", value=f"ZT-{datetime.now().strftime('%Y%m%d%H%M')}")
            inv_desc = st.text_area("Leistungsbeschreibung / Rota ve Hizmet Açıklaması (Örn: Express Transport Linz - Wien)")
            net_amount = st.number_input("Nettobetrag (€) / Netto Tutar", min_value=0.0, step=10.0)
            mwst_rate = st.selectbox("MwSt. (%) / KDV Oranı", [0.0, 10.0, 13.0, 20.0], index=3) # Standart Avusturya KDV %20
            vade_gun = st.slider(" Zahlungsziel (Tage) / Vade Süresi (Gün)", 0, 30, 14)
            
            create_btn = st.form_submit_button("Dokument Generieren (Belgeyi Oluştur)")
            
            if create_btn:
                mwst_amount = net_amount * (mwst_rate / 100.0)
                gross_amount = net_amount + mwst_amount
                
                comp = settings_df.iloc[0].to_dict() if not settings_df.empty else {
                    "Firma Adi": "Zer Transport", "Adres": "Attnang-Puchheim, Austria", "Vergi No": "ATU12345678", "IBAN": "AT61 0000 0000 0000 0000", "E-posta": "office@zertransport.at", "Telefon": "+43 676 0000000"
                }
                client_row = clients_df[clients_df["Müşteri Adı"] == inv_client].iloc[0]
                
                tarih_str = datetime.now().strftime('%Y-%m-%d')
                vade_str = (datetime.now() + timedelta(days=vade_gun)).strftime('%Y-%m-%d')
                
                new_order = pd.DataFrame([[inv_no, inv_client, inv_desc, net_amount, mwst_rate, gross_amount, tarih_str, vade_str, "Offen (Bekliyor)"]], 
                                       columns=["Fatura No", "Müşteri", "Açıklama", "Netto", "MwSt (%)", "Brutto", "Tarih", "Vade Tarihi", "Durum"])
                orders_df = pd.concat([orders_df, new_order], ignore_index=True)
                orders_df.to_csv(DB_ORDERS, index=False)
                
                st.session_state["last_doc"] = {
                    "type": doc_type, "no": inv_no, "client": inv_client, "desc": inv_desc,
                    "net": net_amount, "mwst_rate": mwst_rate, "mwst_val": mwst_amount, "gross": gross_amount,
                    "tarih": tarih_str, "vade": vade_str, "vade_gun": vade_gun,
                    "yetkili": str(client_row["Yetkili"]), "telefon": str(client_row["Telefon"]), "adres": str(client_row["Adres"]),
                    "comp_name": "Zer Transport", "comp_addr": str(comp.get("Adres", "Attnang-Puchheim, Austria")),
                    "comp_tax": str(comp.get("Vergi No", "ATU12345678")), "comp_iban": str(comp.get("IBAN", "")),
                    "comp_mail": str(comp.get("E-posta", "")), "comp_tel": str(comp.get("Telefon", ""))
                }
                st.success("✅ Dokument erfolgreich erstellt!")

    if "last_doc" in st.session_state:
        doc = st.session_state["last_doc"]
        st.markdown("---")
        
        # Tamamen Almanca, Netto-Brutto dökümlü, en altta banka bilgileri olan şık PDF tasarımı
        modern_invoice_html = f"""
        <div style="max-width: 800px; margin: auto; padding: 40px; border: 1px solid #dcdcdc; box-shadow: 0 4px 20px rgba(0,0,0,0.06); font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #ffffff; color: #2c3e50; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #1abc9c; padding-bottom: 25px; margin-bottom: 25px;">
                <div style="line-height: 1.5;">
                    <h2 style="color: #2c3e50; margin: 0 0 5px 0; font-size: 26px;">🚚 {doc['comp_name']}</h2>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;">Anschrift: {doc['comp_addr']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;">Tel: {doc['comp_tel']} | E-Mail: {doc['comp_mail']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;">UID-Nr / Steuernummer: {doc['comp_tax']}</p>
                </div>
                <div style="text-align: right; line-height: 1.5;">
                    <h1 style="color: #1abc9c; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px;">{doc['type']}</h1>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;"><b>Dokumenten-Nr:</b> {doc['no']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;"><b>Datum:</b> {doc['tarih']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;"><b>Fälligkeitsdatum:</b> {doc['vade']}</p>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
                <div style="width: 48%; background: #fdfdfd; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; border-left: 4px solid #1abc9c;">
                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #888; text-transform: uppercase;"><b>Rechnungsempfänger (Kunde):</b></p>
                    <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: bold; color: #111;">{doc['client']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;">Ansprechpartner: {doc['yetkili']}</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;">Adresse: {doc['adres']}</p>
                </div>
                <div style="width: 48%; background: #fdfdfd; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; border-left: 4px solid #34495e;">
                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #888; text-transform: uppercase;"><b>Zahlungsbedingungen:</b></p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;"><b>Zahlungsziel:</b> Innerhalb von {doc['vade_gun']} Tagen</p>
                    <p style="margin: 2px 0; font-size: 13px; color: #555;"><b>Status:</b> Offen</p>
                </div>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #2c3e50; color: white;">
                        <th style="text-align: left; padding: 12px; font-size: 13px;">Leistungsbeschreibung</th>
                        <th style="text-align: right; padding: 12px; font-size: 13px;">Netto Betrag</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 14px 12px; border-bottom: 1px solid #eaeaea; font-size: 13px; color: #333;">{doc['desc']}</td>
                        <td style="padding: 14px 12px; border-bottom: 1px solid #eaeaea; text-align: right; font-size: 13px; color: #333;"><b>{doc['net']:.2f} €</b></td>
                    </tr>
                </tbody>
            </table>

            <div style="display: flex; justify-content: flex-end; margin-bottom: 40px;">
                <div style="width: 280px; font-size: 13px; line-height: 1.6;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #eaeaea; padding: 6px 0;">
                        <span>Nettobetrag:</span>
                        <span><b>{doc['net']:.2f} €</b></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #eaeaea; padding: 6px 0;">
                        <span>MwSt. ({doc['mwst_rate']}%):</span>
                        <span><b>{doc['mwst_val']:.2f} €</b></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #2c3e50; padding: 8px 0; font-size: 16px; color: #1abc9c;">
                        <span><b>Gesamtbetrag:</b></span>
                        <span><b>{doc['gross']:.2f} €</b></span>
                    </div>
                </div>
            </div>

            <!-- Banka Bilgileri En Altta -->
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef; font-size: 12px; color: #444;">
                <p style="margin: 0 0 5px 0; font-weight: bold; text-transform: uppercase; color: #2c3e50;">Bankverbindung / Banka Bilgileri:</p>
                <p style="margin: 2px 0;"><b>IBAN:</b> {doc['comp_iban']}</p>
                <p style="margin: 2px 0;"><b>Unternehmen:</b> {doc['comp_name']} | <b>Steuer-Nr:</b> {doc['comp_tax']}</p>
            </div>

            <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #eaeaea; font-size: 11px; color: #777; text-align: center;">
                <p style="margin: 2px 0;">Bitte überweisen Sie den Gesamtbetrag unter Angabe der Dokumenten-Nr auf das genannte Konto.</p>
                <p style="margin: 2px 0;">{doc['comp_name']} — Professional Transport & Express Logistics</p>
            </div>
        </div>
        """
        
        st.markdown(modern_invoice_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("💡 **PDF olarak kaydetmek için:** Klavyenizden **Ctrl + P** tuşlarına basın ve açılan pencerede hedef olarak **'PDF olarak kaydet' (Save as PDF)** seçeneğini seçin.")
        
        wa_text = f"Sehr geehrte(r) {doc['yetkili']}, Ihr Dokument {doc['no']} über {doc['gross']:.2f} EUR ist bereit. Vielen Dank - {doc['comp_name']}."
        st.markdown(f"📱 **Per WhatsApp senden:** [Hier klicken](https://wa.me/{doc['telefon'].replace(' ', '')}?text={urllib.parse.quote(wa_text)})", unsafe_allow_html=True)

elif menu == "👥 Müşteri Yönetimi":
    st.subheader("👥 Kundenverwaltung / Müşteri Yönetimi")
    with st.form("add_client_form"):
        c_name = st.text_input("Kundenname / Firma Adı")
        c_auth = st.text_input("Ansprechpartner / Yetkili")
        c_mail = st.text_input("E-Mail-Adresse")
        c_phone = st.text_input("Telefonnummer (z.B. +43676...)")
        c_addr = st.text_area("Adresse / Adres")
        save_new = st.form_submit_button("Kunden Speichern")
        
        if save_new and c_name:
            new_c = pd.DataFrame([[c_name, c_auth, c_mail, c_phone, c_addr]], columns=["Müşteri Adı", "Yetkili", "E-posta", "Telefon", "Adres"])
            clients_df = pd.concat([clients_df, new_c], ignore_index=True)
            clients_df.to_csv(DB_CLIENTS, index=False)
            st.success(f"Kunde {c_name} gespeichert!")
            st.rerun()
            
    if not clients_df.empty:
        st.markdown("---")
        st.dataframe(clients_df, use_container_width=True)

elif menu == "⚙️ Firma Ayarları":
    st.subheader("⚙️ Firmeneinstellungen / Şirket Bilgileri")
    current = settings_df.iloc[0] if not settings_df.empty else {"Firma Adi": "Zer Transport", "Adres": "Attnang-Puchheim", "Vergi No": "ATU12345678", "IBAN": "", "E-posta": "", "Telefon": ""}
    
    with st.form("settings_form"):
        f_adi = st.text_input("Unternehmensname (Şirket Adı)", value="Zer Transport")
        f_adres = st.text_area("Anschrift (Adres)", value=current.get("Adres", "Attnang-Puchheim, Austria"))
        f_vergi = st.text_input("UID-Nr / Steuernummer", value=current.get("Vergi No", ""))
        f_iban = st.text_input("Bank IBAN", value=current.get("IBAN", ""))
        f_mail = st.text_input("E-Mail", value=current.get("E-posta", ""))
        f_tel = st.text_input("Telefon", value=current.get("Telefon", ""))
        logo_file = st.file_uploader("Unternehmenslogo (PNG / JPG)", type=["png", "jpg", "jpeg"])
        save_set = st.form_submit_button("Einstellungen Speichern")
        
        if save_set:
            new_s = pd.DataFrame([[f_adi, f_adres, f_vergi, f_iban, f_mail, f_tel]], columns=["Firma Adi", "Adres", "Vergi No", "IBAN", "E-posta", "Telefon"])
            new_s.to_csv(DB_SETTINGS, index=False)
            if logo_file:
                with open(LOGO_PATH, "wb") as f:
                    f.write(logo_file.getbuffer())
            st.success("Einstellungen gespeichert!")

elif menu == "📷 CMR Tara & Gönder":
    st.subheader("📷 CMR Dokument hochladen")
    cmr_file = st.file_uploader("CMR Foto", type=["jpg", "png", "jpeg"])
    if cmr_file:
        st.image(cmr_file, caption="Hochgeladenes CMR", use_column_width=True)
        st.success("CMR erfolgreich verarbeitet!")
