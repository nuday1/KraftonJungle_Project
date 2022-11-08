from flask import Flask, render_template, jsonify, request, redirect, make_response
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone, timedelta
import json
import jwt
import random

SECRET_KEY = 'jungle'

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle

@app.route('/')
def home():
    token_receive = request.cookies.get('token')
    try :
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('index.html', userId=payload["userId"])
    except jwt.ExpiredSignatureError :
        return render_template('login.html')
    except jwt.exceptions.DecodeError :
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def login() :
    # id, pw 받기
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    db_user = db.users.find_one({'userId' : id_receive})

    #일치하는 경우
    if(db_user['pw']==pw_receive) :
        # return jsonify({'result' : 'success', 'userId': id_receive})
        payload = {
            'userId' : id_receive,
            'exp' : datetime.utcnow() + timedelta(minutes=60) #로그인 60분 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        resp = make_response()
        resp.set_cookie('token', token)
        return resp

    else :
        # return render_template('index.html')
        return jsonify({'result' : 'fail'})

@app.route('/sign_up', methods=['POST'])
def sign_up() :
    # 정보 받기
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    name_receive = request.form['name_give']
    phone_receive = request.form['phone_give']
    like_list = []
    hate_list = []
    star_list = []

    if db.users.find_one({'userId':id_receive}) == None :
        new_user = {'userId' : id_receive, 'pw': pw_receive, 'name': name_receive, 'phone':phone_receive, 'likelist':like_list, 'hatelist':hate_list, 'starlist':star_list}
        db.users.insert_one(new_user)
        return jsonify({'result' : 'success'})
    else :
        return jsonify({'result' : 'fail'})
  

@app.route('/main', methods=['POST'])
def show_quests():
    userId_receive = request.form['userId_give']
    sort_receive = request.form['sort_give']

    user = db.users.find_one({'userId':userId_receive}, {'_id':False})
    quest = list(db.quests.find({}, {'_id':False}))
    attList = user['starlist']


    if(sort_receive == '1') :
        quest = list(db.quests.find({}, {'_id':False}).sort('like', 1))
    elif(sort_receive == '2') :
        quest = list(db.quests.find({}, {'_id':False}).sort('hate', 1))
    elif(sort_receive == '3') :
        quest = list(db.quests.find({}, {'_id':False}).sort('star', 1))
    elif(sort_receive == '4') :
        quest = list(db.quests.find({}, {'_id':False}).sort('reward', 1))
    elif(sort_receive == '5') :
        quest = list(db.quests.find({}, {'_id':False}).sort('date', 1))

    # for i in quest :
    #         for j in user['starlist'] :
    #             if i['questId'] == j :
    #                 temp = i
    #                 del i
    #                 quest.append(temp)
    #                 break

    quest.reverse()

    return jsonify({'result': 'success', 'questslist': quest, 'starlist' : attList})

@app.route('/post_quest', methods=['POST'])
def post_quest():
    title_receive=request.form['title_give']
    content_receive=request.form['content_give']
    writer_receive=request.form['writer_give']
    reward_receive=request.form['reward_give']
    like_default = 0
    hate_default = 0
    star_default = 0

    KST = timezone(timedelta(hours=9))
    time_record = datetime.now(KST)
    _day = str(time_record)[:10]
    _time = str(time_record.time())[:8]
    date = _day + " " + _time

    overlap = False
    while not overlap :
        id = title_receive + str(random.randint(0, 9999))
        overlap = db.quests.find({'questId':id})

    writer = db.users.find_one({'userId':writer_receive})
    writer_name = writer['name']
    writer_call = writer['phone']

    quest = {'questId' : id, 'date': date, 'writer' : writer_receive, 'title': title_receive, 'content': content_receive, 'reward' : reward_receive, 'like': like_default, 'hate': hate_default, 'star': star_default,'call' : writer_call,'name':writer_name }
    db.quests.insert_one(quest)

    return jsonify({'result': 'success'})

@app.route('/like', methods=['POST'])
def like() :
    userId_receive = request.form['userId_give']
    questId_receive = request.form['questId_give']
    user = db.users.find_one({'userId':userId_receive})
    quest = db.quests.find_one({'questId':questId_receive})

    overlap = False

    for i in user['likelist'] :
        if i == quest['questId']:
            overlap = True

    if overlap == True :
        temp = list(user['likelist'])
        temp.remove(i)
        db.users.update_one({'userId':userId_receive}, {'$set':{'likelist' :temp}})
        like_down = quest['like'] - 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'like':like_down}})   
    else: 
        temp = list(user['likelist'])
        temp.append(questId_receive)
        db.users.update_one({'userId':userId_receive}, {'$set':{'likelist' :temp}})
        like_up = quest['like'] + 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'like':like_up}})
    return jsonify({'result': 'success'})

@app.route('/hate', methods=['POST'])
def hate() :
    userId_receive = request.form['userId_give']
    questId_receive = request.form['questId_give']
    user = db.users.find_one({'userId':userId_receive})
    quest = db.quests.find_one({'questId':questId_receive})

    overlap = False

    for i in user['hatelist'] :
        if i == quest['questId']:
            overlap = True

    if overlap == True :
        temp = list(user['hatelist'])
        temp.remove(i)
        db.users.update_one({'userId':userId_receive}, {'$set':{'hatelist' :temp}})
        hate_down = quest['hate'] - 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'hate':hate_down}})   
    else: 
        temp = list(user['hatelist'])
        temp.append(questId_receive)
        db.users.update_one({'userId':userId_receive}, {'$set':{'hatelist' :temp}})
        hate_up = quest['hate'] + 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'hate':hate_up}})
    return jsonify({'result': 'success'})

@app.route('/star', methods=['POST'])
def star() :
    userId_receive = request.form['userId_give']
    questId_receive = request.form['questId_give']
    user = db.users.find_one({'userId':userId_receive})
    quest = db.quests.find_one({'questId':questId_receive})

    overlap = False

    for i in user['starlist'] :
        if i == quest['questId']:
            overlap = True

    if overlap == True :
        temp = list(user['starlist'])
        temp.remove(i)
        db.users.update_one({'userId':userId_receive}, {'$set':{'starlist' :temp}})
        star_down = quest['star'] - 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'star':star_down}})   
    else: 
        temp = list(user['starlist'])
        temp.append(questId_receive)
        db.users.update_one({'userId':userId_receive}, {'$set':{'starlist' :temp}})
        star_up = quest['star'] + 1
        db.quests.update_one({'questId':questId_receive},{'$set':{'star':star_up}})
    return jsonify({'result': 'success'})

@app.route('/edit', methods=['POST'])
def edit() :
    questId_receive = request.form['questId_give']
    newtitle_receive = request.form['newtitle_give'] 
    newcontent_receive = request.form['newcontent_give']
    newreward_receive = request.form['newreward_give']
    
    KST = timezone(timedelta(hours=9))
    time_record = datetime.now(KST)
    _day = str(time_record)[:10]
    _time = str(time_record.time())[:8]
    date = _day + " " + _time
 
    db.quests.update_one({'questId':questId_receive},{'$set':{'title':newtitle_receive}})
    db.quests.update_one({'questId':questId_receive},{'$set':{'content':newcontent_receive}})
    db.quests.update_one({'questId':questId_receive},{'$set':{'reward':newreward_receive}})
    db.quests.update_one({'questId':questId_receive},{'$set':{'date':date}})

    return jsonify({'result': 'success'})

@app.route('/delete', methods=['POST'])
def delete() :
    questId_receive = request.form['questId_give']
    db.quests.delete_one({'questId':questId_receive})
    return jsonify({'result': 'success'})

@app.route('/finish', methods=['POST'])
def finish() :
    questId_receive = request.form['questId_give']
    db.quests.delete_one({'questId':questId_receive})
    return jsonify({'result': 'success'})    

if __name__ == '__main__':  
   app.run('0.0.0.0',port=8000,debug=True)