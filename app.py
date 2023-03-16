from flask import Flask, request, jsonify, render_template, redirect, send_from_directory
import requests
import os
from os import path
from sense_hat import SenseHat
import sqlite3 


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

sense = SenseHat()

with sqlite3.connect('messages.db') as connection:
    c = connection.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, message TEXT, datetime TEXT, author TEXT)')

    # create TABLE if not exists for hosts table with id, hostname and port
    c.execute('CREATE TABLE IF NOT EXISTS hosts(id INTEGER PRIMARY KEY, hostname TEXT, port TEXT)')

# API for Sense HAT messages

# create GET endpoint to retrieve all messages from database
@app.route('/get_messages', methods=['GET'])
def get_messages():
    if request.method == 'GET':
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute('SELECT * FROM messages')
            messages = c.fetchall()
            # return json response with OK status
            return jsonify({'status': 'OK', 'messages': messages})
        
# create GET endpoint to retrieve all hosts from database
@app.route('/get_hosts', methods=['GET'])
def get_hosts():
    if request.method == 'GET':
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute('SELECT * FROM hosts')
            hosts = c.fetchall()
            # return json response with OK status
            return jsonify({'status': 'OK', 'hosts': hosts})

# create POST endpoint to receive data and set LED matrix on sense hat to show message
@app.route('/set_message', methods=['POST'])
def set_message():
    if request.method == 'POST':
        message = request.json['message']
        color = request.json['color']
        author = request.json['author']
        sense.show_message(message, 0.1, color)
        msg_data = (message, author)
        with sqlite3.connect('messages.db') as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO messages(message, datetime, author) VALUES(?, datetime('now','localtime'), ?)", msg_data)
        # return json response with OK status
        return jsonify({'status': 'Message set', 'color': color, 'message': message, 'author': author})

# create UPDATE endpoint to update message based on id
@app.route('/update_message', methods=['UPDATE'])
def update_message():
    if request.method == 'UPDATE':
        id = request.json['id']
        message = request.json['message']
        data = (message, id)
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute('UPDATE messages SET message=? WHERE id=?', data)
        # return json response with OK status
        return jsonify({'status': 'Message updated'})

# create DELETE endpoint to delete a message in the database based on primary key
@app.route('/delete_message', methods=['DELETE'])
def delete_message():
    if request.method == 'DELETE':
        id = request.json['id']
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute('DELETE FROM messages WHERE id=?', (id,))
        # return json response with OK status
        return jsonify({'status': 'Message deleted'})

# create POST endpoint to receive JSON data from HTTP POST request and set LED matrix on sense hat
@app.route('/set_heart', methods=['POST'])
def set_heart():
    if request.method == 'POST':
        r = request.json['color']
        k = [0, 0, 0]
        sense.set_pixels([
            k, r, r, k, k, r, r, k, 
            r, r, r, r, r, r, r, r, 
            r, r, r, r, r, r, r, r, 
            r, r, r, r, r, r, r, r, 
            r, r, r, r, r, r, r, r, 
            k, r, r, r, r, r, r, k, 
            k, k, r, r, r, r, k, k, 
            k, k, k, r, r, k, k, k
        ])
        # return json response with OK status
        return jsonify({'status': 'Heart set', 'color': r})

# create POST endpoint to receive JSON data from HTTP POST request and set LED matrix on sense hat
@app.route('/set_smiley', methods=['POST'])
def set_smiley():
    if request.method == 'POST':
        mood = request.json['mood']
        X = request.json['color']
        O = [0, 0, 0]
        if mood == "happy":
            sense.set_pixels([
            O, O, O, O, O, O, O, O,
            O, X, X, O, O, X, X, O,
            O, X, X, O, O, X, X, O,
            O, O, O, O, O, O, O, O,
            X, X, O, O, O, O, X, X,
            X, X, X, X, X, X, X, X,
            O, X, X, X, X, X, X, O,
            O, O, O, O, O, O, O, O])
            # return json response with OK status
            return jsonify({'status': 'Smiley set', 'mood': mood})

        elif mood == "sad":
            sense.set_pixels([
            O, O, O, O, O, O, O, O,
            O, X, X, O, O, X, X, O,
            O, X, X, O, O, X, X, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, X, X, X, X, X, X, O,
            X, X, X, X, X, X, X, X,
            X, X, O, O, O, O, X, X])
            # return json response with OK status
            return jsonify({'status': 'Smiley set', 'mood': mood})

# create POST endpoint to receive JSON data from HTTP POST request and set LED matrix on sense hat
@app.route('/clear', methods=['POST'])
def clear():
    if request.method == 'POST':
        sense.clear()
        # return json response with OK status
        return jsonify({'status': 'Display cleared'})


# Web site

# create a route for the default page, which loads index.html
@app.route('/')
def index():
    url = request.host
    messages = requests.get('http://' + url + '/get_messages').json()
    hosts = requests.get('http://' + url + '/get_hosts').json()
    return render_template('index.html', url=url, messages=messages, hosts=hosts)

# create POST route to add host to database
@app.route('/add_host', methods=['POST'])
def add_host():
    if request.method == 'POST':
        hostname = request.form['hostname']
        port = request.form['port']
        host_data = (hostname, port)
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute("INSERT INTO hosts (hostname, port) VALUES (?, ?)", host_data)
        # return json response with OK status
        return redirect('/')

# delete host from database
@app.route('/delete_host', methods=['POST'])
def delete_host():
    if request.method == 'POST':
        id = request.form['id']
        with sqlite3.connect('messages.db') as connection:
            c = connection.cursor()
            c.execute('DELETE FROM hosts WHERE id=?', (id,))
        return redirect('/')

# create post route to send message to pi4
@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        author = request.form['author']
        message = request.form['message']
        host = request.form['host']
        color = [int(request.form['color1']), int(request.form['color2']), int(request.form['color3'])]
        requests.post('http://' + host + '/set_message', json={'message': message, 'author': author, 'color': color})
        return redirect('/')

# create post route to send heart to host
@app.route('/send_heart', methods=['POST'])
def send_heart():
    if request.method == 'POST':
        host = request.form['host']
        color = [int(request.form['color1']), int(request.form['color2']), int(request.form['color3'])]
        requests.post('http://' + host + '/set_heart', json={'color': color})
        return redirect('/')

# create post route to send smiley to host with mood happy or sad and color
@app.route('/send_smiley', methods=['POST'])
def send_smiley():
    if request.method == 'POST':
        host = request.form['host']
        mood = request.form['mood']
        color = [int(request.form['color1']), int(request.form['color2']), int(request.form['color3'])]
        requests.post('http://' + host + '/set_smiley', json={'mood': mood, 'color': color})
        return redirect('/')

# app route to clear display for host
@app.route('/set_clear', methods=['POST'])
def clear_host():
    if request.method == 'POST':
        host = request.form['host']
        try:
            requests.post('http://' + host + '/clear')
            return redirect('/')
        except Exception as e:
            return {'status': 'Failed', 'error': str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
