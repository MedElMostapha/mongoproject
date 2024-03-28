from flask import Flask,render_template,request,redirect,url_for,session,flash
from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta
import plotly.graph_objs as go
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



def calculate_vote_rate(votes_count, total_votes):
    if total_votes == 0:
        return 0
    return round((votes_count / total_votes) * 100,2)

@app.route('/admin')
def page_admin():
    if 'admin' in session:
        # Calculer le nombre de participations par jour
        start_date = datetime.now() - timedelta(days=7)  # Date de début il y a une semaine
        end_date = datetime.now()  # Date de fin aujourd'hui

        participation_per_day = []
        dates = []

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            votes_count = vote_table.count_documents({'date': date_str})  # Supposons que la date est stockée dans la base de données
            participation_per_day.append(votes_count)
            dates.append(date_str)
            current_date += timedelta(days=1)

        # Créer le graphique Plotly (graphique à courbes)
        fig1 = go.Figure(data=[go.Scatter(x=dates, y=participation_per_day, mode='lines', marker_color='blue')])
        fig1.update_layout(
            title='Nombre de participations par jour',

            xaxis=dict(tickvals=[0], ticktext=['']),
            plot_bgcolor='white',  # Fond blanc pour le graphique
            height=300 , # Taille du graphique
        )

        # Convertir le graphique Plotly en code HTML pour l'intégrer dans le modèle HTML
        graph_html1 = fig1.to_html(full_html=False,default_height=200, default_width=300, config={'displayModeBar': False})

        # Créer le graphique Plotly pour le taux de participation
        total_votes = vote_table.count_documents({})  # Nombre total de votes exprimés
        total_candidates = candidat_table.count_documents({})  # Nombre total de candidats
        participation_count = total_votes
        non_participation_count = total_votes - total_candidates
        candidats_data = candidat_table.find()

        values = [participation_count, non_participation_count]

        fig2 = go.Figure(data=[go.Bar(y=values, marker_color=['green', 'red'], width=0.5)])
        fig2.update_layout(
            title='Taux de participation',
            legend_title='Légendes',
            xaxis=dict(tickvals=[0], ticktext=['']),
            legend=dict(x=0, y=-0.2),  # Positionner les légendes en bas du graphe
            plot_bgcolor='white',  # Fond blanc pour le graphique
            height=300 , # Taille du graphique
            width=200

        )

        # Convertir le deuxième graphique Plotly en code HTML pour l'intégrer dans le modèle HTML
        graph_html2 = fig2.to_html(full_html=False,default_height=200, default_width=300, config={'displayModeBar': False})

        candidats_votes = []
        for cand in candidats_data:
            votes_count = vote_table.count_documents({'candidat_id': ObjectId(cand['_id'])})
            vote_rate = calculate_vote_rate(votes_count, total_votes)
            candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count, 'vote_rate': vote_rate})

        return render_template('admin.html', candidats_votes=candidats_votes, graph_html1=graph_html1, graph_html2=graph_html2)
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
    participation_rate = round((total_votes / total_candidates) * 100 if total_candidates > 0 else 0,2)

    # Calculez le taux de non-participation
    non_participation_rate = round(100 - participation_rate,2)

    # Obtenez les détails de chaque candidat
    candidats_data = candidat_table.find()
    candidats_votes = []
    for cand in candidats_data:
        votes_count = vote_table.count_documents({'candidat_id': ObjectId(cand['_id'])})
        candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count})

    return render_template('resultat.html', total_votes=total_votes, total_candidates=total_candidates,
                           participation_rate=participation_rate, non_participation_rate=non_participation_rate,
                           candidats_votes=candidats_votes)



if __name__ == '__main__':
    app.run(debug=True)


