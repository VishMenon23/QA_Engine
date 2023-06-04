from flask import Blueprint,render_template,request,Response
import io
import pandas as pd
import random
import csv
import openai
import os

views = Blueprint(__name__,"views")

openai.api_key = os.environ.get('Api_Key')

def Generate_Questions(num_questions):
    airbnb = pd.read_csv("https://raw.githubusercontent.com/dev7796/data101_tutorial/main/files/dataset/airbnb.csv")

    aggregates = ['min', 'max', 'mean']   # Defining the operations that need to be run on a particular query/question
    attributes = ['price']                # Defining the output feild

    # Defining the attributes that will be used at random to form the query/question
    categorical_attributes = {'room_type': list(set(airbnb['room_type'])),
                            'neighbourhood_group': list(set(airbnb['neighbourhood_group'])),
                            'host_name': list(set(airbnb['host_name'])),
                            'floor': list(set(airbnb['floor'])),
                            'neighbourhood': list(set(airbnb['neighbourhood']))}
    questions = []
    i=0
    c_1=0
    c_2=0
    while(i<num_questions):
        subset_choice = [1,2]
        num_of_subset_conditions = random.choice(subset_choice)
        if(num_of_subset_conditions==1):
            question_template = 'What is the {} {} when {}?'
        elif(num_of_subset_conditions==2):
            question_template = 'What is the {} {} when {} and {}?'  
        # Randomly select an aggregate, attribute, and categorical attribute
        agg = random.choice(aggregates)
        attr = random.choice(attributes)
        cat_attr, cat_val = random.choice(list(categorical_attributes.items()))
        cat_val = random.choice(cat_val)
        answer=""
        question=""
        # Generating the questions using the template and the selected values
        if(num_of_subset_conditions==1):
            question = question_template.format(agg, attr, f"{cat_attr} == '{cat_val}'")
            if(agg=='min'):
                answer = str(airbnb.loc[airbnb[cat_attr] == cat_val, 'price'].min())
            elif(agg=='max'):
                answer = str(airbnb.loc[airbnb[cat_attr] == cat_val, 'price'].max())    
            elif(agg=='mean'):
                answer = str(airbnb.loc[airbnb[cat_attr] == cat_val, 'price'].mean())  
        elif(num_of_subset_conditions==2):
            temp_categorical_attribute=categorical_attributes.copy()
            temp_categorical_attribute.pop(cat_attr)
            temp_cat_attr, temp_cat_val = random.choice(list(temp_categorical_attribute.items()))
            temp_cat_val = random.choice(temp_cat_val)
            question = question_template.format(agg, attr, f"{cat_attr} == '{cat_val}'",f"{temp_cat_attr} == '{temp_cat_val}'")
            #print(question)
            if(agg=='min'):
                answer = str(airbnb.loc[(airbnb[cat_attr] == cat_val) & (airbnb[temp_cat_attr] == temp_cat_val), 'price'].min())
            elif(agg=='max'):
                answer = str(airbnb.loc[(airbnb[cat_attr] == cat_val) & (airbnb[temp_cat_attr] == temp_cat_val), 'price'].max())  
            elif(agg=='mean'):
                answer = str(airbnb.loc[(airbnb[cat_attr] == cat_val) & (airbnb[temp_cat_attr] == temp_cat_val), 'price'].mean())         
        
        if(answer=="nan"):
            #answer = "No Answer for these conditions"
            continue      # Running the iteration again to generate a question that will have an actual answer
        temp = question + " Answer = " + answer    # Concatenation of the Question and answer
        questions.append(temp)
        if(num_of_subset_conditions==1):
            c_1=c_1+1
        elif(num_of_subset_conditions==2):
            c_2=c_2+1
        #print(c_1,c_2)
        i=i+1

    return questions

# Home Page Root
@views.route('/')
def home():
    return render_template('home.html')


@views.route('/gpt', methods=['GET', 'POST'])
def question_page():
    if request.method == 'POST':
        question_type = int(request.form['question_type'])
        question = request.form['question']
        link = request.form['link_ds']
        answer = get_answer(question_type, question, link)
        return render_template('home.html', answer=answer)

    return render_template('home.html')

def get_answer(question_type, question, link):
    answer = ""
    # Coding Question
    if question_type == 1:
        ds_link = pd.read_csv(link)
        column_names = ds_link.columns
        str_col=""
        len=column_names.size
        for i in range(len):
            if(i==len-2):
                str_col+=column_names[i]+" and "
            elif(i==len-1):
                str_col+=column_names[i]    
            else:
                str_col+=column_names[i]+","
        question = "Write code in R to find the " + question +" in the dataset "+link+" with columns " + str_col + ". Return only the R code"
        messages = [{"role": "system", "content": "You are a data scientist who knows the programming language R"}]
        messages.append({"role": "user", "content": question})
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": ChatGPT_reply})
        answer = ChatGPT_reply

    # Text Question 
    if question_type == 2:
        question+=" Make sure the answer is less than 200 words."
        messages = [{"role": "system", "content": "You are a data scientist"}]
        messages.append({"role": "user", "content": question})
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": ChatGPT_reply})
        answer = ChatGPT_reply

    return answer

# Question Generation Root
@views.route('/generate', methods=['POST'])
def generate():
    num_questions = int(request.form['num_questions'])          # Retrieving the number of questions from the user.
    generated_questions = Generate_Questions(num_questions)     # Calling the Generate_Questions funtion to generate 'num_questions' questions
    csv_data = io.StringIO()  
    csv_writer = csv.writer(csv_data)
    for row in generated_questions:
        csv_writer.writerow([row])
    csv_output = csv_data.getvalue()                            # Generating the response CSV which will be downloaded automatically
    
    response = Response(
        csv_output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=Generated_Q&A.csv"}
    ) 
    return response
    