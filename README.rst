# 🌬️ Haize Parkeen Aurreikuspena

Haize-parkeen datu historikoen eta aurreikuspenen bistaratzaile automatikoa, orduro eguneratzen dena.

## 📊 Proiektuari buruz

Aplikazio honek Google Sheets-etik datuak irakurtzen ditu eta haize-parkeen aurreikuspen interaktibo bat sortzen du, GitHub Pages bidez argitaratuta.

### Parke eolikoak:
- ⚡ **Badia**
- ⚡ **Elgea**
- ⚡ **Corrella**

## 🚀 Ezaugarriak

- ✅ **Eguneraketa automatikoa**: Orduro exekutatzen da GitHub Actions-ekin
- ✅ **Datu historikoak**: Duela urtebeteko egun eta ordu beraren alderaketa
- ✅ **5 eguneko aurreikuspena**: Haize-abiaduraren estimazioa
- ✅ **Diseinu modernoa eta erantzunkorra**: Mugikorretan eta mahaigainean funtzionatzen du
- ✅ **Denbora errealeko eguneraketak**: Azken eguneraketaren data-ordua erakusten du

## 📁 Egitura

```
├── .github/
│   └── workflows/
│       └── update-forecast.yml    # GitHub Actions workflow-a
├── generate_forecast.py           # Python script-a datuak prozesatzeko
├── index.html                     # Sortutako HTML orria (automatikoa)
└── README.md                      # Dokumentazio hau
```

## 🛠️ Instalazioa

### 1. Biltegi hau klonatu

```bash
git clone https://github.com/zure-erabiltzailea/zure-erabiltzailea.github.io.git
cd zure-erabiltzailea.github.io
```

### 2. Dependentziak instalatu (lokalki probatzeko)

```bash
pip install pandas
```

### 3. Script-a exekutatu

```bash
python generate_forecast.py
```

Honek `index.html` fitxategia sortuko du.

## ⚙️ Konfigurazioa

### Google Sheets IDa aldatu

`generate_forecast.py` fitxategian, aldatu Google Sheet-aren IDa:

```python
GSHEET_ID = "ZURE_GSHEET_ID_HEMEN"
```

### Orri-orriak (tabs) konfiguratu

Gehitu edo kendu parke eolikoak:

```python
sheet_tabs = {
    "Badia": "129655069",      # gid-a URLtik
    "Elgea": "408081399",
    "Corrella": "107505326"
}
```

## 🔄 Eguneraketa automatikoa

GitHub Actions workflow-ak orduro exekutatzen du script-a automatikoki eta `index.html` eguneratzen du.

### Eskuz exekutatzeko:

1. Joan **Actions** atalera zure biltegian
2. Hautatu "Actualizar Pronóstico de Viento"
3. Sakatu **Run workflow**

### Cron ordutegia:

```yaml
cron: '0 * * * *'  # Ordu bakoitzeko minutu 0ean
```

## 📈 Nola funtzionatzen du

1. **Datuak eskuratu**: Google Sheets publikoetatik datuak irakurtzen ditu
2. **Datu historikoak**: Duela urtebeteko egun eta ordu bereko datuak filtratzen ditu
3. **Aurreikuspena**: Azken 30 eguneko batez bestekoa kalkulatzen du hurrengo 5 egunetarako
4. **HTML sortu**: Diseinu modernoa duen orri interaktiboa sortzen du
5. **Argitaratu**: GitHub Pages-en automatikoki argitaratzen da

## 🌐 Webgunea ikusi

Zure webgunea helbide honetan dago eskuragarri:

```
https://zure-erabiltzailea.github.io
```

## 📝 Datuak

Datuak Google Sheets batetik eskuratzen dira formatu honekin:

- **timestamp**: Data eta ordua
- **fechas**: Daten zutabea (aurreikuspenak kalkulatzeko)
- **wind_mps**: Haize-abiadura segundoko metrotan
- Beste zutabe batzuk (aukerakoak)

## 🔒 Baimenak

GitHub Actions-ek aldaketak egin ahal izateko, ziurtatu baimenak aktibatuta daudela:

1. **Settings** → **Actions** → **General**
2. Hautatu: **Read and write permissions**
3. Markatu: **Allow GitHub Actions to create and approve pull requests**

## 🐛 Arazoak konpontzea

### Workflow-ak ez du funtzionatzen

- Egiaztatu baimenak aktibatuta daudela
- Begiratu **Actions** ataleko erroreen mezuak
- Ziurtatu Google Sheets-a publikoa dela

### Daturik ez da agertzen

- Egiaztatu zutabeen izenak bat datozela script-an
- Begiratu Google Sheets-aren IDa zuzena den
- Ziurtatu `gid` zenbakiak zuzenak direla

### GitHub Pages-ek ez du funtzionatzen

- **Settings** → **Pages** → Ziurtatu **main** adarra hautatuta dagoela
- Itxaron minutu batzuk propagatzeko

## 📄 Lizentzia

Proiektu hau kode irekikoa da. Libreki erabil dezakezu eta alda dezakezu.

## 🤝 Ekarpenak

Ekarpenak ongi etorriak dira! Zabaldu issue bat edo bidali pull request bat.

## 📧 Kontaktua

Galderarik baduzu, sortu issue bat biltegi honetan.

---

**Azken eguneratzea**: Automatikoki eguneratzen da orduro ⏰

**Egilea**: [Zure izena hemen]

**URL**: https://zure-erabiltzailea.github.io
