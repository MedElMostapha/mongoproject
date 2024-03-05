from flask import Flask,render_template,request,redirect,url_for,session
from pymongo import MongoClient
import bcrypt


from bson.objectid import ObjectId


app= Flask("__name__")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Remplacez ceci par votre propre clé secrète


client=MongoClient("localhost",27017)

db=client['election']
candidat=db.candidat
utilisateurs=db.utilisateurs
vote=db.vote


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
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe'].encode('utf-8')
        role = 'electeur'  # Vous pouvez ajouter un champ pour le rôle dans le formulaire d'inscription

        # Vérifie si l'utilisateur existe déjà dans la base de données
        if utilisateurs.find_one({'email': email}):
            return 'Un utilisateur avec cet email existe déjà. Veuillez choisir un autre email.'

        # Hachage du mot de passe
        mot_de_passe_hache = bcrypt.hashpw(mot_de_passe, bcrypt.gensalt())

        # Création de l'utilisateur dans la base de données
        nouvel_utilisateur = {
            'nom': nom,
            'prenom': prenom,
            'email': email,
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
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe'].encode('utf-8')
        motadmin = request.form['mot_de_passe']

        utilisateur = utilisateurs.find_one({'email': email})

        if utilisateur and bcrypt.checkpw(mot_de_passe, utilisateur['mot_de_passe']):
            session['utilisateur_id'] = str(utilisateur['_id'])
            return redirect(url_for('index'))
        elif email == 'admin@admin' and motadmin == 'admin':
            session['admin'] = email
            return redirect(url_for('page_admin'))
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

    candidats=candidat.find()



    return render_template("index.html",candidats=candidats)

@app.route('/list', methods=['GET'])
def liste_candidats():
    candidats = candidat.find()
    return render_template('candidats.html', candidats=candidats)

# Ajouter un nouveau candidat
@app.route('/candidats/nouveau', methods=['GET', 'POST'])
def ajouter_candidat():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        candidat.insert_one({'nom': nom, 'prenom': prenom})
        return redirect(url_for('liste_candidats'))
    else:
        return render_template('ajouterForm.html')

# Modifier un candidat existant
@app.route('/candidats/modifier/<string:candidat_id>', methods=['GET', 'POST'])
def modifier_candidat(candidat_id):
    candidat = candidat.find_one({'_id': ObjectId(candidat_id)})
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        candidat.update_one({'_id': ObjectId(candidat_id)}, {'$set': {'nom': nom, 'prenom': prenom}})
        return redirect(url_for('liste_candidats'))
    else:
        return render_template('modifier_candidat.html', candidat=candidat)

# Supprimer un candidat
@app.route('/candidats/supprimer/<string:candidat_id>', methods=['POST'])
def supprimer_candidat(candidat_id):
    candidat.delete_one({'_id': ObjectId(candidat_id)})
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


        candidat.insert_one(cnd)

        return redirect('ajouter')

    
    return render_template('ajouterform.html')
@app.route('/voter', methods=['POST'])

def voter():
    if request.method == 'POST':
        if est_authentifie():
            nom = request.form['nom']
            prenom = request.form['prenom']
            verdict = request.form['vote']

            # Récupérer l'ID de l'utilisateur à partir de la session
            utilisateur_id = session['utilisateur_id']
            utilisateur = utilisateurs.find_one({'_id': ObjectId(utilisateur_id)})

            # Vérifier si l'utilisateur existe
            if utilisateur:
                # Insérer le vote dans la base de données
                vote.insert_one({'utilisateur_id': utilisateur_id, 'nom': nom, 'prenom': prenom, 'verdict': verdict})
                return 'Votre vote a été enregistré avec succès.'
            else:
                return 'Utilisateur non trouvé.'
        else:
            return 'Vous devez être connecté pour voter.'
    else:
        return 'Méthode non autorisée.'




@app.route('/admin')
def page_admin():
    if 'admin' in session:
        # Récupérer les données que vous souhaitez afficher dans la page d'administration
        # Par exemple, vous pouvez récupérer la liste des utilisateurs, des candidats, etc.
        utilisateurs_data = utilisateurs.find()
        candidats_data = candidat.find()
        candidats_votes = []

        for cand in candidats_data:
            votes_count = vote.count_documents({'utilisateur_id': cand['_id']})
            candidats_votes.append({'nom': cand['nom'], 'prenom': cand['prenom'], 'votes_count': votes_count})


        return render_template('admin.html', utilisateurs=utilisateurs_data, candidats=candidats_data,candidats_votes=candidats_votes)
    else:
        return 'Accès refusé. Vous devez être connecté en tant qu\'administrateur.'

# Dans votre template admin.html, vous pouvez afficher les données récupérées de la base de données





if __name__ =="__main__" :

    app.run(debug=True)