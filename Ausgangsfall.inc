***-----LRP-----***

sets

g       Knoten der Graphen G1 und G2
         /j1*j3, i1*i10/

k       Touren im LRP
         /k1*k20/

j       potenzielle BS-Standorte
         /j1*j3/

i       Kunden
         /i1*i10/
;

parameters

akku_s        Maximale Streckenreichweite des Akkus [m]
              /4500/

akku_t        Maximale Einsatzdauer des Akkus [Zeitslots]
              /24/

a(i) Belieferungsfenster Beginn fuer Kunde i [Zeitslots]
        /
        i1      1
        i2      20
        i3      50
        i4      70
        i5      80
        i6      80
        i7      50
        i8      40
        i9      30
        i10      20/

b(i)   Belieferungsfenster Ende fuer Kunde i [Zeitslots]

     /  i1      10
        i2      30
        i3      70
        i4      80
        i5      90
        i6      90
        i7      96
        i8      90
        i9      90
        i10      90/

c             Kostensatz pro Distanzeinheit [je m]
                /0.000434/

Cap(j)          Kapazität einer Station  [Einheitspaket]
              / j1      15
                j2      15
                j3      5/

Comp          Kapazität eines LR [Einheitspaket]
              /2/

close(j)      Belieferungsende in BS j [Zeitslots]
     /  j1      96
        j2      96
        j3      48/

cp     		Personalkostensatz pro min[Euro]
                 /0.073667/
* entspricht 4.42 Euro pro Stunde

d(i)   Nachfrage des Kunden i  [Einheitspaket]
        /
        i1      1
        i2      2
        i3      1
        i4      2
        i5      2
        i6      1
        i7      1
        i8      2
        i9      1
        i10     1/

flat    Mietkostenpauschale [Euro]
        /11.90/

open(j)       Belieferungsbeginn in BS j [Zeitslots]
     /  j1      0
        j2      0
        j3      24/

p_s            Sicherheitspuffer für die Reichweite des Akkus [m]
              /500/

p_t            Sicherheitspuffer für die Einsatzdauer des Akkus [Zeitslots]
              /3/

sp              Durchschnittliche Geschwindigkeit des Lierroboters [m pro min]
                /75/
* entspricht 4.5 kmh

sp_max          Maximal zulässige Geschwindigkeit die für den LR gilt [m pro min]
                /100/
* entspricht 6 kmh

sz              Servicezeit bei jedem Kunden [Zeitslots]
                /3/

z               Länge eines Zeitslots [Minuten]
                /5/
;

table dis(g,h)   Distanzmatrix zwischen g und h [m]

            j1          j2      j3      i1      i2      i3      i4      i5      i6      i7      i8      i9      i10
   j1       0           700     950     1200    1000    800     500     600     700     350     500     750     950
   j2       700         0       500     850     240     800     450     1100    500     1100    800     800     1600
   j3       950         550     0       550     350     550     550     1200    800     1200    1000    1100    1700
   i1       1200        850     550     0       650     650     850     1500    1100    1400    1300    1400    1900
   i2       1000        240     350     650     0       750     700     1400    700     1300    1000    1000    1900
   i3       800         800     550     650     750     0       450     1100    1000    1000    1000    1000    1500
   i4       500         450     550     850     700     450     0       850     550     750     550     600     1200
   i5       600         1100    1200    1500    1400    1100    850     0       1200    500     1100    1300    600
   i6       700         500     800     1100    700     1000    550     1200    0       950     650     600     1500
   i7       350         1100    1200    1400    1300    1000    750     500     950     0       650     1000    550
   i8       500         800     1000    1300    1000    1000    550     1100    650     650     0       450     1200
   i9       750         800     1100    1400    1000    1000    600     1300    600     1000    450     0       1200
   i10      950         1600    1700    1900    1900    1500    1200    600     1500    550     1200    1200    0;

fz(g,h) = dis(g,h) / sp ;
fzslot(g,h) = fz(g,h) / z ;
fzr(g,h) = round(fzslot(g,h), 0) ;





