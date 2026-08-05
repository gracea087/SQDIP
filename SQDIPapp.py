from flask import Flask, jsonify, render_template 

import pyodbc 

from waitress import serve 

 

app = Flask(__name__) 

 

# Database connection string 

CONN_STR = ( 

    'DRIVER={ODBC Driver 17 for SQL Server};' 

    'SERVER=localhost\\SQLEXPRESS;' 

    'DATABASE=AppDB;' 

    'Trusted_Connection=yes;' 

) 

 

@app.route('/safety')
def safety():
    return render_template('safety.html')

@app.route('/quality')
def quality():
    return render_template('quality.html')

@app.route('/deliverables')
def deliverables():
    return render_template('deliverables.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/productivity')
def productivity():
    return render_template('productivity.html')

@app.route('/api/products') 

def get_products(): 

    try: 

        conn   = pyodbc.connect(CONN_STR) 

        cursor = conn.cursor() 

        cursor.execute('SELECT ID, Name, Price, Stock FROM Products') 

        rows   = cursor.fetchall() 

        result = [{'id': r[0], 'name': r[1], 

                   'price': float(r[2]), 'stock': r[3]} 

                  for r in rows] 

        conn.close() 

        return jsonify(result) 

    except Exception as e: 

        return jsonify({'error': str(e)}), 500 

 

@app.route('/api/status') 

def status(): 

    return jsonify({'status': 'running', 'server': 'Waitress'}) 

 

if __name__ == '__main__':
    print('Starting SQDIP application on port 5002')
    serve(
        app,
        host='0.0.0.0',
        port=5002,
        threads=8
    )