# stos

Prosty w obsłudze klient konsolowy do znanej i lubianej przez studentów platformy [STOS](http://kaims.pl/~kmocet/stos/).

## Zależności

- Python 3.3+
- beautifulsoup4
- colorama
- requests
- tabulate

## Instalacja

Sklonuj to repozytorium, następnie dodaj jego lokalizację do zmiennej PATH.

## Użycie

Aby dokonać jednorazowej inicjalizacji w obecnym folderze, wydaj polecenie:

```
stos init IDENTYFIKATOR_ZADANIA
```

IDENTYFIKATOR_ZADANIA można znaleźć w adresie URL zadania. Na przykład, dla zadania "Tarzan2" (*https://kaims.pl/~kmocet/stos/index.php?p=show&id=365*), identyfikator to `365`. Po pomyślnej inicjalizacji w obecnym folderze powstanie folder `.stos`, w którym będzie trzymana konfiguracja. Dzięki niemu, po jednorazowym zalogowaniu się nie trzeba więcej podawać nazwy użytkownika (numeru indeksu) i hasła. Uwaga: nazwa użytkownika (numer indeksu) i hasło są trzymane w jawnym tekście.

Aby wysłać kod źródłowy na STOS, wydaj polecenie:

```
stos push
```

Wszystkie pliki **\*.cpp**, **\*.h**, **\*.hpp** z folderu, w którym dokonano inicjalizacji, zostaną wgrane na STOS jako rozwiązanie zadania. Po chwili wyświetli się tabela wyników.

Jeśli chcesz zobaczyć tabelę wyników, nie wysyłając rozwiązania na STOS, wydaj polecenie:

```
stos status
```
