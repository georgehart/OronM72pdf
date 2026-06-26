import os
import sys  # Toegevoegd voor de terminal argumenten
import base64
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from weasyprint import HTML

# ==========================================
# 1. CONFIGURATIE EN DATA LADEN via Argumenten
# ==========================================
CONFIG_FILE = "setup/config.json"

# Controleer of de gebruiker een CSV-bestand heeft meegegeven
if len(sys.argv) < 2:
    print("\n[Fout] Je bent vergeten het CSV-bestand mee te geven!")
    print("Gebruik: python scriptnaam.py <pad_naar_csv_bestand>")
    print("Voorbeeld: python scriptnaam.py ./data/BP_110326_240626.csv\n")
    sys.exit(1)

# Haal het pad op uit het eerste argument
csv_pad = sys.argv[1]

if not os.path.exists(csv_pad):
    raise FileNotFoundError(f"Het bestand {csv_pad} werd niet gevonden. Controleer het opgegeven pad.")

# Laad JSON config voor medicatie en opmerkingen
try:
    import json
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    medicatie_lijst = config_data.get("medicatie", ["Geen medicatie opgegeven."])
    opmerkingen_lijst = config_data.get("opmerkingen", ["Geen extra opmerkingen."])
except Exception as e:
    print(f"Kon config niet laden uit JSON: {e}")
    medicatie_lijst = ["Fout bij laden van medicatieconfiguratie."]
    opmerkingen_lijst = ["Fout bij laden van opmerkingen."]

df = pd.read_csv(csv_pad, usecols=range(5))

# ==========================================
# 2. DATUM EN TIJD PARSEN (NEDERLANDS -> ENGELS)
# ==========================================
tekst_datums = df['Datum'] + ' ' + df['Tijd']
nederlands_naar_engels = {
    'jan.': 'Jan', 'feb.': 'Feb', 'mrt.': 'Mar', 'apr.': 'Apr', 
    'mei': 'May', 'jun.': 'Jun', 'jul.': 'Jul', 'aug.': 'Aug', 
    'sep.': 'Sep', 'okt.': 'Oct', 'nov.': 'Nov', 'dec.': 'Dec'
}
for nl, en in nederlands_naar_engels.items():
    tekst_datums = tekst_datums.str.replace(nl, en, case=False, regex=False)

df['Timestamp'] = pd.to_datetime(tekst_datums, format='%d %b %Y %H:%M', errors='coerce')
df = df.sort_values('Timestamp')
df['Pure_Datum'] = df['Timestamp'].dt.date

# ==========================================
# 3. GEMIDDELDEN & ESC CLASSIFICATIE BEREKENEN
# ==========================================
dagelijkse_gemiddelden = df.groupby('Pure_Datum')[['Systolisch (mmHg)', 'Diastolisch (mmHg)', 'Hartslag (spm)']].mean().round(1)
gemiddelden_timestamps = pd.to_datetime(dagelijkse_gemiddelden.index) + pd.Timedelta(hours=12)

totaal_gem_systolisch = df['Systolisch (mmHg)'].mean()
totaal_gem_diastolisch = df['Diastolisch (mmHg)'].mean()
totaal_gem_hartslag = df['Hartslag (spm)'].mean()

def classificeer_esc(row):
    sys = row['Systolisch (mmHg)']
    dia = row['Diastolisch (mmHg)']
    if pd.isna(sys) or pd.isna(dia):
        return 'Onbekend'
    if sys >= 140 or dia >= 90:
        return 'Hypertensie (Te hoog)'
    elif (130 <= sys < 140) or (85 <= dia < 90):
        return 'Hoog-Normaal'
    else:
        return 'Normaal / Optimaal'

df['ESC_Zone'] = df.apply(classificeer_esc, axis=1)
esc_counts = df['ESC_Zone'].value_counts()

for zone in ['Normaal / Optimaal', 'Hoog-Normaal', 'Hypertensie (Te hoog)']:
    if zone not in esc_counts:
        esc_counts[zone] = 0

# ==========================================
# 4. VISUALISATIES GENEREREN
# ==========================================
temp_chart_path = 'temp_chart.png'
temp_boxplot_path = 'temp_boxplot.png'
temp_pie_path = 'temp_pie.png'

# --- GRAFIEK 1: Trendgrafiek ---
plt.figure(figsize=(11, 4.8), dpi=300)
plt.plot(df['Timestamp'], df['Systolisch (mmHg)'], label='Systolisch (Meting)', color='#e74c3c', alpha=0.15, marker='o', markersize=2)
plt.plot(df['Timestamp'], df['Diastolisch (mmHg)'], label='Diastolisch (Meting)', color='#3498db', alpha=0.15, marker='o', markersize=2)
plt.plot(gemiddelden_timestamps, dagelijkse_gemiddelden['Systolisch (mmHg)'], label='Systolisch (Daggemiddelde)', color='#c0392b', linestyle='--', linewidth=1.8, marker='X')
plt.plot(gemiddelden_timestamps, dagelijkse_gemiddelden['Diastolisch (mmHg)'], label='Diastolisch (Daggemiddelde)', color='#2980b9', linestyle='--', linewidth=1.8, marker='X')
plt.axhline(y=totaal_gem_systolisch, color='#c0392b', linestyle='-', linewidth=1.2, alpha=0.5, label=f'Gem. Systolisch ({totaal_gem_systolisch:.1f})')
plt.axhline(y=totaal_gem_diastolisch, color='#2980b9', linestyle='-', linewidth=1.2, alpha=0.5, label=f'Gem. Diastolisch ({totaal_gem_diastolisch:.1f})')
plt.title('Bloeddruk & Hartslag Verloop', fontsize=11, fontweight='bold', color='#2c3e50')
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left', fontsize=8, ncol=3)
plt.tight_layout()
plt.savefig(temp_chart_path, dpi=300)
plt.close()

# --- GRAFIEK 2: Boxplot Verdeling ---
plt.figure(figsize=(5.2, 4.2), dpi=300)
box = plt.boxplot([df['Systolisch (mmHg)'].dropna(), df['Diastolisch (mmHg)'].dropna()], labels=['Systolisch', 'Diastolisch'], patch_artist=True)
for patch, kleur in zip(box['boxes'], ['#e74c3c', '#3498db']):
    patch.set_facecolor(kleur); patch.set_alpha(0.4); patch.set_edgecolor(kleur)
plt.title('Statistische Spreiding', fontsize=11, fontweight='bold', color='#2c3e50')
plt.grid(True, linestyle=':', alpha=0.4, axis='y')
plt.tight_layout()
plt.savefig(temp_boxplot_path, dpi=300)
plt.close()

# --- GRAFIEK 3: ESC Zones Taartdiagram ---
plt.figure(figsize=(5.2, 4.2), dpi=300)
esc_kleuren = {'Normaal / Optimaal': '#2ecc71', 'Hoog-Normaal': '#f1c40f', 'Hypertensie (Te hoog)': '#e74c3c'}
plot_data = [esc_counts['Normaal / Optimaal'], esc_counts['Hoog-Normaal'], esc_counts['Hypertensie (Te hoog)']]
plot_labels = ['Normaal', 'Hoog-Normaal', 'Te Hoog']
plt.pie(plot_data, labels=plot_labels, colors=[esc_kleuren[k] for k in ['Normaal / Optimaal', 'Hoog-Normaal', 'Hypertensie (Te hoog)']],
        autopct=lambda p: '{:.1f}%'.format(p) if p > 0 else '', startangle=90, 
        textprops={'fontsize': 9, 'color': '#2c3e50', 'fontweight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'alpha': 0.75})
plt.title('Metingen volgens ESC-richtlijnen', fontsize=11, fontweight='bold', color='#2c3e50')
plt.tight_layout()
plt.savefig(temp_pie_path, dpi=300)
plt.close()

# ==========================================
# 5. HTML EN CSS STRUCTUUR OPBOUWEN
# ==========================================
def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

chart_b64 = get_base64(temp_chart_path)
boxplot_b64 = get_base64(temp_boxplot_path)
pie_b64 = get_base64(temp_pie_path)
huidige_datum = datetime.now().strftime('%d-%m-%Y')

medicatie_html = "".join([f"<li>{med}</li>" for med in medicatie_lijst])
opmerkingen_html = "".join([f"<li>{opm}</li>" for opm in opmerkingen_lijst])

html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    :root {{ --print-date: "{huidige_datum}"; }}
    @page {{
        size: A4; margin: 12mm 15mm;
        @bottom-right {{ content: "Pagina " counter(page) " van " counter(pages); font-size: 8pt; font-family: Arial, sans-serif; color: #7f8c8d; }}
        @bottom-left {{ content: "Geprint op: " var(--print-date) " | Omron Gezondheidsrapport — Vertrouwelijk"; font-size: 8pt; font-family: Arial, sans-serif; color: #7f8c8d; }}
    }}
    body {{ font-family: Arial, sans-serif; color: #2c3e50; margin: 0; line-height: 1.4; font-size: 9.5pt; }}
    .header {{ border-bottom: 2px solid #34495e; padding-bottom: 5px; margin-bottom: 12px; }}
    .title {{ font-size: 18pt; font-weight: bold; margin: 0; color: #2c3e50; }}
    .name {{ font-size: 12pt; font-weight: bold; margin: 5px 0 0 0; color: #2b6299; }}
    .subtitle {{ font-size: 9.5pt; color: #7f8c8d; margin: 3px 0 0 0; }}
    
    .meta-table {{ width: 100%; margin-bottom: 12px; font-size: 8.5pt; border-collapse: collapse; }}
    .meta-table td {{ padding: 2px 0; }}
    
    .section-title {{ font-size: 11pt; font-weight: bold; border-left: 4px solid #34495e; padding-left: 6px; margin: 12px 0 8px 0; page-break-after: avoid; }}
    
    .context-container {{ width: 100%; margin-bottom: 10px; }}
    .context-box {{ width: 48%; display: inline-block; vertical-align: top; border-radius: 6px; padding: 8px 12px; box-sizing: border-box; }}
    .med-box {{ background: #fffbeb; border: 1px solid #fef3c7; }}
    .med-box h4 {{ margin: 0 0 4px 0; color: #b45309; font-size: 9pt; text-transform: uppercase; }}
    .med-box ul {{ margin: 0; padding-left: 15px; color: #451a03; font-size: 9pt; }}
    
    .obs-box {{ background: #f0fdf4; border: 1px solid #dcfce7; float: right; }}
    .obs-box h4 {{ margin: 0 0 4px 0; color: #166534; font-size: 9pt; text-transform: uppercase; }}
    .obs-box ul {{ margin: 0; padding-left: 15px; color: #14532d; font-size: 9pt; }}
    
    .kpis {{ width: 100%; border-spacing: 10px 0; margin: 0 -10px 12px -10px; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; text-align: center; }}
    .kpi-title {{ font-size: 7.5pt; text-transform: uppercase; color: #64748b; font-weight: bold; }}
    .kpi-value {{ font-size: 16pt; font-weight: bold; margin: 2px 0; }}
    .sys {{ color: #c0392b; }} .dia {{ color: #2980b9; }} .pulse {{ color: #27ae60; }}
    
    .flex-container {{ width: 100%; margin-top: 5px; }}
    .flex-col {{ width: 49%; display: inline-block; vertical-align: top; text-align: center; }}
    
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 8.5pt; }}
    .data-table th {{ background: #f1f5f9; color: #334155; font-weight: bold; padding: 5px; border-bottom: 1.5px solid #cbd5e1; text-align: left; }}
    .data-table td {{ padding: 4px; border-bottom: 1px solid #e2e8f0; }}
    .data-table tr:nth-child(even) {{ background: #f8fafc; }}
</style>
</head>
<body>

    <div class="header">
        <h1 class="title">Bloeddrukwaarden</h1>
        <h4 class="name">Georges Hart</h4>
    </div>

    <div class="context-container">
        <div class="context-box med-box">
            <h4>Huidige Medicatie:</h4>
            <ul>{medicatie_html}</ul>
        </div>
        <div class="context-box obs-box">
            <h4>Klinische Opmerkingen:</h4>
            <ul>{opmerkingen_html}</ul>
        </div>
    </div>

    <table class="meta-table">
        <tr>
            <td style="width: 15%;"><strong>Periode:</strong></td>
            <td style="width: 35%;">{df['Pure_Datum'].min().strftime('%d-%m-%Y')} t/m {df['Pure_Datum'].max().strftime('%d-%m-%Y')}</td>
            <td style="width: 20%;"><strong>Meetapparaat:</strong></td>
            <td style="width: 30%;">Omron M7 Inteli IT AFIB</td>
        </tr>
        <tr>
            <td><strong>Gegenereerd:</strong></td>
            <td>{datetime.now().strftime('%d-%m-%Y %H:%M')}</td>
            <td><strong>Aantal records:</strong></td>
            <td>{len(df)} metingen</td>
        </tr>
    </table>

    <div class="section-title">Algemene Gemiddelden</div>
    <table class="kpis">
        <tr>
            <td class="kpi-card"><div class="kpi-title">Gem. Systolisch</div><div class="kpi-value sys">{totaal_gem_systolisch:.1f}</div><div style="font-size: 7.5pt; color: #94a3b8;">mmHg</div></td>
            <td class="kpi-card"><div class="kpi-title">Gem. Diastolisch</div><div class="kpi-value dia">{totaal_gem_diastolisch:.1f}</div><div style="font-size: 7.5pt; color: #94a3b8;">mmHg</div></td>
            <td class="kpi-card"><div class="kpi-title">Gem. Hartslag</div><div class="kpi-value pulse">{totaal_gem_hartslag:.1f}</div><div style="font-size: 7.5pt; color: #94a3b8;">spm</div></td>
        </tr>
    </table>

    <div class="section-title">Trendverloop complete periode</div>
    <div style="text-align: center;"><img src="data:image/png;base64,{chart_b64}" style="width: 100%; height: auto;"></div>

    <div class="flex-container">
        <div class="flex-col"><img src="data:image/png;base64,{boxplot_b64}" style="width: 100%;"></div>
        <div class="flex-col" style="float: right;"><img src="data:image/png;base64,{pie_b64}" style="width: 100%;"></div>
    </div>

    <div style="page-break-before: always;"></div>

    <div class="section-title">Recente Dagelijkse Gemiddelden (Laatste 15 dagen)</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Datum</th>
                <th>Systolisch (mmHg)</th>
                <th>Diastolisch (mmHg)</th>
                <th>Hartslag (spm)</th>
                <th>Status (ESC)</th>
            </tr>
        </thead>
        <tbody>
"""

for date_idx, row in dagelijkse_gemiddelden.tail(15).iloc[::-1].iterrows():
    dummy_row = {'Systolisch (mmHg)': row['Systolisch (mmHg)'], 'Diastolisch (mmHg)': row['Diastolisch (mmHg)']}
    status = classificeer_esc(dummy_row)
    status_kleur = esc_kleuren.get(status, '#2c3e50')
    
    html_content += f"""
            <tr>
                <td>{date_idx.strftime('%d-%m-%Y')}</td>
                <td style="font-weight: bold; color: #c0392b;">{row['Systolisch (mmHg)']:.1f}</td>
                <td style="font-weight: bold; color: #2980b9;">{row['Diastolisch (mmHg)']:.1f}</td>
                <td style="color: #27ae60;">{row['Hartslag (spm)']:.1f}</td>
                <td style="color: {status_kleur}; font-weight: bold;">{status}</td>
            </tr>
    """

html_content += """
        </tbody>
    </table>

</body>
</html>
"""

# ==========================================
# 6. PDF OPSLAAN EN SCHOONMAKEN
# ==========================================
output_pdf = "GH_Bloeddruk_Verslag.pdf"
HTML(string=html_content).write_pdf(output_pdf)

for p in [temp_chart_path, temp_boxplot_path, temp_pie_path]:
    if os.path.exists(p):
        os.remove(p)

print(f"Succes! Het uitgebreide rapport is opgeslagen als '{output_pdf}'.")
