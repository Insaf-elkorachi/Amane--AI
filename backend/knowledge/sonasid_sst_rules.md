# Regles SST SONASID ajoutees a AMANE AI

Ce corpus doit etre utilise par AMANE AI pour enrichir les reclamations HSE, proposer les premieres mesures de securisation et citer les regles SONASID pertinentes. Les documents originaux sont stockes dans `backend/knowledge/documents_sonasid`.

## Utilisation par l'assistant

- Toujours donner la priorite a la securite immediate des personnes avant l'analyse documentaire.
- Identifier si la reclamation concerne une situation dangereuse ou un acte dangereux.
- Associer la reclamation aux regles SST SONASID ci-dessous quand les mots-cles correspondent.
- Ne jamais inventer une procedure: si la regle exacte n'est pas retrouvee, dire qu'une validation HSE est necessaire.
- Pour les rapports manager, conserver le nom de la regle source dans l'analyse RAG.

## Documents sources

### Regle SST N1 - EPI

Source: `documents_sonasid/SAS006 Règle SST N°1 EPI  12 juillet 2011.pdf`
Mots-cles: EPI, casque, lunettes, gants, chaussures de securite, protection individuelle, tenue de travail.
Usage AMANE: a utiliser pour toute reclamation liee a l'absence ou au mauvais port des equipements de protection individuelle.

### Regle SST N2 - Balisage

Source: `documents_sonasid/SAS006 Règle SST N°2 Balisage 18 Aout 2011.pdf`
Mots-cles: balisage, zone interdite, signalisation, rubalise, delimitation, acces zone dangereuse.
Usage AMANE: a utiliser lorsque la zone doit etre isolee, signalee ou protegee apres un incident ou une anomalie.

### Regle SST N3 - Manutention a proximite d'une charge suspendue

Source: `documents_sonasid/SAS006 Règle SST N°03 Manutention à proximité d'une charge suspendue Oct. 2011.pdf`
Mots-cles: charge suspendue, levage, manutention, grue, pont roulant, collision, ecrasement.
Usage AMANE: a utiliser pour les risques autour des charges en hauteur ou suspendues.

### Regle SST N4 - Geste de commandement

Source: `documents_sonasid/SAS006 Règle SST N°04 Geste de commandement 16 Janvier 2012.pdf`
Mots-cles: gestes de commandement, guidage, manoeuvre, levage, communication, chef de manoeuvre.
Usage AMANE: a utiliser quand une manoeuvre necessite un guidage clair entre operateurs.

### Regle SST N5 - Utilisation telephone cellulaire

Source: `documents_sonasid/SAS006 Règle SST N°05 Utilisation téléphone cellulaire 11 fév. 2012.pdf`
Mots-cles: telephone, portable, distraction, conduite, circulation, zone industrielle.
Usage AMANE: a utiliser pour les actes dangereux lies a l'usage du telephone en zone de travail.

### Regle SST N6 - Plan de prevention des entreprises exterieures

Source: `documents_sonasid/SAS006 Règle SST N°6 Plan de prévention des EE.pdf`
Mots-cles: entreprise exterieure, plan de prevention, intervention, sous-traitant, permis, coactivite.
Usage AMANE: a utiliser pour les travaux ou interventions impliquant des prestataires.

### Regle SST N7 - Conduite et engins

Source: `documents_sonasid/SAS006 Règle SST N°07 Conduite & Engin 13 Juin 2012.pdf`
Mots-cles: engin, conduite, chariot, vehicule, circulation, vitesse, conducteur.
Usage AMANE: a utiliser pour incidents de circulation interne, conduite dangereuse ou engins industriels.

### Regle SST N8 - Travaux en hauteur

Source: `documents_sonasid/SAS006 Règle SST N°08 Travaux en Hauteur 01 Aout 2012.pdf`
Mots-cles: hauteur, chute, harnais, garde-corps, plateforme, toiture, nacelle.
Usage AMANE: a utiliser pour tout risque de chute de hauteur ou intervention en hauteur.

### Regle SST N9 - Consignation

Source: `documents_sonasid/SAS006 Règle SST N°09 Consignation 22 nov. 2012.pdf`
Mots-cles: consignation, energie, verrouillage, cadenassage, isolement, electricite, intervention machine.
Usage AMANE: a utiliser pour travaux sur equipements, machines, energie electrique, hydraulique ou mecanique.

### Regle SST N10 - Chalumeau ou lance a oxygene

Source: `documents_sonasid/SAS006 Règle SST N°10 Utilisation Chalumeau ou Lance à Oxygène V 23 juillet 2013.pdf`
Mots-cles: chalumeau, oxygene, feu, incendie, brulure, point chaud, gaz.
Usage AMANE: a utiliser pour travaux par point chaud, oxycoupage et risques d'incendie.

### Regle SST N11 - Elinguage

Source: `documents_sonasid/SAS006 Règle SST N°11 L'élinguage V23 juillet 2013.pdf`
Mots-cles: elingue, elinguage, levage, crochet, charge, accessoire de levage.
Usage AMANE: a utiliser pour anomalies sur elingues, crochets, charges ou operations de levage.

### Regle SST N12 - Acces engins

Source: `documents_sonasid/SAS006 Règle SST N°12 Accès Engins 08 oct 2013.pdf`
Mots-cles: acces engin, monter, descendre, cabine, marchepied, trois points d'appui.
Usage AMANE: a utiliser pour les risques lors de l'acces aux engins ou postes de conduite.

### Regle SST N13 - Manutention manuelle gestes et postures

Source: `documents_sonasid/SAS006 Règle SST N°13 Manutention manuelle Gestes et postures 26 nov. 2013.pdf`
Mots-cles: manutention manuelle, posture, dos, charge, effort, ergonomie.
Usage AMANE: a utiliser pour les risques TMS, effort physique et manipulation manuelle.

### Regle SST N14 - Echafaudage

Source: `documents_sonasid/SAS006 Règle SST N°14 Utilisation de l'échafaudage Validé par le CSC V 20 Janvier 2014.pdf`
Mots-cles: echafaudage, plateforme, garde-corps, hauteur, montage, verification.
Usage AMANE: a utiliser pour les travaux sur echafaudage et risques de chute.

### Regle SST N15 - On The Job Stop, Reflechir et Agir en Securite

Source: `documents_sonasid/4_SAS006 Règle SST N°15 On The Job Stop Réfléchir et Agir en Sécurité Validé par le CSC V 22 avril 2014.pdf`
Mots-cles: stop, reflechir, agir, pause securite, analyse avant action, comportement.
Usage AMANE: a utiliser pour encourager l'arret de l'activite en cas de doute ou danger.

### Regle SST N16 - Produits dangereux

Source: `documents_sonasid/2_SAS006 Règle SST N°16 Utilisation des produits Dangereux validée par le CSC 11 juin 2014.pdf`
Mots-cles: produit dangereux, produits dangereux, chimique, chimiques, FDS, stockage, exposition, fuite, deversement, deversements, manipulation produit dangereux.
Usage AMANE: a utiliser pour risques chimiques, deversements, stockage et manipulation de produits dangereux.

### Regle SST N17 - Repli de chantier

Source: `documents_sonasid/3_SAS006 Règle SST N°17 Repli de chantier.pdf`
Mots-cles: repli, chantier, rangement, fin travaux, proprete, evacuation materiel.
Usage AMANE: a utiliser pour fin d'intervention, ordre, proprete et retrait des moyens temporaires.

### Regle SST N18 - Echelles portables

Source: `documents_sonasid/SAS006 Règle SST N°18 Utilisation échelles portables.pdf`
Mots-cles: echelle, portable, chute, appui, stabilite, acces temporaire.
Usage AMANE: a utiliser pour risques lies a l'utilisation d'echelles.

### Regle SST N19 - Circulation des engins

Source: `documents_sonasid/SAS006 Règle SST N°19 Circulation des Engins.pdf`
Mots-cles: circulation, engin, pieton, voie, croisement, priorite, collision.
Usage AMANE: a utiliser pour interaction engins-pietons et circulation interne.

### Regle SST N20 - Chargement et dechargement hors bennage

Source: `documents_sonasid/SAS006 Règle SST N°20 chargement et déchargement hors bennage.pdf`
Mots-cles: chargement, dechargement, camion, arrimage, chute de charge, manutention.
Usage AMANE: a utiliser pour operations logistiques et manipulation de charges.

### Regle SST N21 - Outillage a main

Source: `documents_sonasid/2_Règle N21 Outillage à main validé CSC VF.doc`
Mots-cles: outillage, outil a main, marteau, cle, meuleuse, outil defectueux, blessure.
Usage AMANE: document source conserve; extraction automatique du texte non active pour le format Word `.doc`.

### Regle SST N22 - Gestion des shunts JORF

Source: `documents_sonasid/SAS006 Règle SST N°22 Gestion des shunt JORF.pdf`
Mots-cles: shunt, securite machine, protection, by-pass, interverrouillage, JORF.
Usage AMANE: a utiliser pour les protections neutralisees ou dispositifs de securite contournes.

### Regle SST N23 - 5S Site vraiment propre

Source: `documents_sonasid/SAS006 Règle SST N°23 5S Site Vraiment Propre TRN.pdf`
Mots-cles: 5S, proprete, rangement, ordre, zone propre, dechet, obstacle, glissade.
Usage AMANE: a utiliser pour anomalies d'ordre, proprete, obstacles et risques de glissade.

### Regle SST N25 - Utilisation pont roulant

Source: `documents_sonasid/2_SA006 Règle N°25 Utilisation Pont roulant V CSC.pdf`
Mots-cles: pont roulant, levage, commande, charge, crochet, deplacement, manoeuvre.
Usage AMANE: a utiliser pour operations de pont roulant avec charge.

### Regle SST N26 - Utilisation pont roulant a vide

Source: `documents_sonasid/2_SA006 Règle N°26 Utilisation Pont Roulant à vide        .pdf`
Mots-cles: pont roulant a vide, crochet vide, deplacement, commande, circulation.
Usage AMANE: a utiliser pour pont roulant sans charge et risques de collision ou mauvaise manoeuvre.

### Hierarchie de controle RCSC 17 et 18

Source: `documents_sonasid/Règle Hièrarchie de controle RCSC 17 & 18.pdf`
Mots-cles: hierarchie de controle, elimination, substitution, protection collective, protection individuelle, prevention.
Usage AMANE: a utiliser pour recommander les actions de maitrise du risque dans le bon ordre.

### Message securite - Regle SST audit terrain

Source: `documents_sonasid/Message sécurité Règle SST audit terrain.pdf`
Mots-cles: audit terrain, observation, message securite, verification, comportement, conformite.
Usage AMANE: a utiliser pour orienter les controles terrain et observations HSE.

