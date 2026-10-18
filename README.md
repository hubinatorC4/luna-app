# Luna – asystentka AI i trenerka głosu

Luna to aplikacja webowa (PWA). Rozmawia po polsku ciepłym, niskim głosem z hiszpańskim akcentem i pomaga ćwiczyć wypowiadanie się. Luna zawsze ujawnia, że jest sztuczną inteligencją.

**Na żywo:** https://luna-voice-coach.onrender.com · strona promocyjna: `/promo.html`

## Funkcje (v1.1)
- czat tekstowy i głosowy, słowo wybudzające „Luna”, synteza mowy (edge-tts, pl-PL-ZofiaNeural)
- panel „Barwa głosu”: wysokość, tempo, ciepło, głośność i presety
- „Stwórz własną asystentkę”: imię, słowo wybudzające, ton, długość odpowiedzi, kolor pierścienia, stroje, pozy i sylwetki (gating według planów)
- plany Podstawowa → Premium → Pro / Ultra (wersja demonstracyjna, bez płatności)
- tryb hologram, okrągłe awatary Luny i użytkownika
- muzyka w tle: 10 utworów smooth jazz (Kevin MacLeod, CC BY 4.0, zob. `static/music/LICENSES.md`)
- panel producenta: osobowość, teksty, baza wiedzy, reguły, głos, wygląd, katalog postaci i playlista

## Uruchomienie lokalne
```bash
pip install -r requirements.txt
LUNA_ADMIN_CODE=twojkod python3 server.py   # http://localhost:8765
```
Potrzebny jest ffmpeg. Jeśli nie ma go w systemie, aplikacja użyje binarki z `imageio-ffmpeg`.

## Zmienne środowiskowe
| Zmienna | Opis |
|---|---|
| `LUNA_ADMIN_CODE_HASH` | (zalecane) hash kodu producenta w formacie `pbkdf2_sha256$200000$sól$skrót` |
| `LUNA_ADMIN_CODE` | alternatywnie: kod w postaci jawnej (gdy ustawiony jest hash, ta zmienna jest ignorowana) |
| `LUNA_API_KEY`, `LUNA_BASE_URL`, `LUNA_MODEL` | opcjonalny model językowy zgodny z OpenAI. Bez niego działa wbudowana baza wiedzy |
| `PORT` | port serwera (Render ustawia go sam) |

Hash wygenerujesz tak:
```bash
python3 -c "import hashlib,os,getpass;s=os.urandom(16).hex();c=getpass.getpass('Kod: ');print('pbkdf2_sha256\$200000\$'+s+'\$'+hashlib.pbkdf2_hmac('sha256',c.encode(),s.encode(),200000).hex())"
```
Panel producenta otworzysz, wpisując kod w zwykłym czacie. Kod jest sprawdzany wyłącznie na serwerze i nie trafia do historii rozmowy.

## Wdrażanie (Render)
1. `./deploy.sh "Opis zmian"` robi commit i push na GitHub (`hubinatorC4/luna-app`, gałąź `main`).
2. Jeśli w Renderze połączysz repozytorium z GitHubem, wdrożenie uruchomi się samo. W przeciwnym razie kliknij **Manual Deploy**.
3. Przy nowej wersji podbij `VERSION` w `static/sw.js` i `server.py`. Zainstalowane aplikacje pokażą wtedy komunikat **„Dostępna nowa wersja – odśwież”**.

Konfiguracja usługi jest w `render.yaml` (plan free, Frankfurt, health check `/api/health`).

> ⚠️ Darmowy Render ma **ulotny dysk**. Zmiany z panelu producenta (`data/config.json`, `data/catalog.json`) i przesłane pliki znikają po każdym wdrożeniu. Przed aktualizacją zrób **Eksport JSON**, a po niej **Import**.

## Obrazy
- Stroje, pozy i sylwetki: wrzuć do `/workspace` pliki `luna_outfit_<id>.jpg`, `luna_pose_<id>.jpg`, `luna_body_<id>.jpg` i uruchom `python3 tools/build_images.py`. Skrypt tworzy wersje 1x/2x w JPEG i WebP, a także awatary 256/512/1024, ikony PWA i favicon.
- Brakujące pozycje katalogu (np. sukienka koktajlowa, sylwetki) wyświetlają zastępczy obraz z napisem „wkrótce”.
- Dozwolone są tylko stonowane obrazy, bez treści rozbieranych czy erotycznych.

## Katalog i plany
Katalog (`catalog.py`, nadpisywany przez `data/catalog.json`) opisuje plany, postacie, stroje, pozy i sylwetki. Każdą pozycję można w panelu przypisać do innego planu. Gating działa po stronie klienta, bo plany są na razie demonstracyjne.

## Muzyka
Wolno używać wyłącznie utworów na licencjach pozwalających na redystrybucję (CC0, domena publiczna, CC BY). Każdy utwór trzeba dopisać do `static/music/LICENSES.md` i `playlist.json` (tytuł, autor, źródło, licencja). Nie dodawaj popularnych utworów chronionych prawem autorskim.

## Bezpieczeństwo treści
Stała linia bezpieczeństwa po stronie serwera i ujawnianie, że Luna jest AI, nie dają się wyłączyć z panelu.
