"""
Base de données des 18 équipes de Ligue 1 2025-2026
Contient les effectifs, formations préférées, et informations des coachs.
"""

LIGUE1_TEAMS = {
    "psg": {
        "full_name": "Paris Saint-Germain",
        "short_name": "PSG",
        "city": "Paris",
        "stadium": "Parc des Princes",
        "coach": "Luis Enrique",
        "api_football_id": 85,
        "preferred_formations": ["4-3-3", "3-4-3"],
        "style": "Possession dominante, pressing haut, jeu de position",
        "squad": {
            "GK": [
                {"name": "Lucas Chevalier", "number": 1, "rating": 84, "age": 22},
                {"name": "Matvey Safonov", "number": 99, "rating": 79, "age": 26},
            ],
            "DEF": [
                {"name": "Achraf Hakimi", "number": 2, "rating": 87, "position": "DD", "age": 27},
                {"name": "Marquinhos", "number": 5, "rating": 86, "position": "DC", "age": 32},
                {"name": "Lucas Hernandez", "number": 21, "rating": 83, "position": "DC", "age": 30},
                {"name": "Nuno Mendes", "number": 25, "rating": 84, "position": "DG", "age": 24},
                {"name": "Willian Pacho", "number": 51, "rating": 83, "position": "DC", "age": 23},
                {"name": "Illia Zabarnyi", "number": 4, "rating": 82, "position": "DC", "age": 23},
            ],
            "MID": [
                {"name": "Vitinha", "number": 17, "rating": 87, "position": "MC", "age": 26},
                {"name": "Warren Zaïre-Emery", "number": 33, "rating": 84, "position": "MC", "age": 20},
                {"name": "Fabian Ruiz", "number": 8, "rating": 83, "position": "MC", "age": 30},
                {"name": "João Neves", "number": 87, "rating": 84, "position": "MC", "age": 21},
                {"name": "Lee Kang-in", "number": 19, "rating": 81, "position": "MOC", "age": 25},
                {"name": "Senny Mayulu", "number": 18, "rating": 76, "position": "MOC", "age": 19},
            ],
            "FWD": [
                {"name": "Ousmane Dembélé", "number": 10, "rating": 86, "position": "AD", "age": 29},
                {"name": "Bradley Barcola", "number": 29, "rating": 84, "position": "AG", "age": 22},
                {"name": "Khvicha Kvaratskhelia", "number": 7, "rating": 85, "position": "AG", "age": 25},
                {"name": "Gonçalo Ramos", "number": 9, "rating": 82, "position": "BU", "age": 25},
                {"name": "Désiré Doué", "number": 14, "rating": 80, "position": "AD", "age": 21},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Chevalier",
                "Hakimi", "Marquinhos", "Pacho", "Nuno Mendes",
                "Zaïre-Emery", "Vitinha", "João Neves",
                "Dembélé", "Gonçalo Ramos", "Barcola"
            ]
        }
    },
    "om": {
        "full_name": "Olympique de Marseille",
        "short_name": "OM",
        "city": "Marseille",
        "stadium": "Stade Vélodrome",
        "coach": "Habib Beye",
        "api_football_id": 81,
        "preferred_formations": ["3-4-2-1", "4-2-3-1"],
        "style": "Pressing intense, jeu de transition, intensité physique",
        "squad": {
            "GK": [
                {"name": "Geronimo Rulli", "number": 1, "rating": 82, "age": 32},
                {"name": "Jeffrey de Lange", "number": 16, "rating": 74, "age": 25},
            ],
            "DEF": [
                {"name": "Benjamin Pavard", "number": 2, "rating": 82, "position": "DD", "age": 30},
                {"name": "Leonardo Balerdi", "number": 5, "rating": 80, "position": "DC", "age": 26},
                {"name": "Lilian Brassier", "number": 3, "rating": 78, "position": "DC", "age": 25},
                {"name": "Ulisses Garcia", "number": 21, "rating": 75, "position": "DG", "age": 28},
            ],
            "MID": [
                {"name": "Pierre-Emile Højbjerg", "number": 23, "rating": 82, "position": "MC", "age": 30},
                {"name": "Ismaël Bennacer", "number": 6, "rating": 80, "position": "MC", "age": 28},
                {"name": "Quinten Timber", "number": 8, "rating": 78, "position": "MC", "age": 24},
                {"name": "Bilal Nadir", "number": 20, "rating": 74, "position": "MOC", "age": 19},
            ],
            "FWD": [
                {"name": "Mason Greenwood", "number": 11, "rating": 83, "position": "AD", "age": 24},
                {"name": "Pierre-Emerick Aubameyang", "number": 17, "rating": 80, "position": "BU", "age": 36},
                {"name": "Neal Maupay", "number": 9, "rating": 77, "position": "BU", "age": 30},
                {"name": "Amine Gouiri", "number": 7, "rating": 79, "position": "AG", "age": 26},
                {"name": "Ethan Nwaneri", "number": 18, "rating": 76, "position": "MOC", "age": 18},
                {"name": "Igor Paixão", "number": 10, "rating": 79, "position": "AG", "age": 25},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Rulli",
                "Pavard", "Balerdi", "Brassier", "Garcia",
                "Højbjerg", "Bennacer",
                "Greenwood", "Gouiri", "Paixão",
                "Aubameyang"
            ]
        }
    },
    "monaco": {
        "full_name": "AS Monaco",
        "short_name": "Monaco",
        "city": "Monaco",
        "stadium": "Stade Louis-II",
        "coach": "Sébastien Pocognoli",
        "api_football_id": 91,
        "preferred_formations": ["4-2-3-1", "4-4-2"],
        "style": "Contre-attaque rapide, transitions, intensité physique",
        "squad": {
            "GK": [
                {"name": "Philipp Köhn", "number": 1, "rating": 79, "age": 26},
                {"name": "Radoslaw Majecki", "number": 33, "rating": 77, "age": 25},
            ],
            "DEF": [
                {"name": "Vanderson", "number": 2, "rating": 80, "position": "DD", "age": 24},
                {"name": "Mohammed Salisu", "number": 22, "rating": 79, "position": "DC", "age": 26},
                {"name": "Thilo Kehrer", "number": 4, "rating": 78, "position": "DC", "age": 29},
                {"name": "Caio Henrique", "number": 12, "rating": 79, "position": "DG", "age": 27},
                {"name": "Wilfried Singo", "number": 21, "rating": 78, "position": "DD", "age": 25},
            ],
            "MID": [
                {"name": "Denis Zakaria", "number": 8, "rating": 81, "position": "MC", "age": 29},
                {"name": "Youssouf Fofana", "number": 6, "rating": 80, "position": "MC", "age": 26},
                {"name": "Aleksandr Golovin", "number": 17, "rating": 80, "position": "MOC", "age": 30},
                {"name": "Lamine Camara", "number": 20, "rating": 78, "position": "MC", "age": 21},
                {"name": "Maghnes Akliouche", "number": 10, "rating": 79, "position": "MOC", "age": 23},
            ],
            "FWD": [
                {"name": "Breel Embolo", "number": 36, "rating": 78, "position": "BU", "age": 29},
                {"name": "Folarin Balogun", "number": 9, "rating": 79, "position": "BU", "age": 25},
                {"name": "Eliesse Ben Seghir", "number": 11, "rating": 78, "position": "AG", "age": 20},
                {"name": "Takumi Minamino", "number": 15, "rating": 77, "position": "AD", "age": 31},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Köhn",
                "Vanderson", "Salisu", "Kehrer", "Caio Henrique",
                "Zakaria", "Camara",
                "Akliouche", "Golovin", "Ben Seghir",
                "Embolo"
            ]
        }
    },
    "lille": {
        "full_name": "LOSC Lille",
        "short_name": "Lille",
        "city": "Lille",
        "stadium": "Stade Pierre-Mauroy",
        "coach": "Bruno Génésio",
        "api_football_id": 79,
        "preferred_formations": ["4-2-3-1", "4-3-3"],
        "style": "Pressing haut, transitions rapides, solidité défensive",
        "squad": {
            "GK": [
                {"name": "Lucas Chevalier", "number": 1, "rating": 82, "age": 22},
            ],
            "DEF": [
                {"name": "Bafodé Diakité", "number": 5, "rating": 78, "position": "DD", "age": 24},
                {"name": "Alexsandro", "number": 4, "rating": 77, "position": "DC", "age": 24},
                {"name": "Thomas Meunier", "number": 2, "rating": 77, "position": "DD", "age": 35},
                {"name": "Aïssa Mandi", "number": 3, "rating": 77, "position": "DC", "age": 33},
                {"name": "Gabriel Gudmundsson", "number": 13, "rating": 76, "position": "DG", "age": 26},
                {"name": "Tiago Santos", "number": 15, "rating": 76, "position": "DD", "age": 23},
            ],
            "MID": [
                {"name": "Benjamin André", "number": 21, "rating": 79, "position": "MC", "age": 34},
                {"name": "Angel Gomes", "number": 8, "rating": 79, "position": "MOC", "age": 25},
                {"name": "Rémy Cabella", "number": 7, "rating": 76, "position": "MOC", "age": 36},
                {"name": "Ngal'ayel Mukau", "number": 18, "rating": 75, "position": "MC", "age": 20},
            ],
            "FWD": [
                {"name": "Jonathan David", "number": 9, "rating": 83, "position": "BU", "age": 26},
                {"name": "Edon Zhegrova", "number": 47, "rating": 80, "position": "AD", "age": 26},
                {"name": "Mohamed Bayo", "number": 10, "rating": 76, "position": "BU", "age": 26},
                {"name": "Hakon Arnar Haraldsson", "number": 11, "rating": 75, "position": "AG", "age": 23},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Chevalier",
                "Tiago Santos", "Diakité", "Alexsandro", "Gudmundsson",
                "André", "Mukau",
                "Zhegrova", "Angel Gomes", "Haraldsson",
                "David"
            ]
        }
    },
    "lens": {
        "full_name": "RC Lens",
        "short_name": "Lens",
        "city": "Lens",
        "stadium": "Stade Bollaert-Delelis",
        "coach": "Pierre Sage",
        "api_football_id": 116,
        "preferred_formations": ["3-4-1-2", "3-5-2"],
        "style": "Intensité physique, pressing, jeu direct et vertical",
        "squad": {
            "GK": [
                {"name": "Brice Samba", "number": 1, "rating": 82, "age": 31},
            ],
            "DEF": [
                {"name": "Kevin Danso", "number": 4, "rating": 80, "position": "DC", "age": 26},
                {"name": "Abdukodir Khusanov", "number": 5, "rating": 78, "position": "DC", "age": 21},
                {"name": "Facundo Medina", "number": 3, "rating": 78, "position": "DC", "age": 26},
                {"name": "Deiver Machado", "number": 22, "rating": 76, "position": "DG", "age": 30},
                {"name": "Przemyslaw Frankowski", "number": 11, "rating": 77, "position": "DD", "age": 30},
            ],
            "MID": [
                {"name": "Andy Diouf", "number": 8, "rating": 78, "position": "MC", "age": 22},
                {"name": "Adrien Thomasson", "number": 10, "rating": 77, "position": "MOC", "age": 32},
                {"name": "Neil El Aynaoui", "number": 28, "rating": 76, "position": "MC", "age": 23},
                {"name": "Angelo Fulgini", "number": 7, "rating": 76, "position": "MOC", "age": 29},
            ],
            "FWD": [
                {"name": "Elye Wahi", "number": 9, "rating": 77, "position": "BU", "age": 22},
                {"name": "M'Bala Nzola", "number": 18, "rating": 74, "position": "BU", "age": 29},
                {"name": "Florian Sotoca", "number": 12, "rating": 75, "position": "BU", "age": 33},
            ],
        },
        "default_xi": {
            "formation": "3-4-1-2",
            "lineup": [
                "Samba",
                "Danso", "Khusanov", "Medina",
                "Frankowski", "Diouf", "El Aynaoui", "Machado",
                "Thomasson",
                "Wahi", "Sotoca"
            ]
        }
    },
    "ol": {
        "full_name": "Olympique Lyonnais",
        "short_name": "OL",
        "city": "Lyon",
        "stadium": "Groupama Stadium",
        "coach": "Pierre Sage",
        "api_football_id": 80,
        "preferred_formations": ["4-3-3", "4-2-3-1"],
        "style": "Possession offensive, construction depuis l'arrière, pressing haut",
        "squad": {
            "GK": [
                {"name": "Lucas Perri", "number": 1, "rating": 79, "age": 27},
                {"name": "Rémy Descamps", "number": 30, "rating": 73, "age": 29},
            ],
            "DEF": [
                {"name": "Clinton Mata", "number": 2, "rating": 77, "position": "DD", "age": 33},
                {"name": "Moussa Niakhaté", "number": 3, "rating": 79, "position": "DC", "age": 30},
                {"name": "Duje Caleta-Car", "number": 15, "rating": 78, "position": "DC", "age": 30},
                {"name": "Abner", "number": 6, "rating": 78, "position": "DG", "age": 26},
                {"name": "Ainsley Maitland-Niles", "number": 22, "rating": 75, "position": "DD", "age": 28},
            ],
            "MID": [
                {"name": "Corentin Tolisso", "number": 8, "rating": 79, "position": "MC", "age": 32},
                {"name": "Maxence Caqueret", "number": 7, "rating": 79, "position": "MC", "age": 26},
                {"name": "Jordan Veretout", "number": 17, "rating": 78, "position": "MC", "age": 33},
                {"name": "Orel Mangala", "number": 28, "rating": 77, "position": "MC", "age": 27},
                {"name": "Saïd Benrahma", "number": 10, "rating": 78, "position": "MOC", "age": 30},
            ],
            "FWD": [
                {"name": "Georges Mikautadze", "number": 69, "rating": 80, "position": "BU", "age": 24},
                {"name": "Malick Fofana", "number": 19, "rating": 81, "position": "AG", "age": 21},
                {"name": "Ernest Nuamah", "number": 11, "rating": 77, "position": "AD", "age": 22},
                {"name": "Gift Orban", "number": 14, "rating": 76, "position": "BU", "age": 24},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Perri",
                "Mata", "Caleta-Car", "Niakhaté", "Abner",
                "Caqueret", "Tolisso", "Benrahma",
                "Nuamah", "Mikautadze", "Fofana"
            ]
        }
    },
    "nice": {
        "full_name": "OGC Nice",
        "short_name": "Nice",
        "city": "Nice",
        "stadium": "Allianz Riviera",
        "coach": "Claude Puel",
        "api_football_id": 84,
        "preferred_formations": ["3-4-1-2", "4-3-3"],
        "style": "Solidité défensive, pressing, transitions rapides",
        "squad": {
            "GK": [
                {"name": "Marcin Bulka", "number": 1, "rating": 79, "age": 25},
            ],
            "DEF": [
                {"name": "Jean-Clair Todibo", "number": 4, "rating": 80, "position": "DC", "age": 26},
                {"name": "Dante", "number": 2, "rating": 76, "position": "DC", "age": 42},
                {"name": "Youssouf Ndayishimiye", "number": 3, "rating": 76, "position": "DC", "age": 27},
                {"name": "Melvin Bard", "number": 5, "rating": 75, "position": "DG", "age": 23},
                {"name": "Jordan Lotomba", "number": 22, "rating": 75, "position": "DD", "age": 27},
            ],
            "MID": [
                {"name": "Khéphren Thuram", "number": 8, "rating": 80, "position": "MC", "age": 24},
                {"name": "Pablo Rosario", "number": 6, "rating": 77, "position": "MC", "age": 28},
                {"name": "Sofiane Diop", "number": 10, "rating": 78, "position": "MOC", "age": 25},
                {"name": "Morgan Sanson", "number": 14, "rating": 76, "position": "MC", "age": 31},
            ],
            "FWD": [
                {"name": "Gaetan Laborde", "number": 9, "rating": 77, "position": "BU", "age": 31},
                {"name": "Jeremie Boga", "number": 7, "rating": 77, "position": "AG", "age": 29},
                {"name": "Terem Moffi", "number": 18, "rating": 76, "position": "BU", "age": 25},
            ],
        },
        "default_xi": {
            "formation": "3-4-1-2",
            "lineup": [
                "Bulka",
                "Todibo", "Dante", "Ndayishimiye",
                "Lotomba", "Thuram", "Rosario", "Bard",
                "Diop",
                "Laborde", "Boga"
            ]
        }
    },
    "rennes": {
        "full_name": "Stade Rennais FC",
        "short_name": "Rennes",
        "city": "Rennes",
        "stadium": "Roazhon Park",
        "coach": "Intérimaire (après Habib Beye)",
        "api_football_id": 94,
        "preferred_formations": ["4-3-3", "4-4-2"],
        "style": "Pressing, jeu de transition, intensité",
        "squad": {
            "GK": [
                {"name": "Steve Mandanda", "number": 1, "rating": 77, "age": 41},
            ],
            "DEF": [
                {"name": "Warmed Omari", "number": 3, "rating": 76, "position": "DC", "age": 24},
                {"name": "Christopher Wooh", "number": 4, "rating": 76, "position": "DC", "age": 25},
                {"name": "Adrien Truffert", "number": 5, "rating": 77, "position": "DG", "age": 23},
                {"name": "Lorenz Assignon", "number": 2, "rating": 76, "position": "DD", "age": 25},
            ],
            "MID": [
                {"name": "Baptiste Santamaria", "number": 6, "rating": 77, "position": "MC", "age": 31},
                {"name": "Ludovic Blas", "number": 10, "rating": 78, "position": "MOC", "age": 27},
                {"name": "Ibrahim Salah", "number": 8, "rating": 74, "position": "MC", "age": 22},
            ],
            "FWD": [
                {"name": "Arnaud Kalimuendo", "number": 9, "rating": 78, "position": "BU", "age": 24},
                {"name": "Amine Gouiri", "number": 11, "rating": 78, "position": "AG", "age": 25},
                {"name": "Désiré Doué", "number": 7, "rating": 79, "position": "AD", "age": 21},
                {"name": "Jérémy Doku", "number": 14, "rating": 79, "position": "AD", "age": 24},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Mandanda",
                "Assignon", "Wooh", "Omari", "Truffert",
                "Santamaria", "Salah", "Blas",
                "Gouiri", "Kalimuendo", "Doku"
            ]
        }
    },
    "toulouse": {
        "full_name": "Toulouse FC",
        "short_name": "Toulouse",
        "city": "Toulouse",
        "stadium": "Stadium de Toulouse",
        "coach": "Carles Martinez Novell",
        "api_football_id": 96,
        "preferred_formations": ["4-3-3", "4-2-3-1"],
        "style": "Jeu de possession, construction basse, jeu collectif",
        "squad": {
            "GK": [
                {"name": "Guillaume Restes", "number": 1, "rating": 79, "age": 20},
            ],
            "DEF": [
                {"name": "Rasmus Nicolaisen", "number": 4, "rating": 76, "position": "DC", "age": 28},
                {"name": "Anthony Rouault", "number": 3, "rating": 76, "position": "DC", "age": 24},
                {"name": "Moussa Diarra", "number": 5, "rating": 74, "position": "DC", "age": 23},
                {"name": "Kévin Keben", "number": 2, "rating": 74, "position": "DD", "age": 22},
                {"name": "Aron Donnum", "number": 22, "rating": 74, "position": "DG", "age": 26},
            ],
            "MID": [
                {"name": "Stijn Spierings", "number": 8, "rating": 76, "position": "MC", "age": 30},
                {"name": "Niklas Schmidt", "number": 10, "rating": 75, "position": "MOC", "age": 28},
                {"name": "César Music", "number": 6, "rating": 74, "position": "MC", "age": 22},
            ],
            "FWD": [
                {"name": "Thijs Dallinga", "number": 9, "rating": 76, "position": "BU", "age": 25},
                {"name": "Zakaria Aboukhlal", "number": 7, "rating": 76, "position": "AD", "age": 25},
                {"name": "Ado Onaiwu", "number": 18, "rating": 74, "position": "BU", "age": 30},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Restes",
                "Keben", "Nicolaisen", "Rouault", "Donnum",
                "Spierings", "Music", "Schmidt",
                "Aboukhlal", "Dallinga", "Onaiwu"
            ]
        }
    },
    "brest": {
        "full_name": "Stade Brestois 29",
        "short_name": "Brest",
        "city": "Brest",
        "stadium": "Stade Francis-Le Blé",
        "coach": "Eric Roy",
        "api_football_id": 106,
        "preferred_formations": ["4-3-3", "3-5-2"],
        "style": "Discipline tactique, pressing, solidité collective",
        "squad": {
            "GK": [
                {"name": "Marco Bizot", "number": 1, "rating": 78, "age": 34},
            ],
            "DEF": [
                {"name": "Brendan Chardonnet", "number": 3, "rating": 76, "position": "DC", "age": 31},
                {"name": "Julien Le Cardinal", "number": 4, "rating": 75, "position": "DC", "age": 27},
                {"name": "Bradley Locko", "number": 5, "rating": 75, "position": "DG", "age": 23},
                {"name": "Kenny Lala", "number": 2, "rating": 76, "position": "DD", "age": 33},
            ],
            "MID": [
                {"name": "Pierre Lees-Melou", "number": 8, "rating": 77, "position": "MC", "age": 33},
                {"name": "Hugo Magnetti", "number": 6, "rating": 76, "position": "MC", "age": 27},
                {"name": "Mahdi Camara", "number": 10, "rating": 77, "position": "MC", "age": 28},
            ],
            "FWD": [
                {"name": "Martin Satriano", "number": 9, "rating": 76, "position": "BU", "age": 24},
                {"name": "Kamory Doumbia", "number": 18, "rating": 75, "position": "AD", "age": 24},
                {"name": "Mama Baldé", "number": 7, "rating": 75, "position": "AG", "age": 29},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Bizot",
                "Lala", "Chardonnet", "Le Cardinal", "Locko",
                "Lees-Melou", "Magnetti", "Camara",
                "Doumbia", "Satriano", "Baldé"
            ]
        }
    },
    "strasbourg": {
        "full_name": "RC Strasbourg Alsace",
        "short_name": "Strasbourg",
        "city": "Strasbourg",
        "stadium": "Stade de la Meinau",
        "coach": "Liam Rosenior",
        "api_football_id": 95,
        "preferred_formations": ["4-2-3-1", "3-5-2"],
        "style": "Jeu offensif, pressing, mentalité offensive",
        "squad": {
            "GK": [{"name": "Matz Sels", "number": 1, "rating": 79, "age": 33}],
            "DEF": [
                {"name": "Gerzino Nyamsi", "number": 4, "rating": 75, "position": "DC", "age": 28},
                {"name": "Alexander Djiku", "number": 3, "rating": 77, "position": "DC", "age": 31},
                {"name": "Thomas Delaine", "number": 5, "rating": 75, "position": "DG", "age": 33},
                {"name": "Ronael Pierre-Gabriel", "number": 2, "rating": 74, "position": "DD", "age": 28},
            ],
            "MID": [
                {"name": "Habib Diarra", "number": 8, "rating": 76, "position": "MC", "age": 22},
                {"name": "Jean-Ricner Bellegarde", "number": 6, "rating": 76, "position": "MC", "age": 27},
                {"name": "Adrien Thomasson", "number": 10, "rating": 76, "position": "MOC", "age": 30},
            ],
            "FWD": [
                {"name": "Habib Diallo", "number": 9, "rating": 76, "position": "BU", "age": 30},
                {"name": "Emanuel Emegha", "number": 7, "rating": 75, "position": "BU", "age": 23},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Sels",
                "Pierre-Gabriel", "Djiku", "Nyamsi", "Delaine",
                "Diarra", "Bellegarde",
                "Thomasson",
                "Emegha", "Diallo", "Emegha"
            ]
        }
    },
    "nantes": {
        "full_name": "FC Nantes",
        "short_name": "Nantes",
        "city": "Nantes",
        "stadium": "Stade de la Beaujoire",
        "coach": "Vahid Halilhodžić",
        "api_football_id": 83,
        "preferred_formations": ["4-4-2", "4-2-3-1"],
        "style": "Solidité défensive, contre-attaques, jeu direct",
        "squad": {
            "GK": [{"name": "Alban Lafont", "number": 1, "rating": 78, "age": 26}],
            "DEF": [
                {"name": "Jean-Charles Castelletto", "number": 4, "rating": 76, "position": "DC", "age": 31},
                {"name": "Nicolas Pallois", "number": 3, "rating": 75, "position": "DC", "age": 38},
                {"name": "Fabien Centonze", "number": 2, "rating": 75, "position": "DD", "age": 30},
                {"name": "Quentin Merlin", "number": 5, "rating": 75, "position": "DG", "age": 23},
            ],
            "MID": [
                {"name": "Pedro Chirivella", "number": 6, "rating": 76, "position": "MC", "age": 29},
                {"name": "Florent Mollet", "number": 10, "rating": 76, "position": "MOC", "age": 32},
                {"name": "Moussa Sissoko", "number": 8, "rating": 75, "position": "MC", "age": 36},
            ],
            "FWD": [
                {"name": "Mostafa Mohamed", "number": 9, "rating": 76, "position": "BU", "age": 27},
                {"name": "Moses Simon", "number": 7, "rating": 77, "position": "AG", "age": 29},
                {"name": "Ignatius Ganago", "number": 11, "rating": 74, "position": "BU", "age": 26},
            ],
        },
        "default_xi": {
            "formation": "4-4-2",
            "lineup": [
                "Lafont",
                "Centonze", "Castelletto", "Pallois", "Merlin",
                "Mollet", "Chirivella", "Sissoko", "Simon",
                "Mohamed", "Ganago"
            ]
        }
    },
    "angers": {
        "full_name": "Angers SCO",
        "short_name": "Angers",
        "city": "Angers",
        "stadium": "Stade Raymond Kopa",
        "coach": "Alexandre Dujeux",
        "api_football_id": 77,
        "preferred_formations": ["4-4-2", "3-5-2"],
        "style": "Solidité défensive, bloc bas, contre-attaques",
        "squad": {
            "GK": [{"name": "Yahia Fofana", "number": 1, "rating": 76, "age": 25}],
            "DEF": [
                {"name": "Cédric Hountondji", "number": 4, "rating": 74, "position": "DC", "age": 31},
                {"name": "Halid Sabanovic", "number": 3, "rating": 73, "position": "DC", "age": 26},
                {"name": "Yan Music", "number": 5, "rating": 73, "position": "DG", "age": 23},
                {"name": "Souleyman Doumbia", "number": 2, "rating": 74, "position": "DD", "age": 29},
            ],
            "MID": [
                {"name": "Himad Abdelli", "number": 10, "rating": 75, "position": "MOC", "age": 26},
                {"name": "Farid El Melali", "number": 7, "rating": 74, "position": "AD", "age": 27},
                {"name": "Pierrick Capelle", "number": 8, "rating": 73, "position": "MC", "age": 39},
                {"name": "Baptiste Music", "number": 6, "rating": 73, "position": "MC", "age": 23},
            ],
            "FWD": [
                {"name": "Abdallah Sima", "number": 9, "rating": 75, "position": "BU", "age": 24},
                {"name": "Jim Allevinah", "number": 11, "rating": 73, "position": "AG", "age": 28},
            ],
        },
        "default_xi": {
            "formation": "4-4-2",
            "lineup": [
                "Fofana",
                "Doumbia", "Hountondji", "Sabanovic", "Music",
                "El Melali", "Capelle", "Abdelli", "Allevinah",
                "Sima", "Allevinah"
            ]
        }
    },
    "auxerre": {
        "full_name": "AJ Auxerre",
        "short_name": "Auxerre",
        "city": "Auxerre",
        "stadium": "Stade de l'Abbé-Deschamps",
        "coach": "Christophe Pélissier",
        "api_football_id": 78,
        "preferred_formations": ["4-2-3-1", "4-4-2"],
        "style": "Jeu direct, solidité défensive, transitions",
        "squad": {
            "GK": [{"name": "Donovan Léon", "number": 1, "rating": 75, "age": 33}],
            "DEF": [
                {"name": "Jubal", "number": 4, "rating": 75, "position": "DC", "age": 30},
                {"name": "Théo Pellenard", "number": 3, "rating": 73, "position": "DG", "age": 30},
                {"name": "Gideon Mensah", "number": 5, "rating": 73, "position": "DG", "age": 26},
                {"name": "Kévin Oliveira", "number": 2, "rating": 73, "position": "DD", "age": 25},
            ],
            "MID": [
                {"name": "Birama Touré", "number": 6, "rating": 74, "position": "MC", "age": 28},
                {"name": "Lassine Sinayoko", "number": 10, "rating": 73, "position": "MOC", "age": 24},
                {"name": "Gauthier Hein", "number": 8, "rating": 74, "position": "MC", "age": 27},
            ],
            "FWD": [
                {"name": "Gaëtan Perrin", "number": 9, "rating": 74, "position": "BU", "age": 25},
                {"name": "Hamed Traoré", "number": 7, "rating": 76, "position": "AD", "age": 24},
                {"name": "Ado Onaiwu", "number": 11, "rating": 73, "position": "BU", "age": 30},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Léon",
                "Oliveira", "Jubal", "Mensah", "Pellenard",
                "Touré", "Hein",
                "Traoré", "Sinayoko", "Perrin",
                "Onaiwu"
            ]
        }
    },
    "le_havre": {
        "full_name": "Le Havre AC",
        "short_name": "Le Havre",
        "city": "Le Havre",
        "stadium": "Stade Océane",
        "coach": "Didier Digard",
        "api_football_id": 111,
        "preferred_formations": ["4-2-3-1", "4-4-2"],
        "style": "Bloc défensif solide, contre-attaques, jeu physique",
        "squad": {
            "GK": [{"name": "Arthur Desmas", "number": 1, "rating": 75, "age": 28}],
            "DEF": [
                {"name": "Arouna Sangante", "number": 4, "rating": 74, "position": "DC", "age": 25},
                {"name": "Christopher Operi", "number": 3, "rating": 73, "position": "DC", "age": 26},
                {"name": "Gautier Lloris", "number": 5, "rating": 73, "position": "DG", "age": 29},
                {"name": "Yohan Tavares", "number": 2, "rating": 73, "position": "DD", "age": 28},
            ],
            "MID": [
                {"name": "Abdoullah Ba", "number": 8, "rating": 75, "position": "MC", "age": 22},
                {"name": "Daler Kuzyaev", "number": 6, "rating": 74, "position": "MC", "age": 33},
                {"name": "Oussama Targhalline", "number": 10, "rating": 74, "position": "MOC", "age": 22},
            ],
            "FWD": [
                {"name": "André Ayew", "number": 9, "rating": 74, "position": "BU", "age": 36},
                {"name": "Josué Casimir", "number": 7, "rating": 73, "position": "AG", "age": 23},
                {"name": "Loïc Nego", "number": 11, "rating": 73, "position": "AD", "age": 33},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Desmas",
                "Tavares", "Sangante", "Operi", "Lloris",
                "Ba", "Kuzyaev",
                "Nego", "Targhalline", "Casimir",
                "Ayew"
            ]
        }
    },
    "lorient": {
        "full_name": "FC Lorient",
        "short_name": "Lorient",
        "city": "Lorient",
        "stadium": "Stade du Moustoir",
        "coach": "Olivier Pantaloni",
        "api_football_id": 114,
        "preferred_formations": ["4-2-3-1", "3-5-2"],
        "style": "Jeu organisé, pressing moyen, transitions efficaces",
        "squad": {
            "GK": [{"name": "Yvon Mvogo", "number": 1, "rating": 76, "age": 32}],
            "DEF": [
                {"name": "Montassar Talbi", "number": 4, "rating": 75, "position": "DC", "age": 28},
                {"name": "Julien Laporte", "number": 3, "rating": 76, "position": "DC", "age": 33},
                {"name": "Vincent Le Goff", "number": 5, "rating": 74, "position": "DG", "age": 35},
                {"name": "Igor Silva", "number": 2, "rating": 75, "position": "DD", "age": 26},
            ],
            "MID": [
                {"name": "Laurent Music", "number": 6, "rating": 75, "position": "MC", "age": 25},
                {"name": "Romain Music", "number": 8, "rating": 74, "position": "MC", "age": 27},
                {"name": "Enzo Le Fée", "number": 10, "rating": 77, "position": "MOC", "age": 25},
            ],
            "FWD": [
                {"name": "Bamba Dieng", "number": 9, "rating": 75, "position": "BU", "age": 26},
                {"name": "Adil Aouchiche", "number": 7, "rating": 74, "position": "AG", "age": 23},
                {"name": "Dilane Music", "number": 11, "rating": 73, "position": "AD", "age": 22},
            ],
        },
        "default_xi": {
            "formation": "4-2-3-1",
            "lineup": [
                "Mvogo",
                "Silva", "Laporte", "Talbi", "Le Goff",
                "Laurent Music", "Romain Music",
                "Aouchiche", "Le Fée", "Dilane Music",
                "Dieng"
            ]
        }
    },
    "paris_fc": {
        "full_name": "Paris FC",
        "short_name": "Paris FC",
        "city": "Paris",
        "stadium": "Stade Charléty",
        "coach": "Thierry Laurey",
        "api_football_id": 327,
        "preferred_formations": ["4-3-3", "4-4-2"],
        "style": "Jeu collectif, discipline tactique, transitions",
        "squad": {
            "GK": [{"name": "Lucas Music", "number": 1, "rating": 74, "age": 27}],
            "DEF": [
                {"name": "Axel Music", "number": 4, "rating": 73, "position": "DC", "age": 26},
                {"name": "Maxime Music", "number": 3, "rating": 73, "position": "DC", "age": 28},
                {"name": "Dylan Music", "number": 5, "rating": 72, "position": "DG", "age": 24},
                {"name": "Romain Music", "number": 2, "rating": 72, "position": "DD", "age": 25},
            ],
            "MID": [
                {"name": "Samuel Music", "number": 6, "rating": 73, "position": "MC", "age": 26},
                {"name": "Kevin Music", "number": 8, "rating": 73, "position": "MC", "age": 27},
                {"name": "Yannis Music", "number": 10, "rating": 74, "position": "MOC", "age": 24},
            ],
            "FWD": [
                {"name": "Julien Music", "number": 9, "rating": 73, "position": "BU", "age": 25},
                {"name": "Omar Music", "number": 7, "rating": 72, "position": "AG", "age": 23},
            ],
        },
        "default_xi": {
            "formation": "4-3-3",
            "lineup": [
                "Lucas Music",
                "Romain Music", "Axel Music", "Maxime Music", "Dylan Music",
                "Samuel Music", "Kevin Music", "Yannis Music",
                "Omar Music", "Julien Music", "Omar Music"
            ]
        }
    },
    "metz": {
        "full_name": "FC Metz",
        "short_name": "Metz",
        "city": "Metz",
        "stadium": "Stade Saint-Symphorien",
        "coach": "Laszlo Bölöni",
        "api_football_id": 112,
        "preferred_formations": ["3-5-2", "4-4-2"],
        "style": "Solidité défensive, bloc compact, contre-attaques",
        "squad": {
            "GK": [{"name": "Alexandre Oukidja", "number": 1, "rating": 76, "age": 36}],
            "DEF": [
                {"name": "Kiki Kouyaté", "number": 4, "rating": 75, "position": "DC", "age": 29},
                {"name": "Dylan Bronn", "number": 3, "rating": 75, "position": "DC", "age": 31},
                {"name": "Matthieu Udol", "number": 5, "rating": 74, "position": "DG", "age": 29},
                {"name": "Fali Candé", "number": 2, "rating": 74, "position": "DD", "age": 27},
            ],
            "MID": [
                {"name": "Lamine Gueye", "number": 6, "rating": 74, "position": "MC", "age": 26},
                {"name": "Joseph Music", "number": 8, "rating": 73, "position": "MC", "age": 25},
                {"name": "Nicolas Music", "number": 10, "rating": 74, "position": "MOC", "age": 27},
            ],
            "FWD": [
                {"name": "Georges Mikautadze", "number": 9, "rating": 77, "position": "BU", "age": 25},
                {"name": "Ibrahima Niane", "number": 7, "rating": 74, "position": "AG", "age": 27},
                {"name": "Sadio Music", "number": 11, "rating": 73, "position": "AD", "age": 24},
            ],
        },
        "default_xi": {
            "formation": "3-5-2",
            "lineup": [
                "Oukidja",
                "Kouyaté", "Bronn", "Candé",
                "Udol", "Gueye", "Joseph Music", "Nicolas Music", "Candé",
                "Mikautadze", "Niane"
            ]
        }
    },
}

# Aliases pour la recherche
TEAM_ALIASES = {
    # PSG
    "psg": "psg", "paris saint germain": "psg", "paris saint-germain": "psg", "paris sg": "psg",
    # OM
    "om": "om", "olympique de marseille": "om", "marseille": "om", "olympique marseille": "om",
    # Monaco
    "monaco": "monaco", "as monaco": "monaco", "asm": "monaco",
    # Lille
    "lille": "lille", "losc": "lille", "losc lille": "lille",
    # Lens
    "lens": "lens", "rc lens": "lens", "racing club de lens": "lens",
    # OL
    "ol": "ol", "lyon": "ol", "olympique lyonnais": "ol", "olympique de lyon": "ol",
    # Nice
    "nice": "nice", "ogc nice": "nice",
    # Rennes
    "rennes": "rennes", "stade rennais": "rennes", "srfc": "rennes",
    # Toulouse
    "toulouse": "toulouse", "tfc": "toulouse", "toulouse fc": "toulouse",
    # Brest
    "brest": "brest", "stade brestois": "brest", "sb29": "brest",
    # Strasbourg
    "strasbourg": "strasbourg", "rc strasbourg": "strasbourg", "rcsa": "strasbourg",
    # Nantes
    "nantes": "nantes", "fc nantes": "nantes", "fcn": "nantes",
    # Angers
    "angers": "angers", "angers sco": "angers", "sco": "angers",
    # Auxerre
    "auxerre": "auxerre", "aj auxerre": "auxerre", "aja": "auxerre",
    # Le Havre
    "le havre": "le_havre", "le_havre": "le_havre", "hac": "le_havre", "le havre ac": "le_havre",
    # Lorient
    "lorient": "lorient", "fc lorient": "lorient", "fcl": "lorient",
    # Paris FC
    "paris fc": "paris_fc", "paris_fc": "paris_fc", "pfc": "paris_fc",
    # Metz
    "metz": "metz", "fc metz": "metz",
}


def find_team(query: str) -> dict | None:
    """Trouve une équipe à partir d'une requête textuelle."""
    query_lower = query.lower().strip()
    team_key = TEAM_ALIASES.get(query_lower)
    if team_key and team_key in LIGUE1_TEAMS:
        return LIGUE1_TEAMS[team_key]

    # Recherche partielle
    for alias, key in TEAM_ALIASES.items():
        if query_lower in alias or alias in query_lower:
            if key in LIGUE1_TEAMS:
                return LIGUE1_TEAMS[key]
    return None


def find_team_key(query: str) -> str | None:
    """Trouve la clé d'une équipe à partir d'une requête textuelle."""
    query_lower = query.lower().strip()
    team_key = TEAM_ALIASES.get(query_lower)
    if team_key:
        return team_key
    for alias, key in TEAM_ALIASES.items():
        if query_lower in alias or alias in query_lower:
            return key
    return None


def list_all_teams() -> list[str]:
    """Retourne la liste de toutes les équipes."""
    return [team["full_name"] for team in LIGUE1_TEAMS.values()]
