import secrets
import string

def generer_mot_de_passe(longueur=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longueur))

