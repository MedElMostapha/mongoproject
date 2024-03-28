from flask import Flask,render_template,request,redirect,url_for,session,flash
from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta
import plotly.graph_objs as go
from operator import itemgetter
import pandas as pd


from plotly.subplots import make_subplots




from bson.objectid import ObjectId

app = Flask(__name__, template_folder='templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' 


client=MongoClient("localhost",27017)

db=client['election']
candidat_table=db.candidat
utilisateurs=db.utilisateurs
vote_table=db.vote


def est_authentifie(role_requis=None):
    if 'utilisateur_id' in session:
        utilisateur = utilisateurs.find_one({'_id': ObjectId(session['utilisateur_id'])})
        if utilisateur:
            if role_requis:
                return utilisateur.get('role') == role_requis
            return True
    return False

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        nni=request.form['nni']
        # email = request.form['email']
        nni=request.form['nni']
        mot_de_passe = request.form['mot_de_passe'].encode('utf-8')
        role = 'electeur'  # Vous pouvez ajouter un champ pour le rôle dans le formulaire d'inscription

        # Vérifie si l'utilisateur existe déjà dans la base de données
        if utilisateurs.find_one({'nni': nni}):
            return 'Un utilisateur avec cet email existe déjà. Veuillez choisir un autre email.'

        # Hachage du mot de passe
        mot_de_passe_hache = bcrypt.hashpw(mot_de_passe, bcrypt.gensalt())

        # Création de l'utilisateur dans la base de données
        nouvel_utilisateur = {
            'nom': nom,
            'prenom': prenom,
            'nni': nni,
            'mot_de_passe': mot_de_passe_hache,
            'role': role  # Vous pouvez stocker le rôle de l'utilisateur dans la base de données
        }
        utilisateurs.insert_one(nouvel_utilisateur)

        # Redirige l'utilisateur vers la page de connexion
        return redirect(url_for('connexion'))
    else:
        return render_template('inscription.html')


@app.route('/', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        mot_de_passe = request.form['mot_de_passe'].encode('utf-8')
        motadmin = request.form['mot_de_passe']
        nni = request.form['nni']

        # Vérifier si l'utilisateur est un administrateur
        if nni == 'admin@admin' and motadmin == 'admin':
            session['admin'] = nni
            return redirect(url_for('page_admin'))

        # Si ce n'est pas un administrateur, recherchez l'utilisateur dans la base de données
        utilisateur = utilisateurs.find_one({'nni': nni})

        if utilisateur and bcrypt.checkpw(mot_de_passe, utilisateur['mot_de_passe']) and nni == utilisateur['nni']:
            session['utilisateur_id'] = str(utilisateur['_id'])
            return redirect(url_for('index'))
        else:
            return 'Identifiants incorrects. Veuillez réessayer.'
    else:
        return render_template('connexion.html')

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    
    
    return redirect(url_for('connexion'))


@app.route("/candidats",methods=['GET','POST'])
def index():
    if est_authentifie():

        etat=""
        candidats=candidat_table.find()
        utilisateur_id = session.get('utilisateur_id')
        utilisateur = utilisateurs.find_one({'_id': ObjectId(utilisateur_id)})
        if utilisateur:
            has_voted = vote_table.find_one({'utilisateur_id': utilisateur_id})
            if has_voted:
                etat="voted"
            
        return render_template("index.html",candidats=candidats,etat=etat)
    
    else:

        return redirect(url_for('connexion'))

@app.route('/list', methods=['GET'])
def liste_candidats():
    candidats = candidat_table.find()
    return render_template('candidats.html', candidats=candidats)

# Ajouter un nouveau candidat
@app.route('/candidats/nouveau', methods=['GET', 'POST'])
def ajouter_candidat():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        candidat_table.insert_one({'nom': nom, 'prenom': prenom})
        return redirect(url_for('liste_candidats'))
    else:
        return render_template('ajouterForm.html')

# Modifier un candidat existant
@app.route('/candidats/modifier/<string:candidat_id>', methods=['GET', 'POST'])
def modifier_candidat(candidat_id):
    candidat = candidat_table.find_one({'_id': ObjectId(candidat_id)})
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        candidat_table.update_one({'_id': ObjectId(candidat_id)}, {'$set': {'nom': nom, 'prenom': prenom}})
        return redirect(url_for('liste_candidats'))
    else:
        return render_template('modifier_candidat.html', candidat=candidat)

# Supprimer un candidat
@app.route('/candidats/supprimer/<string:candidat_id>', methods=['POST'])
def supprimer_candidat(candidat_id):
    candidat_table.delete_one({'_id': ObjectId(candidat_id)})
    return redirect(url_for('liste_candidats'))


@app.route("/ajouter",methods=['GET','POST'])
def ajouter():
    if request.method=='POST':

        nom=request.form['nom']
        prenom=request.form['prenom']
        image=request.form['image']
        age=request.form['age']
        partie=request.form['partie']

        cnd={'nom':nom,'prenom':prenom,'image':image,'age':age,"partie":partie}


        candidat_table.insert_one(cnd)

        return redirect('ajouter')

    
    return render_template('ajouterform.html')
@app.route('/voter', methods=['POST'])
def voter():
    if request.method == 'POST':
        if est_authentifie():
            nom = request.form['nom']
            prenom = request.form['prenom']
            candidat_id = request.form['id']

            utilisateur_id = session.get('utilisateur_id')
            utilisateur = utilisateurs.find_one({'_id': ObjectId(utilisateur_id)})

            if utilisateur:
                # Check if the user has already voted
                has_voted = vote_table.find_one({'utilisateur_id': utilisateur_id, 'candidat_id': ObjectId(candidat_id)})
                if has_voted:
                    flash('Vous avez déjà voté pour ce candidat.')
                    return redirect(url_for("index"))

                vote_table.insert_one({'utilisateur_id': utilisateur_id, 'nom': nom, 'prenom': prenom, 'candidat_id': ObjectId(candidat_id)})
                flash('Votre vote a été enregistré avec succès.')

                return redirect(url_for("index"))
            else:
                return 'Utilisateur non trouvé.'
        else:
            return redirect(url_for('connexion'))
    else:
        return 'Méthode non autorisée.'
    
@app.route('/upload_users', methods=['POST'])
def upload_users():
    if 'file' not in request.files:
        return 'Aucun fichier n\'a été téléchargé.'

    file = request.files['file']
    if file.filename == '':
        return 'Nom de fichier vide.'

    if file and file.filename.endswith('.xlsx'):
        try:
            # Lecture du fichier Excel
            df = pd.read_excel(file)
            # Convertir les données en dictionnaires pour l'insertion dans MongoDB
            users_data = df.to_dict('records')
            # Insérer les données dans la collection utilisateurs
            utilisateurs.insert_many(users_data)
            return 'Les utilisateurs ont été importés avec succès dans la base de données.'
        except Exception as e:
            return f'Une erreur s\'est produite lors de l\'importation des utilisateurs : {str(e)}'
    else:
        return 'Veuillez télécharger un fichier au format Excel (.xlsx).'







def calculate_vote_rate(votes_count, total_votes):
    if total_votes == 0:
        return 0
    return round((votes_count / total_votes) * 100,2)

@app.route('/admin')
def page_admin():
    if 'admin' in session:
        # Obtenez le nombre total de votes exprimés
        total_votes = vote_table.count_documents({})

        # Obtenez le nombre total de candidats
        total_candidates = utilisateurs.count_documents({})

        # Calculez le nombre de participations
        participation_count = total_votes

        # Calculez le nombre de non-participations
        non_participation_count = total_candidates - total_votes

        # Calculez le taux de participation réel
        participation_rate = round((participation_count / total_candidates) * 100, 2)

        # Calculez le taux de non-participation
        non_participation_rate = round(100 - participation_rate, 2)

        candidats_data = candidat_table.find()

        print("non : ",non_participation_count)

        values = [participation_count, non_participation_count]
        labels = ['Participation', 'Non-participation']  # Ajout des étiquettes

        fig2 = go.Figure(data=[go.Bar(y=values, marker_color=['green', 'red'], width=0.5, hovertext=labels)])
        fig2.update_layout(
            title='Taux de participation',
            xaxis=dict(tickvals=[0], ticktext=['']),
            legend=dict(x=0, y=-0.2),  # Positionner les légendes en bas du graphe
            plot_bgcolor='white',  # Fond blanc pour le graphique
            height=250,  # Taille du graphique
            width=200,
            hovermode='x',  # Activer le mode d'affichage au survol (affiche les informations au survol de la souris)
        )

        # Convertir le deuxième graphique Plotly en code HTML pour l'intégrer dans le modèle HTML
        graph_html2 = fig2.to_html(full_html=False, default_height=100, default_width=200, config={'displayModeBar': False})

        candidats_votes = []
        for cand in candidats_data:
            votes_count = vote_table.count_documents({'candidat_id': ObjectId(cand['_id'])})
            vote_rate = calculate_vote_rate(votes_count, total_votes)
            candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count, 'vote_rate': vote_rate})

        return render_template('admin.html', candidats_votes=candidats_votes, graph_html2=graph_html2)
    else:
        return 'Accès refusé. Vous devez être connecté en tant qu\'administrateur.'




    


@app.route('/electeurs')
def page_electeurs():
    if 'admin' in session:
        utilisateurs_data = utilisateurs.find()
        return render_template('electeurs.html',utilisateurs=utilisateurs_data)
    else:
        return 'Accès refusé. Vous devez être connecté en tant qu\'administrateur.'


@app.route('/taux_vote_par_candidat')
def taux_vote_par_candidat():
    candidats = candidat_table.find()
    candidats_votes = []

    # Calculer le nombre total de votes
    total_votes = vote_table.count_documents({})
    print(total_votes)

    # Calculer le nombre de votes pour chaque candidat
    for candidat in candidats:
        votes_count = vote_table.count_documents({'candidat_id': str(candidat['_id'])})
        candidats_votes.append({'nom': candidat['nom'], 'prenom': candidat['prenom'], 'votes_count': votes_count})
    
    # Calculer le taux de vote pour chaque candidat
    for candidat in candidats_votes:
        if total_votes > 0:
            candidat['vote_rate'] = (candidat['votes_count'] / total_votes) * 100
        else:
            candidat['vote_rate'] = 0
    
    return render_template('admin.html', candidats_votes=candidats_votes)








@app.route('/resultat')
def resultat():
    # Obtenez le nombre total de votes exprimés
    total_votes = vote_table.count_documents({})

    # Obtenez le nombre total de candidats
    total_candidates = utilisateurs.count_documents({})

    # Calculez le taux de participation réel
    participation_rate = round((total_votes / total_candidates) * 100 if total_candidates > 0 else 0, 2)

    # Calculez le taux de non-participation
    non_participation_rate = round(100 - participation_rate, 2)

    # Obtenez les détails de chaque candidat avec le nombre de votes
    candidats_data = candidat_table.find()
    candidats_votes = []
    for cand in candidats_data:
        votes_count = vote_table.count_documents({'candidat_id': ObjectId(cand['_id'])})
        candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count})

    # Trier les candidats par nombre de votes (classement)
    candidats_votes.sort(key=itemgetter('votes_count'), reverse=True)
    
    # Ajouter le classement à chaque candidat
    for i, candidat in enumerate(candidats_votes, start=1):
        candidat['classement'] = i

    return render_template('resultat.html', total_votes=total_votes, total_candidates=total_candidates,
                           participation_rate=participation_rate, non_participation_rate=non_participation_rate,
                           candidats_votes=candidats_votes)




if __name__ == '__main__':
    app.run(debug=True)


