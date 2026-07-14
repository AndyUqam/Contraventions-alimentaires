-- Script de création de la base de données pour les contraventions alimentaires
-- Table principale : violations

CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_poursuite TEXT,
    business_id TEXT,
    date TEXT,
    description TEXT,
    adresse TEXT,
    date_jugement DATE,
    etablissement TEXT,
    montant REAL,
    proprietaire TEXT,
    ville TEXT,
    statut TEXT,
    date_statut TEXT,
    categorie TEXT
);

-- Index pour accélérer les recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_etablissement ON violations(etablissement);
CREATE INDEX IF NOT EXISTS idx_proprietaire ON violations(proprietaire);
CREATE INDEX IF NOT EXISTS idx_adresse ON violations(adresse);
CREATE INDEX IF NOT EXISTS idx_date ON violations(date);

-- Table des demandes d'inspection (D1)
CREATE TABLE IF NOT EXISTS demandes_inspection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_etablissement TEXT NOT NULL,
    adresse TEXT NOT NULL,
    ville TEXT NOT NULL,
    date_visite_client TEXT NOT NULL,
    nom_client TEXT NOT NULL,
    prenom_client TEXT NOT NULL,
    description_probleme TEXT NOT NULL,
    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_demandes_inspection_ville
ON demandes_inspection(ville);
