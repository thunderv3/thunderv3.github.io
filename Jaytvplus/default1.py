import xbmcgui
import xbmc
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import xbmcvfs
import re
import hashlib
import shutil
import os
from email.utils import formataddr

# URL zur Key-Liste auf Pastebin
KEY_LIST_URL = "https://thunderv3.github.io/Jaytvplus/list.txt"
UPDATE_URL = "http://thunderv3.myexter.com/default1.py"

# SMTP-Serverkonfiguration
SENDER_NAME = "JayTv Support"
SMTP_SERVER = "smtp.web.de"
SMTP_PORT = 587
SENDER_EMAIL = "JaytvPlus@web.de"
SENDER_PASSWORD = "jaytvplus123"

def get_key_list():
    """Lädt die Key-Liste von Pastebin und gibt sie als Liste zurück."""
    try:
        response = urllib.request.urlopen(KEY_LIST_URL)
        key_list = response.read().decode().splitlines()
        return [key.strip() for key in key_list]
    except Exception as e:
        log_and_quit(f"Fehler beim Abrufen der Key-Liste: {e}")

def download_update():
    destination_path = xbmcvfs.translatePath("special://home/addons/service.key/default.py")
    try:
        response = urllib.request.urlopen(UPDATE_URL)
        new_script = response.read().decode()
 
        xbmcgui.Dialog().notification("Update", "Update erfolgreich installiert!", xbmcgui.NOTIFICATION_INFO)
       except Exception as e:
        xbmcgui.Dialog().notification("Update Fehler", f"Fehler beim Herunterladen: {e}", xbmcgui.NOTIFICATION_ERROR)

def check_for_update():
    local_path = xbmcvfs.translatePath("special://home/addons/service.key/default.py")
    try:
        if xbmcvfs.exists(local_path):
            with xbmcvfs.File(local_path, 'r') as f:
                local_content = f.read()
        else:
            local_content = ""
        
        response = urllib.request.urlopen(UPDATE_URL)
        online_content = response.read().decode()
        
        local_hash = hashlib.sha256(local_content.encode()).hexdigest()
        online_hash = hashlib.sha256(online_content.encode()).hexdigest()
        
        if local_hash != online_hash:
            xbmcgui.Dialog().notification("Update", "Neue Version gefunden! Wird aktualisiert...", xbmcgui.NOTIFICATION_INFO)
            download_update()
        else:
            xbmcgui.Dialog().notification("Update", "Sie haben bereits die neueste Version.", xbmcgui.NOTIFICATION_INFO)
    except Exception as e:
        xbmcgui.Dialog().notification("Update Fehler", f"Fehler bei der Update-Prüfung: {e}", xbmcgui.NOTIFICATION_ERROR)

def send_email(recipient_email, key):
    """Sendet den Key per E-Mail an den Empfänger."""
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))  
        msg['To'] = recipient_email
        msg['Subject'] = "Ihr JayTv Plus Support"
        body = f"Willkommen bei JayTv Plus, \n\nSie haben einen Key angefordert zur Authentifizierung. n\Ihr persönlicher Key {key}\n\nBitte beachten sie dass dieser Key ausschließlich für ihre private Nutzung gedacht ist. \n\nWir wünschen ihnen viel Spas mit JayTv Plus"
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())

        xbmcgui.Dialog().notification("E-Mail gesendet", f"Key wurde an {recipient_email} gesendet.", xbmcgui.NOTIFICATION_INFO)
    except Exception as e:
        log_and_quit(f"Fehler beim Senden der E-Mail: {e}")

def hash_value(value):
    """Hasht einen Wert (z. B. E-Mail) mit SHA-256."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def save_data_to_file(email, key=None):
    """Speichert die E-Mail-Adresse einmal gehasht und einmal im Klartext in der Datei 'key.py'."""
    USERDATA_DIR = xbmcvfs.translatePath("special://xbmc/addons/privat.key/")
    
    if not xbmcvfs.exists(USERDATA_DIR):
        xbmcvfs.mkdirs(USERDATA_DIR)

    file_path = xbmcvfs.translatePath("special://xbmc/addons/privat.key/key.py")
    hashed_email = hash_value(email)

    file_content = f"# Hier sind die gespeicherten Daten für JayTv Plus\n"
    file_content += f"EMAIL1 = '{hashed_email}'\n"  # E-Mail1 gehasht
    file_content += f"EMAIL2 = '{email}'\n"  # E-Mail2 im Klartext

    if key:
        hashed_key = hash_value(key)
        file_content += f"KEY = '{hashed_key}'\n"  # Optionaler gehashter Key

    try:
        # Ursprüngliche Datei speichern
        with xbmcvfs.File(file_path, 'w') as f:
            f.write(file_content)
        print("E-Mails und optionaler Key wurden erfolgreich gespeichert.")

        # Kopie der Datei im neuen Ordner speichern
        NEW_USERDATA_DIR = xbmcvfs.translatePath("special://userdata/addon_data/privat.key/")
        if not xbmcvfs.exists(NEW_USERDATA_DIR):
            xbmcvfs.mkdirs(NEW_USERDATA_DIR)

        new_file_path = xbmcvfs.translatePath("special://userdata/addon_data/privat.key/key.py")
        with xbmcvfs.File(new_file_path, 'w') as f:
            f.write(file_content)

        print("Kopie der Datei wurde erfolgreich im neuen Ordner gespeichert.")
        
    except Exception as e:
        print(f"Fehler beim Speichern der Daten: {e}")

def read_key_from_file():
    """Liest die gespeicherte E-Mail und den gehashten Key aus der 'key.py'-Datei."""
    file_path = xbmcvfs.translatePath("special://xbmc/addons/privat.key/key.py")
    if not xbmcvfs.exists(file_path):
        return None

    try:
        with xbmcvfs.File(file_path, 'r') as f:
            content = f.read()
            match_email = re.search(r"EMAIL2 = '(.*?)'", content)  # Wir suchen nach der E-Mail im Klartext
            match_key = re.search(r"KEY = '(.*?)'", content)

            if match_email:
                email = match_email.group(1)
                key = match_key.group(1) if match_key else None
                return email, key
            else:
                return None
    except Exception as e:
        log_and_quit(f"Fehler beim Lesen der Datei: {e}")
    return None

def check_key(key_input):
    """Überprüft, ob der Key in der Key-Liste vorhanden ist."""
    key_list = get_key_list()
    if key_input in key_list:
        xbmcgui.Dialog().notification("JayTv Plus", "Key akzeptiert", xbmcgui.NOTIFICATION_INFO)
        return True
    else:
        log_and_quit("Key nicht autorisiert")
    return False

def log_and_quit(message):
    """Protokolliert eine Fehlermeldung und beendet Kodi."""
    xbmcgui.Dialog().notification("Fehler", message, xbmcgui.NOTIFICATION_ERROR)
    xbmc.executebuiltin("Quit")

def check_saved_email():
    """Überprüft, ob die gehashte E-Mail und die Klartext-E-Mail in der 'key.py' Datei übereinstimmen."""
    data = read_key_from_file()
    if data is None:
        return False  # Die Datei existiert nicht oder E-Mail und Key fehlen

    email, _ = data  # Wir holen uns die Klartext-E-Mail aus der Datei
    hashed_email = hash_value(email)  # Die Klartext-E-Mail wird gehasht

    file_path = xbmcvfs.translatePath("special://xbmc/addons/privat.key/key.py")
    if not xbmcvfs.exists(file_path):
        return False  # Die Datei existiert nicht

    try:
        with xbmcvfs.File(file_path, 'r') as f:
            content = f.read()
            match_email1 = re.search(r"EMAIL1 = '(.*?)'", content)  # Gehashte E-Mail
            match_email2 = re.search(r"EMAIL2 = '(.*?)'", content)  # Klartext-E-Mail

            if match_email1 and match_email2:
                stored_hashed_email = match_email1.group(1)
                stored_email = match_email2.group(1)

                # Vergleiche den gehashten Wert mit dem gespeicherten gehashten Wert und den Klartext
                if stored_hashed_email == hashed_email and stored_email == email:
                    return True  # Die E-Mails stimmen überein
                else:
                    return False  # Die E-Mails stimmen nicht überein
            else:
                return False  # Falls die E-Mail-Daten fehlen oder unvollständig sind
    except Exception as e:
        log_and_quit(f"Fehler beim Überprüfen der E-Mail-Daten: {e}")
    
    return False

def check_saved_key():
    """Überprüft, ob der gespeicherte gehashte Key in der 'key.py' Datei gültig ist."""
    data = read_key_from_file()
    if data is None:
        return False  # Die Datei existiert nicht oder der Key bzw. E-Mail fehlt

    email, saved_hashed_key = data

    # Wähle einen zufälligen Key aus der Online-Liste und hashe ihn
    key_list = get_key_list()
    for key in key_list:
        if saved_hashed_key == hash_value(key):  # Vergleiche den gehashten Key
            xbmcgui.Dialog().notification("JayTv Plus", "Kodi wird gestartet.", xbmcgui.NOTIFICATION_INFO)
            return True
    return False

def copy_default_py():
    """Kopiert die 'default.py' Datei von der Addon-Struktur in den Userdata-Ordner."""
    source_path = xbmcvfs.translatePath("special://xbmc/addons/service.key/default.py")
    destination_path = xbmcvfs.translatePath("special://home/addons/service.key/default.py")
    
       # Sicherstellen, dass der Zielordner existiert
    xbmcvfs.mkdirs(os.path.dirname(destination_path))

    # Datei kopieren
    xbmcvfs.copy(source_path, destination_path)
    
def copy_addon_xml():
    """Kopiert die 'addon.xml' Datei von der Addon-Struktur in den Userdata-Ordner."""
    source_path = xbmcvfs.translatePath("special://xbmc/addons/service.key/addon.xml")
    destination_path = xbmcvfs.translatePath("special://home/addons/service.key/addon.xml")
    
       # Sicherstellen, dass der Zielordner existiert
    xbmcvfs.mkdirs(os.path.dirname(destination_path))

    # Datei kopieren
    xbmcvfs.copy(source_path, destination_path)    
    
def copy_key_py():
    """Kopiert die 'key.py' Datei von der Addon-Struktur in den Userdata-Ordner."""
    source_path = xbmcvfs.translatePath("special://xbmc/addons/privat.key/key.py")
    destination_path = xbmcvfs.translatePath("special://home/addons/privat.key/key.py")
   
   # Sicherstellen, dass der Zielordner existiert
    xbmcvfs.mkdirs(os.path.dirname(destination_path))

    # Datei kopieren
    xbmcvfs.copy(source_path, destination_path)

def main():
    """Hauptfunktion des Scripts."""
    # Update der default.py datei vom server.
    check_for_update()
    xbmcgui.Dialog().ok("JayTv Plus", "Willkommen bei JayTv Plus!")
    if not check_saved_email() or not check_saved_key():
        # Auswahlmenü: Neues Konto erstellen oder vorhandenes Konto verwenden
        dialog = xbmcgui.Dialog()
        selection = dialog.select("Wählen Sie eine Option", ["Neues Konto erstellen", "Vorhandenes Konto verwenden"])

        # Wenn der Benutzer das Menü abbricht (auswählt -1), beende Kodi
        if selection == -1:
            log_and_quit("Abbruch der Auswahl. Kodi wird beendet.")
            return

        if selection == 0:  # Neues Konto erstellen
            email = dialog.input("Geben Sie Ihre E-Mail-Adresse ein", type=xbmcgui.INPUT_ALPHANUM)
            if not email:
                log_and_quit("Keine E-Mail-Adresse eingegeben")

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                log_and_quit("Ungültige E-Mail-Adresse")

            key_list = get_key_list()
            if key_list:
                random_key = random.choice(key_list)
                send_email(email, random_key)  # Sende den zufälligen Key per E-Mail

                # Überprüfe den Key, den der Benutzer eingibt
                dialog.ok("JayTv Plus", "Bitte geben Sie den Key ein, den Sie per E-Mail erhalten haben.")
                key_input = dialog.input("Key Eingabe", type=xbmcgui.INPUT_ALPHANUM)
                if check_key(key_input):  # Wenn der Key gültig ist
                    save_data_to_file(email, key_input)
                    xbmc.executebuiltin("EnableAddon(service.activate)")  # Service-Addon aktivieren
                else:
                    log_and_quit("Key ungültig!")
            else:
                log_and_quit("Keine Keys gefunden")
        elif selection == 1:  # Vorhandenes Konto verwenden
            # E-Mail und Key manuell eingeben
            email = dialog.input("Geben Sie Ihre E-Mail-Adresse ein", type=xbmcgui.INPUT_ALPHANUM)
            key_input = dialog.input("Geben Sie Ihren Key ein", type=xbmcgui.INPUT_ALPHANUM)
            
            if check_key(key_input):  # Wenn der Key gültig ist
                save_data_to_file(email, key_input)
                xbmc.executebuiltin("EnableAddon(service.activate)")  # Service-Addon aktivieren
            else:
                log_and_quit("Key ungültig!")
    
    # Kopiere default.py in den Userdata-Ordner
    copy_default_py()
    # Copie key.py
    copy_key_py()
    # Copie addon.xml
    copy_addon_xml()
# Skript ausführen
main()
