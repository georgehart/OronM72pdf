# bloeddrukverslag
geeft als argument het csv bestand eventueel met path  : "python3 bloedrukverslag.py ./data/BP_110326_240626.csv"
in de setupfolder is een JSON bestand met medicatie schema en opmerkingen

### CSV bestand
Data columns (total 17 columns):
 #   Column                               Non-Null Count  Dtype 
---  ------                               --------------  ----- 
 0   Datum                                154 non-null    object
 1   Tijd                                 154 non-null    object
 2   Systolisch (mmHg)                    154 non-null    int64 
 3   Diastolisch (mmHg)                   154 non-null    int64 
 4   Hartslag (spm)                       154 non-null    int64 
 5   Symptomen                            154 non-null    object
 6   Ingenomen                            154 non-null    object
 7   TruRead                              154 non-null    object
 8   Onregelmatige hartslag gedetecteerd  154 non-null    object
 9   Lichaamsbeweging                     154 non-null    object
 10  Manchetaanleggingsgids               154 non-null    object
 11  Positie-indicator                    154 non-null    object
 12  Meetmodus                            154 non-null    object
 13  Foutcode                             154 non-null    object
 14  Mogelijke AFib                       154 non-null    object
 15  Apparaat                             154 non-null    object
 16  Opmerkingen                          154 non-null    object
dtypes: int64(3), object(14)


Datum,Tijd,Systolisch (mmHg),Diastolisch (mmHg),Hartslag (spm),Symptomen,Ingenomen,TruRead,Onregelmatige hartslag gedetecteerd,Lichaamsbeweging,Manchetaanleggingsgids,Positie-indicator,Meetmodus,Foutcode,Mogelijke AFib,Apparaat,Opmerkingen
