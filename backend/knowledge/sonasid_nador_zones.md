# Zones SONASID Nador - referentiel AMANE AI

Ce fichier alimente le RAG AMANE AI pour maitriser les zones du site SONASID Nador. Les donnees viennent des plans fournis: vue generale du complexe siderurgique et vue detaillee du train a fil a deux veines / Rod and Bar Rolling Mill Complex.

Consigne assistant: quand l'utilisateur cite une zone, AMANE doit reformuler le nom normalise, demander l'emplacement exact si necessaire, identifier les energies possibles, puis associer les regles SST pertinentes. Pour la consignation, AMANE doit appliquer le guide `sonasid_consignation_isolation.md`.

## Vue generale du complexe SONASID Nador

### Zone 1 - Bureau de pont-bascule et loge de garde

- Site: SONASID Nador
- Nom officiel: Bureau de pont-bascule / Loge de garde
- Anglais plan: Weighbridge and gate house
- Equipements principaux: pont-bascule, poste de garde, entree site, controle acces camions
- Risques typiques: circulation camions, collision pieton-engin, chute de plain-pied, non respect des voies
- Energies possibles: mecanique, gravite
- Regles SST associees: N1 EPI, N7 Conduite et engins, N19 Circulation des engins, N2 Balisage
- Mots prononces possibles: pont bascule, bascule, loge de garde, entree, portail, gate house, weighbridge, lbab, gardiennage
- Consignes AMANE: demander si le risque concerne un camion, un pieton, l'acces au site ou la circulation.

### Zone 2 - Station service et garage

- Site: SONASID Nador
- Nom officiel: Station service et garage
- Anglais plan: Station service and garage
- Equipements principaux: station carburant, garage, vehicules, engins, maintenance mobile
- Risques typiques: incendie, fuite carburant, glissade, circulation engins, intervention mecanique
- Energies possibles: chimique, mecanique, electrique, hydraulique, pneumatique
- Regles SST associees: N1 EPI, N7 Conduite et engins, N9 Consignation, N16 Produits dangereux, N19 Circulation des engins
- Mots prononces possibles: station service, garage, carburant, gasoil, fuel, pompe, vehicule, engin
- Consignes AMANE: demander s'il y a fuite, odeur carburant, flamme, intervention en cours ou vehicule en mouvement.

### Zone 3 - Parachevement

- Site: SONASID Nador
- Nom officiel: Parachevement
- Anglais plan: Finishing equipment building
- Equipements principaux: equipements de finition, machines de coupe, evacuation produit, zones de controle
- Risques typiques: happement, coupure, ecrasement, bruit, pieces en mouvement
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N13 Manutention manuelle
- Mots prononces possibles: parachevement, finition, finishing, zone finition, equipement finition
- Consignes AMANE: demander la machine concernee, si elle est en marche, et si une consignation est necessaire.

### Zone 4 - Stockage couronnes

- Site: SONASID Nador
- Nom officiel: Stockage couronnes
- Anglais plan: Coil storage
- Equipements principaux: couronnes, zones de stockage, manutention, pont roulant ou engins selon operation
- Risques typiques: chute de couronne, ecrasement, manutention, collision engin-pieton, arrimage insuffisant
- Energies possibles: mecanique, gravite, electrique
- Regles SST associees: N1 EPI, N3 Charge suspendue, N7 Conduite et engins, N11 Elinguage, N19 Circulation des engins, N20 Chargement/dechargement
- Mots prononces possibles: stockage couronnes, coil storage, couronnes, coil, stock couronne
- Consignes AMANE: demander si la couronne est instable, suspendue, en manutention ou en zone pietonne.

### Zone 5 - Batiment du laminoir

- Site: SONASID Nador
- Nom officiel: Batiment du laminoir
- Anglais plan: Mill building
- Equipements principaux: train de laminage, four de rechauffage, cages, cisailles, convoyeurs, pupitre, bobinoirs
- Risques typiques: metal chaud, happement, ecrasement, bruit, brulure, projection, redemarrage machine
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, vapeur, thermique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N8 Travaux en hauteur, N9 Consignation, N10 Chalumeau/lance oxygene, N11 Elinguage, N25 Pont roulant, N26 Pont roulant a vide
- Mots prononces possibles: laminoir, laminoire, mill, train a fil, train a deux veines, rolling mill
- Consignes AMANE: demander le numero de zone du laminoir ou l'equipement exact: four, cage, cisaille, stelmor, bobinoir, compacteur.

### Zone 6 - Atelier des cylindres et magasins

- Site: SONASID Nador
- Nom officiel: Atelier des cylindres et magasins
- Anglais plan: Roll shop and stores
- Equipements principaux: cylindres, magasin, outillage, manutention, stockage pieces
- Risques typiques: ecrasement, manutention lourde, chute d'objet, outil defectueux
- Energies possibles: mecanique, electrique, hydraulique, gravite
- Regles SST associees: N1 EPI, N11 Elinguage, N13 Manutention manuelle, N21 Outillage a main, N20 Chargement/dechargement
- Mots prononces possibles: atelier cylindres, roll shop, magasin, stores, cylindres, rouleaux
- Consignes AMANE: demander si une piece est suspendue, manutentionnee ou stockee de maniere instable.

### Zone 7 - Salle de commande electrique

- Site: SONASID Nador
- Nom officiel: Salle de commande electrique
- Anglais plan: Electrical control room
- Equipements principaux: armoires electriques, commande, controle, automatismes, tableaux electriques
- Risques typiques: electrocution, arc electrique, incendie electrique, consignation incomplete
- Energies possibles: electrique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir, N22 Gestion des shunts
- Mots prononces possibles: salle electrique, salle de commande, armoire, tableau, electric room, control room
- Consignes AMANE: rappeler qu'un arret d'urgence ou asservissement n'est pas une consignation; demander si test absence tension fait.

### Zone 8 - Traitement d'eau pour laminoir

- Site: SONASID Nador
- Nom officiel: Traitement d'eau pour laminoir
- Anglais plan: Mill water treatment
- Equipements principaux: pompes, bassins, circuits eau, filtres, vannes, tuyauterie
- Risques typiques: glissade, pression, noyade, produit chimique, electricite pres de l'eau
- Energies possibles: electrique, mecanique, hydraulique, chimique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N16 Produits dangereux, N23 5S
- Mots prononces possibles: traitement eau laminoir, water treatment, pompe eau, bassin, filtre
- Consignes AMANE: demander s'il y a fuite, sol glissant, produit chimique ou intervention sur pompe/vanne.

### Zone 9 - Traitement d'eau brute

- Site: SONASID Nador
- Nom officiel: Traitement d'eau brute
- Anglais plan: Raw water treatment
- Equipements principaux: reservoir eau brute, pompes, filtres, tuyauterie, vannes
- Risques typiques: glissade, chute, pression, chimique, intervention electrique
- Energies possibles: electrique, hydraulique, chimique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N16 Produits dangereux, N23 5S
- Mots prononces possibles: eau brute, traitement eau brute, raw water, pompe, reservoir
- Consignes AMANE: demander le type d'intervention et si la pression est purgee avant travaux.

### Zone 10 - Reservoir

- Site: SONASID Nador
- Nom officiel: Reservoir
- Anglais plan: Reservoir
- Equipements principaux: reservoir, acces, tuyauteries, vannes
- Risques typiques: chute de hauteur, chute dans bassin, espace confine possible, pression, glissade
- Energies possibles: hydraulique, gravite, chimique
- Regles SST associees: N1 EPI, N2 Balisage, N8 Travaux en hauteur, N9 Consignation, N18 Echelles portables
- Mots prononces possibles: reservoir, tank, bassin, cuve
- Consignes AMANE: demander si intervention en hauteur, acces echelle ou risque de chute dans le reservoir.

### Zone 11 - Stockage du fuel lourd

- Site: SONASID Nador
- Nom officiel: Stockage du fuel lourd
- Anglais plan: Oil storage
- Equipements principaux: cuves fuel, pompes, tuyauteries, retention, vannes
- Risques typiques: incendie, pollution, fuite, glissade, brulure, produit dangereux
- Energies possibles: chimique, thermique, electrique, hydraulique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N16 Produits dangereux, N23 5S
- Mots prononces possibles: fuel lourd, oil storage, stockage fuel, gasoil, cuve fuel, fuite fuel
- Consignes AMANE: demander s'il y a fuite, odeur, source chaude, flamme, retention ou pollution.

### Zone 12 - Parc de stockage a billettes

- Site: SONASID Nador
- Nom officiel: Parc de stockage a billettes
- Anglais plan: Billet stockyard
- Equipements principaux: billettes, parc de stockage, manutention, pont roulant ou engins
- Risques typiques: chute de billettes, ecrasement, charge suspendue, circulation engins
- Energies possibles: mecanique, gravite, electrique
- Regles SST associees: N1 EPI, N3 Charge suspendue, N7 Conduite et engins, N11 Elinguage, N19 Circulation des engins, N20 Chargement/dechargement
- Mots prononces possibles: parc billettes, stockage billettes, billet stockyard, billettes, stock
- Consignes AMANE: demander si les billettes sont stables, en manutention, chargees ou dechargees.

### Zone 13 - Bureaux

- Site: SONASID Nador
- Nom officiel: Bureaux
- Anglais plan: Office buildings
- Equipements principaux: bureaux administratifs, circulation pietonne, locaux sociaux
- Risques typiques: chute de plain-pied, incendie, evacuation, ergonomie
- Energies possibles: electrique
- Regles SST associees: N1 EPI selon acces industriel, N2 Balisage, N23 5S
- Mots prononces possibles: bureaux, office, administratif
- Consignes AMANE: demander si le signalement concerne bureau, acces pieton, evacuation ou electricite.

### Zone 14 - Centre de formation

- Site: SONASID Nador
- Nom officiel: Centre de formation
- Anglais plan: Training school
- Equipements principaux: salles formation, ateliers pedagogiques, zones d'exercice
- Risques typiques: chute, electricite basse tension, incendie, exercice pratique mal encadre
- Energies possibles: electrique, mecanique selon atelier
- Regles SST associees: N1 EPI, N2 Balisage, N15 Stop Reflechir Agir, N23 5S
- Mots prononces possibles: centre formation, training school, formation
- Consignes AMANE: demander si la situation est en exercice pratique ou dans une salle.

### Zone 15 - Batiment des services

- Site: SONASID Nador
- Nom officiel: Batiment des services
- Anglais plan: Services building
- Equipements principaux: locaux services, maintenance support, circulation interne
- Risques typiques: chute de plain-pied, electricite, incendie, manutention legere
- Energies possibles: electrique, mecanique
- Regles SST associees: N1 EPI, N2 Balisage, N13 Manutention manuelle, N23 5S
- Mots prononces possibles: batiment services, services building, service
- Consignes AMANE: demander le service exact et si une intervention technique est en cours.

### Zone 16 - Sous-station principale

- Site: SONASID Nador
- Nom officiel: Sous-station principale
- Anglais plan: Main sub-station
- Equipements principaux: transformateurs, cellules electriques, alimentation principale, protections electriques
- Risques typiques: electrocution, arc electrique, incendie, consignation critique, acces interdit
- Energies possibles: electrique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir, N22 Gestion des shunts
- Mots prononces possibles: sous station, substation, poste principal, transformateur, cellule electrique
- Consignes AMANE: rappeler validation obligatoire par personnel habilite; demander si la zone est balisee et si l'acces est autorise.

## Detail du laminoir - Train a fil a deux veines

### Laminoir 1 - Stockage et manutention de billettes

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Stockage et manutention de billettes
- Anglais plan: Billet handling and storage
- Equipements principaux: billettes, zones de stockage, moyens de levage/manutention
- Risques typiques: chute de billettes, ecrasement, charge suspendue, collision engin-pieton
- Energies possibles: mecanique, gravite, electrique
- Regles SST associees: N1 EPI, N3 Charge suspendue, N7 Conduite et engins, N11 Elinguage, N20 Chargement/dechargement
- Mots prononces possibles: billettes, stockage billettes, manutention billettes, billet handling, parc billettes
- Consignes AMANE: demander si la billette est au sol, suspendue, instable ou en deplacement.

### Laminoir 2 - Four de rechauffage

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Four de rechauffage
- Anglais plan: Reheat furnace
- Equipements principaux: four, bruleurs, convoyage entree/sortie, zone chaude
- Risques typiques: brulure, incendie, gaz, chaleur, metal chaud, intervention point chaud
- Energies possibles: thermique, chimique, gaz, electrique, mecanique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N10 Chalumeau/lance oxygene, N16 Produits dangereux
- Mots prononces possibles: four, four de rechauffage, reheat furnace, zone chaude, furnace
- Consignes AMANE: demander s'il y a flamme, gaz, metal chaud, intervention ou presence de personne exposee.

### Laminoir 3 - Cisaille pour billettes

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Cisaille pour billettes
- Anglais plan: Billet shear
- Equipements principaux: cisaille, ameneur de billettes, protections machine
- Risques typiques: coupure, ecrasement, happement, redemarrage intempestif
- Energies possibles: electrique, mecanique, hydraulique, pneumatique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: cisaille, cisaille billettes, billet shear, cisailles
- Consignes AMANE: si intervention proche de la cisaille, demander si consignation et absence d'energie sont verifiees.

### Laminoir 4 - Cages degrossisseuses

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Cages degrossisseuses
- Anglais plan: Roughing stands
- Equipements principaux: cages, cylindres, entrainements, guides, protections
- Risques typiques: happement, ecrasement, projection, bruit, metal chaud
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N13 Manutention manuelle, N21 Outillage a main
- Mots prononces possibles: cages degrossisseuses, roughing stands, cage, degrossissage
- Consignes AMANE: demander si machine en marche, intervention outil, changement cylindre ou bourrage.

### Laminoir 5 - Cisailles a ebouter

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Cisailles a ebouter
- Anglais plan: Crop shears
- Equipements principaux: crop shear, guides, convoyage, protections
- Risques typiques: coupure, projection, ecrasement, redemarrage
- Energies possibles: electrique, mecanique, hydraulique, pneumatique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: cisaille a ebouter, crop shear, eboutage, cisailles
- Consignes AMANE: demander si l'acces est ouvert, si l'energie est isolee et si la zone est balisee.

### Laminoir 6 - Cages intermediaires

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Cages intermediaires
- Anglais plan: Intermediate stands
- Equipements principaux: cages, cylindres, guides, entrainements
- Risques typiques: happement, ecrasement, projection, bruit, metal chaud
- Energies possibles: electrique, mecanique, hydraulique, pneumatique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N13 Manutention manuelle
- Mots prononces possibles: cages intermediaires, intermediate stands, cage intermediaire
- Consignes AMANE: demander s'il s'agit d'un bourrage, changement de guide/cylindre ou inspection.

### Laminoir 7 - Pupitre de commande principal du laminoir

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Pupitre de commande principal du laminoir
- Anglais plan: Main mill control pulpit
- Equipements principaux: pupitre commande, supervision, commandes operateur, communication ligne
- Risques typiques: erreur de manoeuvre, redemarrage machine, mauvaise communication, shunt ou asservissement
- Energies possibles: electrique, commande/automatisme
- Regles SST associees: N4 Geste de commandement, N5 Telephone cellulaire, N9 Consignation, N15 Stop Reflechir Agir, N22 Gestion des shunts
- Mots prononces possibles: pupitre, salle commande laminoir, main pulpit, commande principale
- Consignes AMANE: demander si une manoeuvre est en cours et si tous les intervenants sont informes.

### Laminoir 8 - Presse a loups / cobble bundle

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Presse a loups
- Anglais plan: Cobble bundle
- Equipements principaux: presse, zone de cobble/loup, paquet de barres, evacuation incident
- Risques typiques: metal chaud, ecrasement, projection, intervention apres incident de laminage
- Energies possibles: electrique, mecanique, hydraulique, thermique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N10 Point chaud, N15 Stop Reflechir Agir
- Mots prononces possibles: presse a loups, loup, cobble, cobble bundle, paquet cobble
- Consignes AMANE: demander si le loup est chaud, si la ligne est arretee et si la zone est interdite.

### Laminoir 9 - Trains finisseurs No Twist

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Trains finisseurs No Twist
- Anglais plan: No-twist finishing mills
- Equipements principaux: trains finisseurs, blocs no twist, guides, refroidissement
- Risques typiques: happement, projection, bruit, metal chaud, intervention rapide
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, thermique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: no twist, train finisseur, finishing mill, finisseur
- Consignes AMANE: demander si l'intervention concerne guide, cylindre, bourrage ou inspection ligne.

### Laminoir 10 - Boite a eau

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Boite a eau
- Anglais plan: Water box
- Equipements principaux: boite a eau, refroidissement, tuyauterie, pression, vannes
- Risques typiques: pression, fuite eau, glissade, brulure vapeur, electricite pres eau
- Energies possibles: hydraulique, electrique, thermique, pneumatique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N16 Produits dangereux si traitement, N23 5S
- Mots prononces possibles: boite a eau, water box, refroidissement, fuite eau
- Consignes AMANE: demander si fuite, pression, sol glissant ou intervention sur vanne/pompe.

### Laminoir 11 - Aiguille pour bobinoir

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Aiguille pour bobinoir
- Anglais plan: Switch for pouring reel
- Equipements principaux: aiguille, aiguillage, commande bobinoir, guides produit
- Risques typiques: happement, ecrasement, projection, mauvaise orientation produit
- Energies possibles: electrique, mecanique, pneumatique, hydraulique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: aiguille, aiguille bobinoir, switch, pouring reel switch
- Consignes AMANE: demander si le produit est en mouvement et si l'aiguillage est bloque ou mal positionne.

### Laminoir 12 - Bobinoirs

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Bobinoirs
- Anglais plan: Pouring reels
- Equipements principaux: bobinoirs, tambours, entrainements, guides, evacuation couronnes
- Risques typiques: happement, ecrasement, enroulement, metal chaud, redemarrage
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, thermique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: bobinoir, bobinoirs, pouring reel, bobine
- Consignes AMANE: demander si le bobinoir est en rotation, bloque, en intervention ou en nettoyage.

### Laminoir 13 - Formeurs de spires

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Formeurs de spires
- Anglais plan: Laying heads
- Equipements principaux: laying head, formeur spires, guide fil, tete rotative
- Risques typiques: rotation rapide, projection, happement, metal chaud
- Energies possibles: electrique, mecanique, pneumatique, thermique
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N15 Stop Reflechir Agir
- Mots prononces possibles: formeur de spires, laying head, tete de spires, spires
- Consignes AMANE: demander si la tete est en rotation ou si une intervention est prevue.

### Laminoir 14 - Convoyeurs Stelmore

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Convoyeurs Stelmore
- Anglais plan: Stelmor conveyors
- Equipements principaux: convoyeurs Stelmor, ventilateurs/refroidissement, rouleaux, chaines
- Risques typiques: happement, ecrasement, chute de plain-pied, bruit, redemarrage convoyeur
- Energies possibles: electrique, mecanique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N23 5S
- Mots prononces possibles: stelmor, stelmore, convoyeur stelmor, tapis stelmor, convoyeur
- Consignes AMANE: demander si le convoyeur est en marche, bloque, en nettoyage ou en intervention.

### Laminoir 15 - Formeurs de couronnes

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Formeurs de couronnes
- Anglais plan: Reform tubs
- Equipements principaux: formeurs, reform tubs, zone couronnes, evacuation produit
- Risques typiques: ecrasement, happement, chute couronne, metal chaud
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N20 Chargement/dechargement
- Mots prononces possibles: formeur couronne, reform tub, couronne, tub
- Consignes AMANE: demander si la couronne est instable, chaude ou en cours de transfert.

### Laminoir 16 - Chariot collecteur C hook

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Chariot collecteur C hook
- Anglais plan: C hook carrier
- Equipements principaux: chariot, crochet C, transfert couronnes, rail/chemin de roulement
- Risques typiques: ecrasement, collision, charge suspendue, chute couronne, zone interdite
- Energies possibles: electrique, mecanique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N3 Charge suspendue, N11 Elinguage, N19 Circulation des engins
- Mots prononces possibles: c hook, crochet C, chariot collecteur, carrier, chariot couronne
- Consignes AMANE: demander si une personne est proche du chariot ou sous/près de la charge.

### Laminoir 17 - Convoyeur de couronnes

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Convoyeur de couronnes
- Anglais plan: Coil handling system
- Equipements principaux: convoyeur couronnes, transfert, rouleaux, chaines, guides
- Risques typiques: happement, ecrasement, chute couronne, redemarrage
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N20 Chargement/dechargement
- Mots prononces possibles: convoyeur couronnes, coil handling, transfert couronnes, tapis couronnes
- Consignes AMANE: demander si le convoyeur est bloque, en mouvement, ou si quelqu'un intervient dessus.

### Laminoir 18 - Compacteuses a couronnes et machines a ligaturer

- Site: SONASID Nador
- Atelier: Laminoir
- Nom officiel: Compacteuses a couronnes et machines a ligaturer
- Anglais plan: Coil compactors and tying machines
- Equipements principaux: compacteuse, machine a ligaturer, cerclage, presse, convoyage sortie
- Risques typiques: ecrasement, pincement, fouettement ligature, redemarrage machine, chute couronne
- Energies possibles: electrique, mecanique, hydraulique, pneumatique, gravite
- Regles SST associees: N1 EPI, N2 Balisage, N9 Consignation, N13 Manutention manuelle, N20 Chargement/dechargement
- Mots prononces possibles: compacteuse, compacteur, ligatureuse, machine a ligaturer, tying machine, coil compactor
- Consignes AMANE: demander si une intervention se fait dans la zone de compactage ou ligature; rappeler consignation obligatoire avant acces machine.