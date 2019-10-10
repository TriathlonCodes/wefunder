import pymysql
from .db import config
# from mysql import connector

from flask import Flask, url_for, render_template, request
app = Flask(__name__)

import collections



connection = pymysql.connect(host='localhost',
                             user='test',
                             password='password',
                             db='wefunder',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

class Match(collections.namedtuple('Match', 'match_id, user_1_id, user_2_id, winner_id')):
    pass

powers_of_2 = [1, 2,4,8,16,32,64]

@app.route('/')
def render():
    ### TODO: we're basically just re-rendering this entire page
    ###
    with connection.cursor() as cursor:
        sql = 'SELECT * FROM matches;'
        cursor.execute(sql)
        matches = cursor.fetchall()
    matches_by_round = collections.defaultdict(list)
    for match in matches:
        matches_by_round[match['round_id']].append(match)
    return render_template('index.html', rounds=matches_by_round)

# post
@app.route('/add_users', methods=['POST'])
def add_users():
    user_list = request.form['user_list']
    # user_list = '4,7,6,7'
    clensed_user_list = ["\"%s\"" % user for user in user_list.split(',')]
    users = [
        '({})'.format(name) for name in clensed_user_list
    ]
    with connection.cursor() as cursor:
        sql = 'INSERT into users (name) values %s; ' % ', '.join(users)
        # print(sql)
        cursor.execute(sql)
        sql = 'SELECT * FROM matches;'
        cursor.execute(sql)
        matches = cursor.fetchall()
    connection.commit()

    matches_by_round = collections.defaultdict(list)
    for match in matches:
        matches_by_round[match['round_id']].append(match)
    return render_template('index.html', rounds=matches_by_round)


# post
@app.route('/generate', methods=['POST'])
def generate_matches():
    new = request.form['new']
    last_round = request.form.get('last_round')
    # create round
    with connection.cursor() as cursor:
        if new == "true":
            # print("hi!!!")
            sql = 'SELECT * FROM users'
            cursor.execute(sql)
            users = cursor.fetchall()
            winner_ids = [user['user_id'] for user in users]
        else:

            sql = 'SELECT * from matches where round_id = %s' % last_round
            cursor.execute(sql)
            matches = cursor.fetchall()

            winner_ids = [match['winner_id'] for match in matches]
        # new round
        sql = 'INSERT INTO rounds () values ()'
        cursor.execute(sql)

        sql = 'SELECT * from rounds ORDER BY round_id DESC LIMIT 1;'
        cursor.execute(sql)
        new_round = cursor.fetchone()

        # print("winner_ids")
        # print(winner_ids)
        num_matches = None
        for i, power in enumerate(powers_of_2):
            if power >= len(winner_ids) / 2:
                num_matches = power
                break

        if i:
            num_empty = len(winner_ids) % i
        else:
            num_empty = 0
        num_pairs = int((len(winner_ids) - num_empty)/2)
        # print(num_empty)

        empty_matches = winner_ids[:num_empty]
        paired_matches = winner_ids[num_empty:]
        matches = [
            '({user_id}, {user_id}, {user_id}, {new_round})'.format(
                user_id=user_id, new_round=new_round['round_id'])
            for user_id in empty_matches
        ]

        for n in range(int(num_pairs)):

            matches.append(
                '({user_id1}, {user_id2}, NULL, {new_round})'.format(
                    user_id1=winner_ids[n],
                    user_id2=paired_matches[int(n + num_pairs)],
                    new_round=new_round['round_id'])
                )

        sql = 'INSERT into matches (user_1_id, user_2_id, winner_id, round_id) values %s' % ', '.join(matches)
        # print(sql)

        cursor.execute(sql)
    connection.commit()

    with connection.cursor() as cursor:
        sql = 'SELECT * FROM matches;'
        cursor.execute(sql)
        matches = cursor.fetchall()
    matches_by_round = collections.defaultdict(list)
    for match in matches:
        matches_by_round[match['round_id']].append(match)
    return render_template('index.html', rounds=matches_by_round)

@app.route('/play', methods=['POST'])
def play_match():
    winner_id = request.form['winner_id']
    match_id = request.form['match_id']
    sql = 'UPDATE matches SET winner_id = %d where match_id = %d' % (int(winner_id), int(match_id))

    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.commit()

    with connection.cursor() as cursor:
        sql = 'SELECT * FROM matches;'
        cursor.execute(sql)
        matches = cursor.fetchall()
    matches_by_round = collections.defaultdict(list)
    for match in matches:
        matches_by_round[match['round_id']].append(match)
    return render_template('index.html', rounds=matches_by_round)
