from flask_mail import Message
from flask import current_app
from extensions import mail

def envoyer_mail_activation(utilisateur, mot_passe):
    try:
        msg = Message(
            subject="🎉 Activation de votre compte IDSecurity",
            recipients=[utilisateur.email]
        )
        
        # Version HTML moderne et élégante
        msg.html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .welcome {{
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 30px;
            font-weight: 600;
        }}
        .credentials-box {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 25px;
            margin: 30px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .credential-item {{
            margin: 15px 0;
            display: flex;
            align-items: center;
        }}
        .credential-label {{
            font-weight: 600;
            color: #2c3e50;
            min-width: 120px;
        }}
        .credential-value {{
            background: white;
            padding: 8px 15px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            font-family: 'Courier New', monospace;
            flex-grow: 1;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-weight: 600;
            margin: 25px 0;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        .warning-box {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-left: 4px solid #f39c12;
            padding: 20px;
            border-radius: 8px;
            margin: 25px 0;
        }}
        .warning-icon {{
            color: #e74c3c;
            font-size: 18px;
            margin-right: 10px;
        }}
        .footer {{
            text-align: center;
            padding: 25px;
            background-color: #f8f9fa;
            color: #7f8c8d;
            font-size: 14px;
            border-top: 1px solid #e0e0e0;
        }}
        .signature {{
            color: #2c3e50;
            font-weight: 600;
            margin-top: 20px;
        }}
        @media (max-width: 600px) {{
            .content {{
                padding: 20px;
            }}
            .credential-item {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .credential-label {{
                margin-bottom: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo">IDSecurity</div>
            <h1>Votre compte est activé !</h1>
        </div>
        
        <div class="content">
            <div class="welcome">
                Bonjour {utilisateur.prenom} {utilisateur.nom},
            </div>
            
            <p>Nous sommes ravis de vous informer que votre compte IDSecurity a été activé avec succès.</p>
            
            <div class="credentials-box">
                <h3 style="color: #3498db; margin-top: 0;">📋 Vos informations de connexion</h3>
                
                <div class="credential-item">
                    <span class="credential-label">Email :</span>
                    <span class="credential-value">{utilisateur.email}</span>
                </div>
                
                <div class="credential-item">
                    <span class="credential-label">Mot de passe :</span>
                    <span class="credential-value">{mot_passe}</span>
                </div>
            </div>
            
            <div class="warning-box">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span class="warning-icon">⚠️</span>
                    <strong>Important : Sécurité requise</strong>
                </div>
                <p>Pour la sécurité de votre compte, veuillez :</p>
                <ol>
                    <li>Vous pouvez modifier votre mot de passe dans la section "Profil"</li>
                </ol>
            </div>
            
        
        </div>
        
        <div class="footer">
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
            <p>Pour toute question, contactez notre support : support@idsecurity.com</p>
            
            <div class="signature">
                L'équipe IDSecurity<br>
                <span style="font-size: 12px; font-weight: normal;">Votre sécurité, notre priorité</span>
            </div>
            
            <p style="font-size: 12px; margin-top: 20px; color: #95a5a6;">
                © IDSecurity. Tous droits réservés.
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # Version texte brut comme fallback
        msg.body = f"""
Bonjour {utilisateur.prenom} {utilisateur.nom},

Votre compte IDSecurity a été activé avec succès.

VOUS INFORMATIONS DE CONNEXION :
Email : {utilisateur.email}
Mot de passe : {mot_passe}

IMPORTANT :
2. Modifiez votre mot de passe après la première connexion

Lien de connexion : {current_app.config.get('APP_URL', '#')}/login

Cordialement,
L'équipe IDSecurity
---
support@idsecurity.com
        """
        
        mail.send(msg)
        print(f"✅ Email d'activation envoyé avec succès à {utilisateur.email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")
        return False