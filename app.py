from flask import Flask, request, render_template, session,redirect
import google.generativeai as genai
import json
from datetime import datetime

gemini_api_key = 'AIzaSyBcJBgB2Th8GcuT0WoKLz4GqwiBZHDtUZ4'
genai.configure(api_key = gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

def insert(file_name,data):
    with open(file_name, 'w') as file:
        json.dump(data,file)
    return True

def fetch(file_name):
    with open(file_name,'r') as file:
        raw = json.load(file)
    return raw

def delete_quiz(url):
    char = str(url[0:1].upper())
    data = fetch(f'db/quiz/quiz_{char}.json')
    data.pop(url)
    insert(f'db/quiz/quiz_{char}.json',data)


    

def add_quiz(url,data):

    with open('db/no.json','r') as file:
        num = int(file.read())

    with open('db/no.json','w') as file:
        file.write(str(num+1))
        
    char = str(url[0:1].upper())

    url = f"{url}-NaradAI-Quiz-{num}"

    raw = fetch(f'db/quiz/quiz_{char}.json')
    
    data['url'] = url
    raw[url] = data

    insert(f'db/quiz/quiz_{char}.json',raw)
    data2 = fetch('db/quiz_meta.json')
    data2.append(url)
    insert('db/quiz_meta.json',data2)
    return url

    
    

def get_quiz(url):
    try:
        char = str(url[0:1].upper())
        return fetch(f'db/quiz/quiz_{char}.json')[url]
    except KeyError:
        return None
    

def create_user(email,name,password,class_):
    data = fetch('db/users/main.json')
    if(email in data):
        return 'Email Already Exit'
    data[email] = {
        'email':email,
        'name':name,
        'password':password,
        'class':class_,
        'quiz':[]
    }
    insert('db/users/main.json',data)
    return f'User created with email - {email}'



def prompt(inp):
    response = model.generate_content(inp)
    data = response.text
    data = data.replace('```','').replace('json','')
    return data


app = Flask(__name__)

app.secret_key = 'krishnasharma'
app.debug = True

@app.route('/')
def home():
   return render_template('index.html')
@app.route('/make-quiz')
def create_quiz():
    return render_template('create.html')
@app.route('/stats/<path>')
def staticss(path):
    data = fetch('db/result.json')
    result = []
    for i in data:
        if(path in i):
            result.append({
                "url":i,
                "username":data[i]['username'],
                "date":data[i]['date'],
                "percent":data[i]['percent']
            })
    return render_template('stats.html',data=result)
@app.route('/old-quiz',methods=['POST','GET'])
def old_quiz():
    if(request.method == 'POST'):
        try:
            data = request.get_json()
            all = data.get('all')
            quiz = []
            for i in json.loads(all):
                if(i != 'result'):
                    quiz.append(i)
            data = []
            for i in quiz:
                try:
                    quiz_data = get_quiz(i)
                    data.append({
                        "title":quiz_data['title'],
                        "subject":quiz_data['subject'],
                        "url":quiz_data['url']
                    })
                except:
                    continue


            
            return json.dumps(data)
        except:
            return "none"
    return render_template('old.html')
@app.route('/result/<url>')

def result(url):
   try:
        data1 = fetch('db/result.json')[url]
        data2 = json.dumps(data1)

        percent = float(data1['percent'])
        color = 'rgb(60, 196, 52);'
        tag = 'Wow! You are Brilliant!'
        if(percent<40):
            color = 'red'
            tag = 'Going good! Keep it up!'
        if(percent>40 and percent < 80):
            color = 'rgb(255, 89, 0);'
            tag = 'Keep your chin up, better luck next time!'

        database = json.dumps(get_quiz(data1['url']))
        return render_template('result.html',data=database,username=data1['username'],percent=percent,color=color,tag=tag,ans=data1['ans'],correct=data1['correct'],questions = str(len(data1['ans'])),url=url)
   except:
       pass
       return redirect('/')
@app.route('/result_set',methods=['POST'])
def result_set():
    data = request.get_json()

    percent = data.get('percent')
    correct = data.get('correct')
    ans = data.get('ans')
    url = data.get('url')
    username = data.get('username')

    js_data = fetch('db/result.json')
    current_date = datetime.now()

    formatted_date = current_date.strftime("%d %b")
    new_url = f'{url}--{current_date}'
    js_data[new_url] = {
        'percent':percent,
        'correct':correct,
        'ans':ans,
        'username':username,
        'url':url,
        'date':formatted_date
    }
    insert('db/result.json',js_data)
    return new_url


@app.route('/q/<m>')
def qui_p(m):
   if('local' not in m):
    data = get_quiz(m)
    title = data['title']
    dec = data['description']
    keywords = str(data['seo_keywords']).replace('[','').replace(']','')
    return render_template('quiz.html',url=m,title=title,dec=dec,keywords=keywords)
   if('local' in m):
       return render_template('quiz.html',url=m)
@app.route('/<m>/quiz.js')
def quizjs(m):
   data = json.dumps(get_quiz(m))
   types = None
   if('local' in m):
       types = 'local'
   if(data == None and 'local' not in m):
       return 'Not Found'
   user = 'null'
   if 'email' in session:
       user = session['email']
   return render_template('quiz.js',data=data,user=user,types=types,url=m)

@app.route('/make')
def make():
  level = request.args.get('level')
  chapter = request.args.get('chapter')
  subject = request.args.get('subject')
  questions = request.args.get('question')


  if(level and subject and questions == ''):
     return
  m = ''
  i = 0

  while f'"{questions}":' not in m:
    i = i+1
    print(i)
     
  
    m = prompt("""Write """ + questions + """ Questions. Level of hardity """ + level + '% Hard' + """ and """ + subject + """ subject and chapter - """ + chapter + """in this json formate don't miss anythings and make sure the answer are not too long it must be 8-10 words or there must be only 4 option.
example - "{
    "1": {
        "1": "second",
        "2": "m/s^2",
        "3": "hour",
        "4": "day",
        "Q": "What is the SI unit of time?",
        "ans": "second"
    },
    "2": {
        "1": "meter",
        "2": "kilometer",
        "3": "centimeter",
        "4": "mile",
        "Q": "What is the SI unit of distance?",
        "ans": "meter"
    },
    "all": 2,
    "title": "MCQ Class 9 Science Chapter 1 States of Matter",
    "subject": "Chemisitry",
    "seo_keywords": [
        "chemisitry",
        "class 9",
        "matter",
        "mcq",
        "chapter 1"
    ],
    "url": "science-chapter-1-matter-in-our-surrounding",
    "description": "Class 9 chemistry MCQs with answers are provided here for chapter 1 Matter in Our Surroundings. These MCQs are based on CBSE board curriculum and correspond to the most recent Class 9 chemistry syllabus."
}"
Don't use '/' in url only use alphabate and -             
I want same to same formate of json and make sure """ + questions +""" questions are present. Make sure the json is valid. Make sure the answer will be in the option.
                  """)
    try:
        m = json.loads(m)
        break
    except:
        continue

  url = add_quiz(m['url'],m)
  m['url'] = url
  m = json.dumps(m)
  return f'{m}'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
