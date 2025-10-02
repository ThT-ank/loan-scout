import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors


def send_notif_with_image(image_path):
    topic = "SimuImmoTopicTTank"
    headers = {"Filename": f"{image_path}"}

    with open(f"{image_path}", 'rb') as image_file:
        response = requests.put(f"https://ntfy.sh/{topic}", headers=headers, data=image_file)
        if response.status_code == 200:
            print("Notification envoyée avec succès.")
        else:
            print("Échec de l'envoi de la notification.")

def order_data(resultats):

    if not resultats:
        print("Data empty, exiting..")
        exit()

    # Exemple de DataFrame
    df = pd.DataFrame(resultats)

    from textwrap import wrap

        # Fonction pour formater les en-têtes automatiquement
    def wrap_column_labels(labels, width=7):
        return ['\n'.join(wrap(label, width)) for label in labels]

    # Transformer les en-têtes des colonnes
    wrapped_columns = wrap_column_labels(df.columns, width=15)

    # Créer une figure pour le tableau
    fig, ax = plt.subplots(figsize=(10, 4))  # Ajuster la taille

    # Masquer les axes
    ax.axis('tight')
    ax.axis('off')

    # Couleurs pour alternance des lignes
    row_colors = [mcolors.to_rgba("lightblue", 0.4), mcolors.to_rgba("lightblue", 0.2)]

    # Ajouter le tableau à la figure avec styles
    table = ax.table(
        cellText=df.values,
        colLabels=wrapped_columns,
        loc='center',
        cellLoc='center',
        colLoc='center',
        rowLoc='center',
        cellColours=[
            [row_colors[i % 2] for _ in range(len(df.columns))]  # Alternance des lignes
            for i in range(len(df))
        ],
    )

    # Ajouter un style professionnel
    table.auto_set_font_size(False)
    table.set_fontsize(12)  # Taille de police
    table.scale(1.2, 1.5)  # Échelle pour l'espacement horizontal et vertical

    # Appliquer le texte en gras aux en-têtes et ajuster la hauteur
    for (row, col), cell in table.get_celld().items():
        if row == 0:  # En-têtes
            cell.set_text_props(weight='bold')  # Texte en gras
            cell.set_height(0.2)  # Augmenter la hauteur des en-têtes
            cell.set_fontsize(8)
        else:
            cell.set_text_props(weight='normal')  # Texte normal pour le reste
    
    # Appliquer un style à l'en-tête
    for col, cell in table.get_celld().items():
        row, col_index = col
        if row == 0:  # En-tête
            cell.set_facecolor('lightgray')  # Fond gris clair pour l'en-tête
            cell.set_text_props(weight='bold')  # Texte en gras
            cell.set_edgecolor('black')  # Bordure noire pour l'en-tête
        else:
            cell.set_edgecolor('black')  # Bordure noire pour les autres cellules

    # Sauvegarder l'image
    plt.savefig("loan_info.png", bbox_inches='tight', pad_inches=0.5, dpi=300)
    plt.close()

    send_notif_with_image("loan_info.png")


import re

def extract_loan_data(data, loanDuration):
    # Dictionnaire pour stocker les résultats
    resultats = {'Durée' : f"{loanDuration}"}

    mots_remise = (
        r"remise(?:\(s\)|s)?"
        r"|réduction(?:\(s\)|s)?"
        r"|diminution(?:\(s\)|s)?"
        r"|rabais"
    )

    # Expressions régulières pour extraire les valeurs numériques
    patterns = {
        "Capital": (r"capital emprunt[ée]\s*([\d\s]+) €", " €", int),
        "Taux n. fixe": (r"taux standard\s*([\d,]+) %", " %", float),
        "Remise": (rf"(?:{mots_remise})\s*[ée]co[-]?responsable\s*([-\d,]+)\s*%", " %", float),
        "Taux ap. remise": (rf"taux apr[èe]s\s*(?:{mots_remise})\s*([\d\s,]+)\s*%", " %", float),
        "Mensualité av. remise": (r"mensualit[ée] standard\s*([\d\s,]+) €", " €", float),
        "Mensualité ap. remise": (rf"mensualit[ée] apr[èe]s\s*(?:{mots_remise})\s*([\d\s,]+)\s*€", " €", float),
        "Assurance": (r"assurance\s*([\d\s,]+) €/mois", " €", float),
        "Économies": (rf"(?:{mots_remise})\s*[ée]co[-]?responsable\s*([\d\s]+)\s*€", " €", int),
        "Dossier": (r"frais de dossier\s*([\d\s]+) €", " €", int)
    }

    # Parcourir les motifs et extraire les valeurs correspondantes
    for champ, (pattern, unite, type_conv) in patterns.items():
        match = re.search(pattern, data, re.IGNORECASE)
        if match:
            # Nettoyer la valeur en supprimant les espaces et en remplaçant la virgule par un point
            valeur = match.group(1).replace(" ", "").replace(",", ".")
            resultats[champ] = f"{type_conv(valeur)}{unite}"

    return resultats
