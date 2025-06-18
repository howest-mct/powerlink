# Projectgegevens

**VOORNAAM NAAM:** Michiel Gekiere

**Sparringpartner:** Chadia Willems

**Projectsamenvatting in max 10 woorden:** Slim domoticasysteem voor energiezuinig huis met automatische en handmatige bediening.

**Projecttitel:** PowerLink

# Tips voor feedbackgesprekken

## Voorbereiding

> Bepaal voor jezelf waar je graag feedback op wil. Schrijf op voorhand een aantal punten op waar je zeker feedback over wil krijgen. Op die manier zal het feedbackgesprek gerichter verlopen en zullen vragen, die je zeker beantwoord wil hebben, aan bod komen.

## Tijdens het gesprek:

> **Luister actief:** Schiet niet onmiddellijk in de verdediging maar probeer goed te luisteren. Laat verbaal en non-verbaal ook zien dat je aandacht hebt voor de feedback door een open houding (oogcontact, rechte houding), door het maken van aantekeningen, knikken...

> **Maak notities:** Schrijf de feedback op zo heb je ze nog nadien. Noteer de kernwoorden en zoek naar een snelle noteer methode voor jezelf. Als je goed noteert,kan je op het einde van het gesprek je belangrijkste feedback punten kort overlopen.

> **Vat samen:** Wacht niet op een samenvatting door de docenten, dit is jouw taak: Check of je de boodschap goed hebt begrepen door actief te luisteren en samen te vatten in je eigen woorden.

> **Sta open voor de feedback:** Wacht niet op een samenvatting door de docenten, dit is jouw taak: Check of je de boodschap goed hebt begrepen door actief te luisteren en samen te vatten in je eigen woorden.`

> **Denk erover na:** Denk na over wat je met de feedback gaat doen en koppel terug. Vind je de opmerkingen terecht of onterecht? Herken je je in de feedback? Op welke manier ga je dit aanpakken?

## NA HET GESPREK

> Herlees je notities en maak actiepunten. Maak keuzes uit alle feedback die je kreeg: Waar kan je mee aan de slag en wat laat je even rusten. Wat waren de prioriteiten? Neem de opdrachtfiche er nog eens bij om je focuspunten te bepalen.Noteer je actiepunten op de feedbackfiche.

# Feedforward gesprekken

## Gesprek 1 (Datum: 26/05/2025)

Lector: Stijn

Vragen voor dit gesprek:

- vraag 1: Is de database in orde?
- vraag 2: Hoe best omgaan met tijdschema?
- vraag 3: Moet er een kolom zijn voor batterytracking?

Dit is de feedback op mijn vragen.

- feedback 1:
  Waarom user input bij website? -> niet gebruiken
  Actuator en sensors in 1 tabel plaatsen -> Componenten
  Signals & measurements ook samen zetten -> historiek, value hier hangt af van wat je uit uw componenten tabel gebruikt
- feedback 2:
  Temp en licht schedule samen zetten
  Type tabel maken voor temp, airco en licht
  Database simpeler maken zodat je als er dingen bij komen die niet een aparte tabel nodig hebben
- feedback 3:
  Batterij tabel weg

## Toermoment 1 (Datum: 03/06/2025)

- Bij paar testen batterijverbruik kunnen inschatten
- Paar grafieken maken
- Feedforward ok
- Toggle ok
- Database ok
- Geen branches -> moet echt bv. backend & frontent

## Gesprek 2 (Datum: 04/06/2025)

Lector: Stijn

Vragen voor dit gesprek:

- vraag 1: Hoe moet ik de frontend aanpakken?

Dit is de feedback op mijn vragen.

- feedback 1:
  Database niet aanpassen aan de hand van uw frontend
  Vraag: hoe filteren uit database wat wel of niet getoond moet worden?
  Werd dat doorgegeven dat je dat moest doorgeven aan db?
  Wat studenten bijhouden zijn instellingen frontend
  Op frontend vaste waarde tonen (altijd) op gelijk welke manier maar moet niet worden bijgehouden in db
  Het lukt wel om in de db bij te houden
  Is een prototype -> maakt niet uit welke componenten getoond worden dus je toont gewoon alles
  Niet beginnen met frontend manipuleren met wat wel of niet getoond gaat worden
  Als je veel tijd hebt mag je het doen, zorg voor 3 - 4 verschillende pagina’s (real life, historiek)
  Dynamische website idee is pas 2de jaar
  Mag het doen als je wilt, maar maak het niet te complex

## Toermoment 2 (Datum: 10/06/2025)

- Temperatuur waardes samen zetten waar nodig, huidige waarde & ingestelde waarde
- Tijdschema voor snachts & dat je er meerdere op 1 dag kunt hebben
- Mogelijkheid om persoon aan huishouden toe te voegen

## Toermoment 3 (Datum: 17/06/2025)

- Als je de schedule afzet disabelen of in grijs zetten zodat het duidelijk wordt dat het afstaat
- De setting is niet duidelijk dat het naar de potentiometer overgaat als je het aflegt
- Boven de schedule een melding 'manual control active'
- Verlichting via website aan en uit zetten?
- Uit knop?
- Website finetunen als er tijd is
- Feature/#id in titel van issues zetten
- Backup video nog maken
- Schema niet in projectfiche zetten, website wel
- Of ipv schema een foto van binnenkant huis
- Woorden highlighten in tekst projectfiche
- Foto uitzoomen zodat het kleiner is in de banner
- Meer feedback op website tonen & kleine dingen verbeteren
- In schedule vooral meer duidelijkheid
- Gewone gebruiker proberen te overtuigen

## Gesprek 3 (Datum: 18/06/2025)

Lector: Geert

Vragen voor dit gesprek:

- vraag 1: RaspBerry Pi start thuis niet meer op, wat nu?

Dit is de feedback op mijn vragen.

- feedback 1: Met nieuwe image proberen, lukte niet.
  Opnieuw met oude SD geprobeerd, dit lukte wel. Waarschijnlijk ergens een hardwarematige fout.

  ## Gesprek 4 (Datum: 18/06/2025)

Lector: Pieter-Jan

Vragen voor dit gesprek:

- vraag 1: Geen verbinding meer met GitHub, pushen of synchen lukt niet meer, wat nu?

Dit is de feedback op mijn vragen.

- feedback 1: .git file was corrupt, dus kopie genomen van de oude repo en de .git verwijderen. Clone nemen van de oude repo van op github.
  Dan de oude kopie plakken in de net geclone repo en dan committen en pushen.
