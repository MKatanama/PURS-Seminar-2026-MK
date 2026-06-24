import time

import serial


# USB serijski portovi na Raspberry Pi racunalu.
ARDUINO_PORT = "/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_854383330363514112C0-if00"
STM32_PORT = "/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_338B344B3035-if00"

BAUDRATE = 115200
CCD_BROJ_PIKSELA = 3694
CCD_BROJ_BAJTOVA = CCD_BROJ_PIKSELA * 2
SH_PERIOD = 200
ICG_PERIOD = 100000
BROJ_USREDNJAVANJA = 1


def pripremi_mehatroniku():
    arduino = serial.Serial(ARDUINO_PORT, BAUDRATE, timeout=0.3, write_timeout=1)

    kraj = time.monotonic() + 8
    while time.monotonic() < kraj:
        linija = arduino.readline().decode("ascii", errors="replace").strip()
        if linija == "Type help to display all SCPI commands.":
            break

    arduino.reset_input_buffer()
    arduino.reset_output_buffer()

    return arduino


def posalji_naredbu(arduino, naredba, timeout=5):
    arduino.write((naredba + "\n").encode("ascii"))
    arduino.flush()

    kraj = time.monotonic() + timeout
    while time.monotonic() < kraj:
        odgovor = arduino.readline().decode("ascii", errors="replace").strip()
        if odgovor:
            return odgovor

    raise RuntimeError("Mehatronicka jedinica nije odgovorila")


def provjeri_vrata(arduino):
    odgovor = posalji_naredbu(arduino, "DOOR?")

    if odgovor != "Door is closed.":
        raise RuntimeError("Vrata instrumenta nisu zatvorena")


def pomakni_na_kivetu(arduino, broj_kivete):
    odgovor = posalji_naredbu(arduino, "POSition:CUVette " + str(broj_kivete), timeout=20)

    if odgovor != "OK":
        raise RuntimeError("Karusel nije potvrdio dolazak u zadanu poziciju")


def ocitaj_temperaturu(arduino):
    odgovor = posalji_naredbu(arduino, "TEMP?")
    return float(odgovor)


def ukljuci_lampu(arduino):
    posalji_naredbu(arduino, "LAMP 1")


def iskljuci_lampu(arduino):
    posalji_naredbu(arduino, "LAMP 0")


def ocitaj_ccd():
    naredba = bytearray(12)
    naredba[0] = ord("E")
    naredba[1] = ord("R")
    naredba[2] = (SH_PERIOD >> 24) & 0xFF
    naredba[3] = (SH_PERIOD >> 16) & 0xFF
    naredba[4] = (SH_PERIOD >> 8) & 0xFF
    naredba[5] = SH_PERIOD & 0xFF
    naredba[6] = (ICG_PERIOD >> 24) & 0xFF
    naredba[7] = (ICG_PERIOD >> 16) & 0xFF
    naredba[8] = (ICG_PERIOD >> 8) & 0xFF
    naredba[9] = ICG_PERIOD & 0xFF
    naredba[10] = 0
    naredba[11] = BROJ_USREDNJAVANJA

    with serial.Serial(STM32_PORT, BAUDRATE, timeout=5, write_timeout=5) as stm32:
        stm32.reset_input_buffer()
        stm32.reset_output_buffer()
        stm32.write(naredba)
        stm32.flush()
        sirovi_bajtovi = stm32.read(CCD_BROJ_BAJTOVA)

    if len(sirovi_bajtovi) != CCD_BROJ_BAJTOVA:
        raise RuntimeError("CCD ocitanje nije vratilo ocekivani broj bajtova")

    podaci = []
    for i in range(CCD_BROJ_PIKSELA):
        vrijednost = sirovi_bajtovi[2 * i] | (sirovi_bajtovi[2 * i + 1] << 8)
        podaci.append(vrijednost)

    return podaci
