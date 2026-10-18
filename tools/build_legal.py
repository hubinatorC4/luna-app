# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_common import HEAD, FOOT, VER
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
act = {k: "" for k in ("a_butik", "a_test", "a_join", "a_face", "a_sup", "a_wall")}
DISC = [("Polski", "Luna to asystentka AI do nauki mówienia i pracy z głosem. Produkt w żaden sposób nie ma na celu seksualizacji kobiet."),
        ("English", "Luna is an AI assistant for learning to speak and working with your voice. The product is in no way intended to sexualise women."),
        ("Español", "Luna es una asistente de IA para aprender a hablar y trabajar la voz. El producto no pretende en modo alguno sexualizar a las mujeres."),
        ("Deutsch", "Luna ist eine KI-Assistentin zum Sprechenlernen und für die Arbeit mit der Stimme. Das Produkt zielt in keiner Weise darauf ab, Frauen zu sexualisieren."),
        ("Українська", "Луна — це ШІ-асистентка для навчання мовлення та роботи з голосом. Продукт жодним чином не має на меті сексуалізацію жінок.")]
body = """<main class="page legal">
<h1>Regulamin aplikacji „Luna mówi jak jest”</h1>
<p class="hint">Obowiązuje od 18.10.2026 r. Dotyczy strony https://luna-voice-coach.onrender.com, aplikacji webowej (PWA) oraz aplikacji na Androida (com.lunamowijakjest.app).</p>
<p class="disclaimer" data-disclaimer>Luna to asystentka AI do nauki mówienia i pracy z głosem. Produkt w żaden sposób nie ma na celu seksualizacji kobiet.</p>
<div class="card"><b>Zastrzeżenie w 5 językach</b><ul>""" + "".join(f"<li lang=\"{l[:2].lower() if l != 'Українська' else 'uk'}\"><b>{l}:</b> {t}</li>" for l, t in DISC) + """</ul></div>

<h2>§ 1. Usługodawca i charakter projektu</h2>
<p>„Luna mówi jak jest” to projekt fanowski – i taki pozostanie. Usługodawcą (sprzedawcą) jest: <b id="sellerName">[dane sprzedawcy zostaną uzupełnione]</b><span id="sellerAddr"></span><span id="sellerNip"></span><span id="sellerVat"></span>. Kontakt: „Czat z twórcą” w aplikacji lub zakładka <a href="/problemy.html">Problemy techniczne</a>.</p>
<p>Luna jest asystentką AI. Jej postać i głos zostały wygenerowane sztucznie. Porady Luny mają charakter edukacyjny i nie zastępują konsultacji z foniatrą ani logopedą.</p>

<h2>§ 2. Wymóg pełnoletności (18+)</h2>
<p>Z aplikacji mogą korzystać wyłącznie osoby pełnoletnie. Przy pierwszym uruchomieniu, przy zakładaniu konta oraz w formularzach zgłoszeniowych prosimy o podanie daty urodzenia i złożenie oświadczenia: „Oświadczam, że jestem osobą pełnoletnią (18+) i posiadam własne konto bankowe.”</p>
<p>Jest to <b>wyłącznie oświadczenie użytkownika</b> – nie weryfikujemy wieku ani posiadania konta bankowego. Zapisujemy datę i godzinę złożenia oświadczenia. Osobom poniżej 18 lat uprzejmie odmawiamy dostępu.</p>

<h2>§ 3. Konto</h2>
<p>Konto zakładasz, podając adres e-mail i hasło (przechowujemy wyłącznie jego bezpieczny skrót Argon2id). Dopóki nie uruchomimy wysyłki e-maili, konta są oznaczone jako niepotwierdzone. W ustawieniach możesz pobrać swoje dane (eksport) i trwale usunąć konto.</p>

<h2>§ 4. Plany i dostęp miesięczny</h2>
<ul><li>Aplikację pobierasz za darmo. Plan <b>Darmowy</b> obejmuje m.in. ok. 5 minut rozmowy z Luną dziennie (limit może się zmienić), test głosu, oglądanie Luna Live (bez zadawania pytań) i 1 strój.</li>
<li>Plan <b>Podstawowa</b> jest <b>bezpłatny</b> – wystarczy założyć konto.</li>
<li>Plany <b>Premium</b> (<span data-price="premium">cena w Cenniku</span>) i <b>Pro</b> (<span data-price="pro">cena w Cenniku</span>) to <b>jednorazowe dostępy na 30 dni</b>, a nie subskrypcje: nie odnawiają się automatycznie. Po 30 dniach wracasz do planu Podstawowa (z kontem), dopóki nie kupisz kolejnego miesiąca. Nie oferujemy planów rocznych.</li>
<li>Każdy wyższy plan obejmuje funkcje niższych. Aplikacja przypomni o wygaśnięciu dostępu na 7 dni i na 1 dzień wcześniej.</li>
<li>Testerzy otrzymują Premium bezpłatnie na 2 miesiące<span data-tester-value></span>.</li></ul>

<h2>§ 5. Ceny i VAT</h2>
<p>Wszystkie ceny planów i pozycji w Butiku Luny są cenami brutto – <b>zawierają podatek VAT</b>. Ceny podajemy w złotych (PLN), jedną cenę za każdy plan. Do czasu publikacji cennika ceny mogą być ukryte. Przy zakupach w aplikacji z Google Play cenę w walucie lokalnej ustala i nalicza Google Play, które rozlicza też należny VAT.</p>

<h2>§ 6. Płatności</h2>
<ul><li><b>Wersja przeglądarkowa:</b> płatności obsługuje Stripe (Stripe Payments Europe Ltd.) w trybie jednorazowym, w złotych – BLIK-iem lub kartą (opcjonalnie Przelewy24). Dostęp przyznajemy automatycznie po potwierdzeniu płatności przez Stripe. Potwierdzenie płatności otrzymasz e-mailem od Stripe.</li>
<li><b>Aplikacja na Androida (Google Play):</b> płatności w aplikacji odbywają się wyłącznie przez Google Play Billing (dostępny jest tam m.in. BLIK). W tej wersji nie używamy Stripe.</li>
<li>Nigdy nie prosimy o hasła, kody BLIK ani numery kart – nie podawaj ich w czacie ani w zgłoszeniach.</li>
<li>Do czasu uruchomienia płatności przyciski zakupu są oznaczone jako „wkrótce”.</li></ul>

<h2>§ 7. Prawo odstąpienia od umowy (treści cyfrowe)</h2>
<p>Konsumentowi przysługuje co do zasady prawo odstąpienia od umowy zawartej na odległość w ciągu 14 dni. Zgodnie z art. 38 ust. 1 pkt 13 ustawy z dnia 30 maja 2014 r. o prawach konsumenta prawo to <b>nie przysługuje</b> w przypadku treści cyfrowych niedostarczanych na nośniku materialnym, jeżeli spełnianie świadczenia rozpoczęło się za wyraźną i uprzednią zgodą konsumenta, który został poinformowany przed jego rozpoczęciem, że po spełnieniu świadczenia utraci prawo odstąpienia od umowy, i przyjął to do wiadomości. Przed płatnością prosimy o zaznaczenie zgody: „Żądam natychmiastowego dostarczenia treści cyfrowych i przyjmuję do wiadomości, że tracę prawo odstąpienia od umowy z chwilą rozpoczęcia dostarczania.” Potwierdzenie tej zgody przekazujemy wraz z potwierdzeniem zakupu. Zwroty zakupów z Google Play regulują zasady Google Play.</p>

<h2>§ 8. Awatary i obrazy</h2>
<p>Awatarem może być wyłącznie gotowa ikona, awatar z galerii, awatar z generatora w aplikacji albo obraz wygenerowany przez AI. <b>Nie wolno wgrywać zdjęć prawdziwych osób.</b> Przy wgrywaniu wymagamy oświadczenia, że obraz został wygenerowany przez AI i nie przedstawia prawdziwej osoby. Serwer odrzuca pliki z metadanymi aparatu bez znacznika AI i usuwa wszystkie metadane – ta kontrola nie jest w 100% skuteczna. Awatary można zgłaszać; moderator może je usunąć lub zablokować użytkownika.</p>

<h2>§ 9. Zasady zachowania i treści</h2>
<p>Luna, Luna Live i czaty są przestrzenią kulturalną i SFW. Zabronione są treści obraźliwe, seksualne, nienawistne oraz spam. Moderator może usuwać wiadomości i blokować użytkowników. Stroje w Butiku Luny są zawsze eleganckie i nieodsłaniające.</p>

<h2>§ 9a. Ścianka Agentek Głosu, komentarze, oceny i głosy</h2>
<ul><li>Wpisy na Ściance Agentek Głosu i komentarze (także pod produktami w Butiku) może publikować osoba pełnoletnia – zalogowana albo podająca nick i potwierdzająca ukończenie 18 lat.</li>
<li>Wszystkie komentarze oraz wpisy nowych autorów sprawdza moderator przed publikacją. Wpisy autorów, którym zatwierdziliśmy co najmniej 3 wpisy, publikują się od razu, ale nadal podlegają moderacji i zgłoszeniom.</li>
<li>Zakazane są: wizerunek prawdziwych osób bez ich zgody, treści o charakterze seksualnym, mowa nienawiści, nękanie, spam i reklama. Obrazy mogą być wyłącznie wygenerowane przez AI; automatyczna kontrola metadanych nie jest stuprocentowo skuteczna, dlatego odpowiedzialność za oświadczenie ponosi autor.</li>
<li>Agentki i postacie AI publikowane przez użytkowników muszą być oznaczone jako postacie AI. Nie mogą udawać prawdziwych osób.</li>
<li>Autor może w każdej chwili edytować lub usunąć swój wpis. Moderator może ukryć lub usunąć treść naruszającą regulamin i zablokować możliwość publikowania.</li>
<li>Głosy 👍/👎 i liczniki pokazują wyłącznie prawdziwe dane: jeden głos na konto lub urządzenie; ponowne kliknięcie usuwa głos. Nie nagradzamy polubień ani obserwowania profili.</li>
<li>Liczniki wyświetleń liczą wpis raz na sesję, gdy jest widoczny przez co najmniej 1 sekundę. Konta i urządzenia wykazujące cechy botów lub fałszywych kont (np. seria polubień w kilka sekund, powtarzane komentarze, jednorazowe adresy e-mail) mogą zostać automatycznie ukryte w liczeniu; usunięcie konta zawsze zatwierdza człowiek, a omyłkowo oznaczone konto przywracamy. Polubienia i komentarze kont bez potwierdzonego adresu e-mail nie są wliczane do publicznych liczników.</li>
<li>Treść naruszającą zasady można zgłosić przyciskiem „Zgłoś”.</li></ul>

<h2>§ 10. Wsparcie dobrowolne i brak reklam</h2>
<p>Dobrowolne wpłaty na stronie „Wesprzyj Lunę” (tylko w wersji przeglądarkowej) nie dają dostępu do płatnych funkcji. Aplikacja nie zawiera reklam.</p>

<h2>§ 11. Reklamacje i kontakt</h2>
<p>Reklamacje i problemy zgłaszaj przez <a href="/problemy.html">Problemy techniczne</a> albo „Czat z twórcą”. Czas odpowiedzi zależy od dostępności osób w biurze, ale nie będzie dłuższy niż 30 dni.</p>

<h2>§ 12. Dane osobowe</h2>
<p>Zasady przetwarzania danych opisuje <a href="/privacy.html">Polityka prywatności</a>.</p>

<h2>§ 13. Zmiany regulaminu</h2>
<p>O zmianach regulaminu poinformujemy w aplikacji z wyprzedzeniem. Zakupiony dostęp pozostaje ważny na dotychczasowych zasadach do końca opłaconego okresu.</p>
</main>
"""
h = HEAD.format(title="Regulamin – Luna mówi jak jest", desc="Regulamin aplikacji Luna mówi jak jest: 18+, konto, dostęp miesięczny, ceny z VAT, płatności BLIK, prawo odstąpienia, awatary AI.", ver=VER, cls="", **act)
js = '<script src="/legal.js?v=' + VER + '"></script>\n<script src="/helpbot-loader.js?v=' + VER + '"></script>\n'
open(os.path.join(S, "regulamin.html"), "w", encoding="utf-8").write(h + body + FOOT + js + "</body>\n</html>\n")
print("ok")
