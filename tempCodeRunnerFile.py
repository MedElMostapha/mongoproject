    elif(request.form['email']=='admin@admin' and request.form['mot_de_passe'].encode('utf-8')=="admin" ):
            session['admin'] = request.form['email']

            return  redirect(url_for('admin'))