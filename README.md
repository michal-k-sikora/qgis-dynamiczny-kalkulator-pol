## [PL] Dynamiczny Kalkulator Pól

**Dynamiczny Kalkulator Pól** umożliwia **jednoczesną aktualizację wielu atrybutów** w wybranej warstwie wektorowej przy użyciu wyrażeń QGIS — w jednym, przejrzystym panelu.  
Została zaprojektowana, aby znacznie przyspieszyć pracę z danymi atrybutowymi w projektach GIS.
---

<img width="746" height="509" alt="screenshot" src="https://github.com/user-attachments/assets/ff577113-f28e-4464-866a-062ad4c9bf57" />

---

## Funkcje

Wtyczka umożliwia m.in.:  
- wybór dowolnej warstwy wektorowej dostępnej w projekcie,  
- wybranie wielu pól do edycji jednocześnie,  
- wpisanie różnych wyrażeń QGIS dla każdego pola w jednym panelu,  
- otwieranie **Kreatora wyrażeń** bezpośrednio z poziomu wtyczki,  
- **podgląd zmian** bez zapisywania ich do warstwy,  
- finalny zapis zmian lub ich odrzucenie,  
- opcję działania **tylko na zaznaczonych obiektach**,  
- zapamiętywanie ostatniego zestawu ustawień i wyrażeń,  
- działanie w formie **dokowalnego panelu bocznego**,  

---

## Interfejs

Panel składa się z dwóch głównych części:

### **Lewa kolumna**
- wybór warstwy wektorowej,  
- lista wszystkich edytowalnych pól,  
- opcja „Tylko zaznaczone obiekty”,  
- przyciski dodawania pól do edycji i czyszczenia panelu,  
- krótki panel pomocy.

### **Prawa kolumna**
- dynamicznie tworzone wiersze edycyjne dla wybranych pól,  
- dla każdego pola:
  - jego nazwa i typ,  
  - pole na wyrażenie QGIS,  
  - przycisk otwierający Kreator wyrażeń,  
  - przycisk usunięcia pola z listy edycyjnej,  
- przyciski operacyjne:
  - **Zastosuj (bez zapisu zmian)**  
  - **Zapisz zmiany na warstwie**  
  - **Odrzuć zmiany**  
  - **Zapisz konfigurację**  
  - **Wczytaj konfigurację**

---

## Instalacja

### **1. Instalacja z ZIP**
1. Pobierz najnowszą wersję wtyczki (plik `.zip`) z zakładki *Releases* repozytorium.
2. W QGIS przejdź do:  
   **Wtyczki → Zainstaluj z pliku ZIP**
3. Wskaż pobrany plik `.zip`.
4. Wtyczka pojawi się w menu **Narzędzia OnGeo** i na pasku o tej samej nazwie.

### **2. Instalacja ręczna**
Skopiuj folder `Dynamiczny_kalkulator_pol` do katalogu:
- Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`
- Linux/macOS: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`

---

## Wymagania

- **QGIS 3.10 lub nowszy**  
- Python (zawarty w instalacji QGIS)  
- Obsługa Qt5/Qt6 (wtyczka wspiera Qt6)

---

## Jak używać wtyczki

1. Uruchom QGIS i aktywuj wtyczkę z listy zainstalowanych wtyczek.  
2. Na pasku „Narzędzia OnGeo” kliknij ikonę **Dynamiczny Kalkulator Pól**.  
3. W panelu bocznym:
   - wybierz warstwę,  
   - wskaż pola, które chcesz modyfikować,  
   - wpisz wyrażenia QGIS,  
   - kliknij **Zastosuj**, aby zobaczyć zmiany bez zapisu,  
   - jeśli wszystko jest poprawne — kliknij **Zapisz zmiany**.

W trakcie pracy możesz otworzyć Kreator wyrażeń QGIS, aby szybko tworzyć i testować formuły.

---

## Przykłady zastosowań

- masowa aktualizacja dat, flag logicznych lub wartości liczbowych,  
- obliczenia geometryczne,  
- kopiowanie wartości między polami,  
- normalizacja danych atrybutowych,  
- wyliczanie wskaźników na podstawie kilku pól jednocześnie.

---

## Zapisywanie konfiguracji

Wtyczka umożliwia zapamiętanie zestawu ostatnio używanych ustawień, w tym:
- nazwy warstwy,  
- stanu checkboxa „Tylko zaznaczone obiekty”,  
- wyrażeń przypisanych do pól.

Konfiguracja przechowywana jest w QGIS QSettings.

---

## Autor

**Michał Sikora**  
Szkolenia i usługi GIS: **https://szkolenia.ongeo.pl/**  
Kontakt: **michal.sikora@ongeo.pl**

---

## ENGLISH

## [EN] Dynamic Field Calculator

**Dynamic Field Calculator** allows **simultaneous updating of multiple attributes** in a selected vector layer using QGIS expressions — all within a single, clear panel.
It was designed to significantly speed up attribute data editing in GIS projects.

---

## FEATURES
- Select any vector layer available in the project
- Edit multiple fields at the same time
- Use different QGIS expressions for each field in a single panel
- Open the Expression Builder directly from the plugin
- Preview changes without saving them to the layer
- Save or discard changes
- Apply changes only to selected features
- Remember the last used settings and expressions
- Work as a dockable side panel

---

## INTERFACE

### **Left column:**
- Vector layer selection
- List of all editable fields
- “Selected features only” option
- Buttons for adding fields and clearing the panel
- Short help section

### **Right column:**
- Dynamically generated edit rows for selected fields
- Field name and type
- QGIS expression input
- Expression Builder button
- Remove field button
- Action buttons:
  **Apply (without saving changes)**
  **Save changes to layer**
  **Discard changes**
  **Save configuration**
  **Load configuration**

---

## INSTALLATION

### Install from ZIP:
1. Download the latest plugin version (.zip) from the Releases tab.
2. In QGIS go to Plugins → Install from ZIP.
3. Select the downloaded file.
4. The plugin will appear in the OnGeo Tools menu and toolbar.

### Manual installation:
Copy the Dynamiczny_kalkulator_pol folder to:
Windows: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins
Linux/macOS: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins

---

## REQUIREMENTS
- QGIS 3.10 or newer
- Python (included with QGIS)
- Qt5 / Qt6 support

---

## USAGE
1. Enable the plugin in QGIS.
2. Open Dynamic Field Calculator from the OnGeo Tools toolbar.
3. Select a layer, choose fields, enter expressions.
4. Click Apply to preview changes.
5. Click Save changes to commit them.

---

## EXAMPLES
- Bulk attribute updates
- Geometry-based calculations
- Copying values between fields
- Attribute normalization
- Calculating indicators from multiple fields

---

## CONFIGURATION
The plugin stores:
- Selected layer
- Selected-features-only state
- Field expressions
using QGIS QSettings.

---

## AUTHOR
**Michał Sikora**
GIS training courses and services: **https://szkolenia.ongeo.pl/**
Contact: **michal.sikora@ongeo.pl**
