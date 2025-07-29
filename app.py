from flask import Flask, render_template, request
import sqlite3
import random
from itertools import combinations
from collections import defaultdict
import json

app = Flask(__name__)
DB = 'tournament.db'

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            team_id INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            points INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            goals_for INTEGER DEFAULT 0,
            goals_against INTEGER DEFAULT 0
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1_id INTEGER,
            team2_id INTEGER,
            date TEXT,
            matchday INTEGER,
            team1_goals INTEGER,
            team2_goals INTEGER,
            winner INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')

    conn.commit()
    conn.close()

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_teams_with_members():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT teams.id AS team_id, teams.name AS team_name, players.name AS player_name
        FROM teams
        LEFT JOIN players ON players.team_id = teams.id
        ORDER BY teams.id
    """)
    data = cur.fetchall()

    teams = {}
    for row in data:
        tid = row['team_id']
        if tid not in teams:
            teams[tid] = {
                'name': row['team_name'],
                'players': []
            }
        if row['player_name']:
            teams[tid]['players'].append(row['player_name'])

    return teams.values()

def update_stats(cur, t1, t2, g1, g2):
    def update(team, pts, win, draw, loss, gf, ga):
        cur.execute('''
            UPDATE teams SET points = points + ?, wins = wins + ?, draws = draws + ?, 
            losses = losses + ?, goals_for = goals_for + ?, goals_against = goals_against + ?
            WHERE id = ?
        ''', (pts, win, draw, loss, gf, ga, team))

    if g1 > g2:
        update(t1, 3, 1, 0, 0, g1, g2)
        update(t2, 0, 0, 0, 1, g2, g1)
    elif g2 > g1:
        update(t2, 3, 1, 0, 0, g2, g1)
        update(t1, 0, 0, 0, 1, g1, g2)
    else:
        update(t1, 1, 0, 1, 0, g1, g2)
        update(t2, 1, 0, 1, 0, g2, g1)

def clear_database():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM players")
    cur.execute("DELETE FROM teams")
    cur.execute("DELETE FROM matches")
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def tournament():
    conn = db()
    cur = conn.cursor()

    if request.method == 'POST':
        if 'player_names' in request.form:
            names = request.form['player_names'].split(',')
            for name in [n.strip() for n in names if n.strip()]:
                cur.execute("INSERT INTO players (name) VALUES (?)", (name,))
            conn.commit()

        elif 'remove_player_id' in request.form:
            pid = int(request.form['remove_player_id'])
            cur.execute("DELETE FROM players WHERE id = ?", (pid,))
            conn.commit()

        elif 'clear_teams' in request.form:
            cur.execute("DELETE FROM teams")
            cur.execute("DELETE FROM matches")
            cur.execute("UPDATE players SET team_id = NULL")
            conn.commit()

        elif 'clear_fixtures' in request.form:
            cur.execute("DELETE FROM matches")
            conn.commit()

        elif 'clear_data' in request.form:
            clear_database()

        elif 'form_teams' in request.form:
            cur.execute("DELETE FROM teams")
            cur.execute("DELETE FROM matches")
            cur.execute("UPDATE players SET team_id = NULL")
            conn.commit()

            cur.execute("SELECT id FROM players")
            players = [row[0] for row in cur.fetchall()]
            random.shuffle(players)

            team_number = 1
            i = 0
            while i < len(players) - 1:
                team_name = f"Team {team_number}"
                cur.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
                team_id = cur.lastrowid
                cur.execute("UPDATE players SET team_id = ? WHERE id = ?", (team_id, players[i]))
                cur.execute("UPDATE players SET team_id = ? WHERE id = ?", (team_id, players[i+1]))
                i += 2
                team_number += 1
            if i < len(players):
                team_name = f"Team {team_number}"
                cur.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
                team_id = cur.lastrowid
                cur.execute("UPDATE players SET team_id = ? WHERE id = ?", (team_id, players[i]))
            conn.commit()

        elif 'generate_fixtures' in request.form:
            cur.execute("SELECT id FROM teams")
            team_ids = [row[0] for row in cur.fetchall()]
            matchups = list(combinations(team_ids, 2))
            random.shuffle(matchups)
            matchday = 1
            schedule = []
            matchday_teams = defaultdict(set)

            while matchups:
                current_day_matches = []
                used = set()
                for t1, t2 in matchups[:]:
                    if t1 not in used and t2 not in used:
                        current_day_matches.append((t1, t2))
                        used.add(t1)
                        used.add(t2)
                        matchups.remove((t1, t2))
                for t1, t2 in current_day_matches:
                    cur.execute("INSERT INTO matches (team1_id, team2_id, matchday) VALUES (?, ?, ?)", (t1, t2, matchday))
                matchday += 1

            conn.commit()

        elif 'submit_result' in request.form:
            match_id = int(request.form['match_id'])
            g1 = int(request.form['g1'])
            g2 = int(request.form['g2'])
            cur.execute("SELECT team1_id, team2_id FROM matches WHERE id = ?", (match_id,))
            t1_id, t2_id = cur.fetchone()
            winner = t1_id if g1 > g2 else t2_id if g2 > g1 else None
            cur.execute("""
                UPDATE matches SET team1_goals=?, team2_goals=?, winner=?, status='completed'
                WHERE id=?
            """, (g1, g2, winner, match_id))
            update_stats(cur, t1_id, t2_id, g1, g2)
            conn.commit()

        elif 'updated_teams' in request.form:
            data = json.loads(request.form['updated_teams'])
            cur.execute("SELECT name, id FROM teams")
            team_map = {row['name']: row['id'] for row in cur.fetchall()}
            for team_name, players in data.items():
                team_id = team_map.get(team_name)
                for player in players:
                    cur.execute("UPDATE players SET team_id = ? WHERE name = ?", (team_id, player))
            conn.commit()

    cur.execute("SELECT id, name, team_id FROM players")
    players = cur.fetchall()

    cur.execute("SELECT name, points, wins, draws, losses, goals_for, goals_against FROM teams ORDER BY points DESC, (goals_for - goals_against) DESC")
    points = cur.fetchall()

    cur.execute("""
        SELECT m.id, t1.name as team1, t2.name as team2,
               m.team1_goals, m.team2_goals, m.status, m.matchday
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        ORDER BY m.matchday, m.id
    """)
    rows = cur.fetchall()

    matchdays = defaultdict(list)
    for m in rows:
        matchdays[m['matchday']].append(m)

    teams_with_members = get_teams_with_members()
    return render_template('tournament.html', players=players, matches=matchdays, points=points, teams=teams_with_members)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
