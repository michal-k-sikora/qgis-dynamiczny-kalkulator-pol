# Dynamiczny Kalkulator Pól

**Dynamiczny Kalkulator Pól** umożliwia **jednoczesną aktualizację wielu atrybutów** w wybranej warstwie wektorowej przy użyciu wyrażeń QGIS — w jednym, przejrzystym panelu.  
Została zaprojektowana, aby znacznie przyspieszyć pracę z danymi atrybutowymi w projektach GIS.

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

