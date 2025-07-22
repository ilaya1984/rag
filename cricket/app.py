from flask import Flask, jsonify, request, render_template
from manager import CricketMatchManager
import uuid

app = Flask(__name__)
matches = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_match', methods=['POST'])
def create_match():
    data = request.json
    match_id = str(uuid.uuid4())
    manager = CricketMatchManager(
        match_id=match_id,
        team_a=data['team1'],
        team_b=data['team2'],
        venue=data.get('venue', ''),
        city=data.get('city', ''),
        ground_type=data.get('ground_type', ''),
        match_type=data.get('match_type', ''),
        overs_limit=int(data.get('total_overs', 5)),
        ball_type=data.get('ball_type', 'leather')
    )
    matches[match_id] = manager
    return jsonify(match_id=match_id, message='Match Created')

@app.route('/api/add_player', methods=['POST'])
def add_player():
    data = request.json
    manager = matches[data['match_id']]
    pid = manager.add_player(data['team'], data['name'])
    return jsonify(player_id=pid)

@app.route('/api/record_toss', methods=['POST'])
def record_toss():
    data = request.json
    manager = matches[data['match_id']]
    manager.record_toss(data['winner'], data['decision'])
    return jsonify(status='ok')

@app.route('/api/create_innings', methods=['POST'])
def create_innings():
    data = request.json
    manager = matches[data['match_id']]
    manager.create_innings(data['innings_key'], data['batting_team'], data['bowling_team'])
    return jsonify(status='ok')

@app.route('/api/set_players', methods=['POST'])
def set_players():
    data = request.json
    manager = matches[data['match_id']]
    manager.set_strikers(data['innings_key'], data['striker'], data['non_striker'])
    manager.start_new_over(data['innings_key'], int(data['over_number']), data['bowler'])
    return jsonify(status='ok')

@app.route('/api/add_score', methods=['POST'])
def add_score():
    data = request.json
    manager = matches[data['match_id']]
    manager.add_score(
        data['innings_key'],
        int(data['runs']),
        extra=data.get('extra'),
        wicket=data.get('wicket'),
        dismissal_type=data.get('dismissal_type')
    )
    return jsonify(status='ok')

@app.route('/api/live_score', methods=['GET'])
def live_score():
    mid = request.args['match_id']
    innings = request.args['innings_key']
    manager = matches[mid]
    return jsonify(manager.get_live_stats(innings))

@app.route('/api/summary', methods=['GET'])
def summary():
    mid = request.args['match_id']
    manager = matches[mid]
    return jsonify(json.loads(manager.to_json()))

if __name__ == '__main__':
    app.run(debug=True)
