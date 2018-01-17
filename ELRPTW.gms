**------------ELRP-TW------------**
option optcr = 0.1;

*-------------------------
*        Indexmengen
*-------------------------
sets

  g              Knoten des Graphen
  k              Touren
  i(g)           Kunden
  j(g)           potenzielle BS

alias (g,h)
alias (i,l);

*-------------------------
*        Parameter
*-------------------------
parameters
  a(i)           Frueheste Belieferungszeitpunkt fuer Kunde i
  akku_s         Maximale Streckenreichweite des Akkus
  akku_t         Maximale Einsatzdauer des Akkus
  b(i)           Spaeteste Belieferungszeitpunkt fuer Kunde i
  c              Kosten der Lieferung mit einem LR pro Distanzeinheit
  Cap(j)         Kapazitaet einer Basisstation j
  close(j)       Ende der Belieferungszeit der BS j
  Comp           Anzahl der Compartments des Lieferroboters
  cp             Personalkostensatz pro min
  dis(g,h)       Distanz zwischen Knotenpunkt g und h
  d(i)           Nachfrage am Kundenort i
  flat           Mietkostenpauschale pro Tour
  fz(g,h)        Fahrzeit von Ort g nach Ort h
  fzslot(g,h)    Fahrzeit von Ort g nach Ort h in Zeitslots
  fzr(g,h)       Gerundete Fahrzeit von Ort g nach Ort h
  open(j)        Beginn der Belieferungszeit der BS j
  p_s            Sicherheitspuffer für die Streckenreichweite des Akkus
  p_t            Sicherheitspuffer für die Einsatzdauer des Akkus
  sp             Durchschnittliche Geschwindigkeit des Lieferroboters
  sp_max         Maximal zulässige Geschwindigkeit
  sz             Servicezeit bei jedem Kunden
  z              Minuten eines Zeitslots im Verhältnis zu einer Stunde
;

*-------------------------
*        Variablen
*-------------------------
free variables

  ZFW_LRP        Zielfunktionswert WLRP;

binary variables

  alpha(g,h,k)   1 wenn Knoten g dem Knoten h auf Tour k vorangeht				checked
  beta(i,j)      1 wenn Kunde i von der Basisstation j beliefert wird
  gamma(j)       1 wenn die Basisstation j errichtet wird
  y(g,k)         1 wenn Ort g auf Tour k besucht wird;

positive variables

  u(g,k)         Hilfsvariable ;

Integer Variable
  t(g,k)         Ankunftszeit an Ort g auf Tour k
  tau_BS(j,k)    Abfahrtszeit bei der Basisstation j auf Tour k;

$include Ausgangsfall.inc

*-------------------------
*        Equations
*-------------------------

equations

Zielfunktion_LRP         Kosten der Stationen und Lieferungen

*****Tourenplanung***
KundeTour                Jeder Kunde wird genau einer Tour zugewiesen
OrtVerlassen             Jeder angefahrene Ort wird auch wieder verlassen
OrtAnfahren              Jeder angefahrene Ort i wird einmal angefahren
Kurzzyklen               Keine Kurzzyklen
SelbstAnfahren           Kein Knoten darf sich selbst anfahren
FahrzeugKap              Maximale Fahrzeugkapazität muss eingehalten werden

*****Standortplanung - Erweiterung zum LRP ***
KundeStationTour         Kunde nur Station zuordnen wenn beide derselben Tour zugeordnet sind
KundeEineStation         Kundenort muss genau einer Station zugeordnet werden
StationKap               Kapazitätsbeschränkung einer Station und Station nur anfahren wenn eroeffnet

*****Electric LRP***
BatteryKap               Maximale Distanz mit Batterieladung
BatteryZeit              Maximale Einsatzdauer der Batterie
Geschwindigkeit          Maximale Geschwindigkeit muss von dem LR eingehalten werden

*****Zeiten***
FruehesteAnkunftKunde    Belieferung fruehestens ab Zeitfenster fuer Kunde i
SpaetesteAnkunftKunde    Späteste Ankunftszeit beim Kunden muss vor dem Ende des Kundenfesters sein
FahrtzeitVonKunden       Folgeort kann erst nach Service- und Fahrtzeit von einem Kunden erreicht werden
FruehesteAbfahrtBS       Station muss geöffnet sein bevor LR den Laden verlassen kann
SpaetesteAnkunftBS       Ankunft bei der BS muss vor deren Schließung erfolgen
;

*-------------------------
*        Zielfunktion
*-------------------------
Zielfunktion_LRP..
  ZFW_LRP =e= sum((k,j),flat*y(j,k)) + sum((j), ((close(j)-open(j))*z*cp)*gamma(j)) + sum((g,h,k), dis(g,h) * c * alpha(g,h,k)) ;

	checked 
  
*--------------------------------------------
*        Restriktionen für die Tourenplanung
*--------------------------------------------
*****Zuordnungen und Bedingungen Kunde Tour Station***

** Jeder Kunde wird genau einer Tour zugewiesen
KundeTour(i)..
  sum(k, y(i,k)) =e= 1;
  
  
	checked
  

*Jeder angefahrene Ort g wird einmal verlassen
OrtVerlassen(g,k)..
sum(h, alpha(g,h,k)) =e= y(g,k);


	checked
	

*Jeder angefahrene Ort h wird einmal angefahren
OrtAnfahren(h,k)..
sum(g, alpha(g,h,k)) =e= y(h,k);


	checked
	

*Keine Kurzzyklen
Kurzzyklen(l,i,k)$(ord(i)<>ord(l))..
  u(l,k) - u(i,k) + card(i)*alpha(l,i,k) =l= card(i) - 1;
  
 
	checked
	

* Kein Knoten darf sich selbst anfahren
SelbstAnfahren(g,k)..
         alpha(g,g,k)    =e=     0;
	
	
	checked

	
*Maximale Fahrzeugkapazität muss eingehalten werden
FahrzeugKap(k)..
  sum((i),d(i)*y(i,k)) =l= Comp;
  
  
	checked

*------------------------------------------------
*   Erweiterung um die Stationszuordnung zum LRP
*------------------------------------------------

* Kunde kann nur von Station beliefert werden, wenn beide derselben Tour zugeordnet sind
KundeStationTour(i,j,k)..
  y(i,k) + y(j,k) - beta(i,j) =l= 1;

*Kundenort muss genau einer Station zugeordnet werden
KundeEineStation(i)..
  sum(j, beta(i,j)) =e= 1;

*Kapazitätsbeschränkung einer Station und Station nur anfahren wenn eroeffnet
StationKap(j)..
  sum((i), d(i)*beta(i,j)) =l= Cap(j)*gamma(j);
  
  
	checked
  

*--------------------------------------------
*        Erweiterung zum Electric LRP
*--------------------------------------------

* Batteriekapazität limitiert die gefahrene Strecke für jede Tour
BatteryKap(k)..
sum((g,h)$(ord(g)<>ord(h)), dis(g,h)*alpha(g,h,k)) =l= akku_s + p_s;


	checked



* Maximale Einsatzdauer der Batterie
BatteryZeit(k)..
         sum((i,g), (sz + fzr(i,g))*alpha(i,g,k)) + sum((j,h), fzr(j,h)*alpha(j,h,k)) =l= akku_T + p_T;

	
	checked
	
	
	
* Maximal zulässige Geschwindigkeit nicht überschreiten
Geschwindigkeit..
         sp =l= sp_max;

*-----------------------------------------------
*        Erweiterung um Zeitfenster zum ELRP-TW
*-----------------------------------------------

****Kunden****

* Ankunftszeit beim Kunden darf erst ab Beginn des Kundenfesters sein
*für jede Tour, auf der i angefahren wird gilt das
FruehesteAnkunftKunde(i,k)..
         t(i,k) =g= a(i)*y(i,k);

* Späteste Ankunftszeit beim Kunden muss vor dem Ende des Kundenfesters sein
* Abfahrtszeit entspricht dem Belieferungsende
SpaetesteAnkunftKunde(i,k)..
         t(i,k)*y(i,k) =l= b(i);

* Folgeort kann erst nach Service- und Fahrtzeit von einem Kunden erreicht werden
* durch =e= werden im Vergleich zu =l= unnötige Pufferzeiten beim Kunden verhindert
FahrtzeitVonKunden(i,g,k)..
         (t(i,k)  + fzr(i,g) + sz - t(g,k))*alpha(i,g,k) =e= 0     ;

*---------Basisstationen----------
*Station muss geöffnet sein, bevor LR den Laden verlassen kann
FruehesteAbfahrtBS(j,i,k)..
         (open(j) + fzr(j,i) - t(i,k))*alpha(j,i,k) =l= 0    ;

* Ankunft bei der BS muss vor deren Schließung erfolgen
SpaetesteAnkunftBS(j,k)..
         (t(j,k)-close(j))*y(j,k) =l= 0;


*-----------------------------------------------
*        Zusätzliche Ausgaben
*-----------------------------------------------
$ontext
Kein Grundbestandteil des ELRP-TW: Das ELRP-TW funktioniert auch,
wenn diese Ausgaben auskommentiert werden. Diese Werte haben keinen
Einfluss auf den Zielfunktionswert, geben allerdings weitere
Auskünfte, die für eine Interpretation sinnvoll sind.
$offtext

Positive Variables
qk(k)    Gefahrene Strecke auf Tour k
q        Gesamte Strecke
dur(k)   Dauer einer Tour k
durA     Dauer aller Touren
pco      Personalkosten
vaco     Variable Kosten
miete    Mietkosten;

Equations
StreckeTour
StreckeGesamt
FahrtzeitVonStation      Bestimmung der Abfahrtszeit von einer Basisstation
DauerTour                Bestimmung der Dauer einer Tour
DauerGesamt              Bestimmung der gesamten Dauer über alle Touren
Perskosten               Bestimmung der Personalkosten
VariableKosten           Bestimmung der variablen Kosten
MietKosten               Bestimmung der Mietkosten für die LR;

StreckeTour(k)..
         qk(k)   =e=     sum((g,h)$(ord(g)<>ord(h)), dis(g,h)*y(g,k)*y(h,k));
StreckeGesamt..
         q       =e=     sum(k, qk(k));
FahrtzeitVonStation(i,j,k)..
         (tau_BS(j,k) + fzr(j,i) - t(i,k))*alpha(j,i,k) =e= 0;
DauerTour(k)..
         dur(k)  =e=     sum((i,g), (sz + fzr(i,g))*alpha(i,g,k)) + sum((j,h), fzr(j,h)*alpha(j,h,k));
DauerGesamt..
         durA    =e=     sum(k, dur(k));
Perskosten..
         pco     =e=     sum(j, ((close(j)-open(j))*z*cp)*gamma(j));
VariableKosten..
         vaco    =e=     sum((g,h,k)$(ord(h)<>ord(g)), dis(g,h) * c *alpha(g,h,k));
MietKosten..
         miete   =e=     sum((k,j),flat*y(j,k));

*-------------------------
*        Bounds
*-------------------------
$ontext
Bounds optimieren den Code: Durch die logischen Grenzen kann der Solver
das Ergebnis schneller finden. Somit verringert sich die Rechenzeit.
-> Dient der Effizienz des Codes
$offtext

t.up(g,k) = 96;

*-------------------------
*        Modellausgabe
*-------------------------
model LRP /all/;
LRP.reslim = 86400;
solve LRP minimizing ZFW_LRP using MINLP;
display ZFW_LRP.l, alpha.l, beta.l, gamma.l;
display y.l, tau_BS.l, t.l;
display dur.l, durA.l;
display qk.l, q.l;
display pco.l, vaco.l, miete.l;
display fz, fzslot, fzr;
