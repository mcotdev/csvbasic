from flask import Flask, request, jsonify, g, render_template, redirect, url_for, send_file, Response
import sqlite3
import pandas as pd
import io

app = Flask(__name__)
DATABASE = 'data.db'

def connect_db():
    return sqlite3.connect(DATABASE)

def init_db():
    with connect_db() as db:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS csv_files (
                            id INTEGER PRIMARY KEY,
                            csv_filename TEXT,
                            description TEXT,
                            csv_file BLOB,
                            csv_raw TEXT
                         )''')
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        
        file_content = file.read()
        file_content_str = file_content.decode("utf-8")

        description = request.form.get('description', 'No description provided')
        data = (file.filename, description, file_content, file_content_str)
        
        g.db.execute('INSERT INTO csv_files (csv_filename, description, csv_file, csv_raw) VALUES (?,?,?,?)', data)
        g.db.commit()
        
        return redirect(url_for('list_files'))
    return render_template('upload.html')

@app.route('/files')
def list_files():
    cursor = g.db.execute('SELECT id, csv_filename, description FROM csv_files')
    files = [{'id': row[0], 'csv_filename': row[1], 'description': row[2]} for row in cursor.fetchall()]
    return render_template('list.html', files=files)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        description = request.form.get('description')
        g.db.execute('UPDATE csv_files SET description =? WHERE id =?', (description, id))
        g.db.commit()
        return redirect(url_for('list_files'))
    else:
        cursor = g.db.execute('SELECT id, csv_filename, description FROM csv_files WHERE id =?', (id,))
        file_info = cursor.fetchone()
        if file_info:
            file = {'id': id, 'csv_filename': file_info[1], 'description': file_info[2]}
        else:
            return "File not found!", 404
        return render_template('edit.html', file=file)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    g.db.execute('DELETE FROM csv_files WHERE id =?', (id,))
    g.db.commit()
    return redirect(url_for('list_files'))

@app.route('/view_raw/<int:id>')
def view_raw(id):
    cursor = g.db.execute('SELECT csv_raw FROM csv_files WHERE id =?', (id,))
    file_info = cursor.fetchone()
    if file_info:
        return Response(file_info[0], mimetype='text/plain')
    else:
        return "File not found!", 404

@app.route('/download_csv/<int:id>')
def download_csv(id):
    cursor = g.db.execute('SELECT csv_filename, csv_file FROM csv_files WHERE id =?', (id,))
    file_info = cursor.fetchone()
    if file_info:
        return send_file(io.BytesIO(file_info[1]), mimetype='text/csv', as_attachment=True, download_name=file_info[0])
    else:
        return "File not found!", 404

@app.route('/convert_to_parquet/<int:id>')
def convert_to_parquet(id):
    cursor = g.db.execute('SELECT csv_filename, csv_raw FROM csv_files WHERE id =?', (id,))
    file_info = cursor.fetchone()
    if file_info:
        csv_raw = file_info[1]
        # Convert CSV to Parquet
        df = pd.read_csv(io.StringIO(csv_raw))
        parquet_buf = io.BytesIO()
        df.to_parquet(parquet_buf, index=False)
        parquet_buf.seek(0)
        return send_file(parquet_buf, mimetype='application/octet-stream', as_attachment=True, download_name=f"{file_info[0].split('.')[0]}.parquet")
    else:
        return "File not found!", 404

@app.route('/view_parquet/<int:id>')
def view_parquet(id):
    cursor = g.db.execute('SELECT csv_raw FROM csv_files WHERE id =?', (id,))
    file_info = cursor.fetchone()
    if file_info:
        csv_raw = file_info[0]
        # Convert CSV to DataFrame
        df = pd.read_csv(io.StringIO(csv_raw))
        # Convert DataFrame to HTML
        html_table = df.to_html(classes='table table-striped')
        return render_template('view_parquet.html', table=html_table)
    else:
        return "File not found!", 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5010)