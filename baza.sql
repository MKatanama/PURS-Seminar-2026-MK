DROP DATABASE IF EXISTS spektrofotometar;
CREATE DATABASE spektrofotometar;
USE spektrofotometar;

CREATE TABLE korisnik (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    ime VARCHAR(50) NOT NULL,
    prezime VARCHAR(50) NOT NULL
);

INSERT INTO korisnik (username, password, ime, prezime) VALUES
    ('PURS', '1234', 'Marin', 'Katana');

CREATE TABLE mjerenje (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ime_operatera VARCHAR(50) NOT NULL,
    prezime_operatera VARCHAR(50) NOT NULL,
    datum_vrijeme DATETIME NOT NULL,
    temperatura FLOAT,
    broj_kivete INT NOT NULL,
    ccd_podaci JSON NOT NULL
);

DROP USER IF EXISTS app@'localhost';
CREATE USER app@'localhost' IDENTIFIED BY '1234';
GRANT SELECT, INSERT ON spektrofotometar.* TO app@'localhost';
