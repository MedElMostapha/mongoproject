from flask import Flask,render_template,request,redirect,url_for,session
from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta



from bson.objectid import ObjectId

app = Flask(__name__, template_folder='templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' 


client=MongoClient("mongodb+srv://mohamedlemineelmostapha:cjdDhzCgE6yXxlgD@cluster0.pjq7xaj.mongodb.net/election")

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
    candidats=candidat_table.find()
    return render_template("index.html",candidats=candidats)

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

            # Récupérer l'ID de l'utilisateur à partir de la session
            utilisateur_id = session['utilisateur_id']
            utilisateur = utilisateurs.find_one({'_id': ObjectId(utilisateur_id)})

            # Vérifier si l'utilisateur existe
            if utilisateur:
                # Insérer le vote dans la base de données
                vote_table.insert_one({'utilisateur_id': utilisateur_id, 'nom': nom, 'prenom': prenom,'candidat_id':ObjectId(candidat_id)})
                return 'Votre vote a été enregistré avec succès.'
            else:
                return 'Utilisateur non trouvé.'
        else:
            return 'Vous devez être connecté pour voter.'
    else:
        return 'Méthode non autorisée.'


def calculate_vote_rate(votes_count, total_votes):
    if total_votes == 0:
        return 0
    return round((votes_count / total_votes) * 100,2)


@app.route('/admin')
def page_admin():
    if 'admin' in session:
        total_votes = vote_table.count_documents({})  # Nombre total de votes exprimés
        
        candidats_data = candidat_table.find()
        candidats_votes = []
        for cand in candidats_data:
            votes_count = vote_table.count_documents({'candidat_id': ObjectId(cand['_id'])})
            vote_rate = calculate_vote_rate(votes_count, total_votes)
            candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count, 'vote_rate': vote_rate})
        
        return render_template('admin.html', candidats_votes=candidats_votes)
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


if __name__ == '__main__':
    app.run(debug=True)


