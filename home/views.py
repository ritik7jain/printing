import json
from django.shortcuts import render, HttpResponse,redirect
from django.http import HttpResponseRedirect
import pyrebase
import os
import PyPDF2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import datetime
import uuid
from django.conf import settings
import re
from django.http import JsonResponse

#ritik_testing
#remote
current_dir = os.path.dirname(os.path.abspath(__file__))
service_account_path = os.path.join(current_dir, 'matchinghearts-44d68-firebase-adminsdk-1siaw-f0a3f4a837.json')
config={
  'apiKey': "AIzaSyAjDLuEFgYrACJETN14FaVmjxI6CUp4E5E",
  'authDomain': "matchinghearts-44d68.firebaseapp.com",
  'databaseURL': "https://matchinghearts-44d68-default-rtdb.firebaseio.com",
  'projectId': "matchinghearts-44d68",
  'storageBucket': "matchinghearts-44d68.appspot.com",
  'messagingSenderId': "929519272659",
  'appId': "1:929519272659:web:b260a13e34180a6d4aca26",
  'measurementId': "G-TGZ6DB4BRN",
  'serviceAccount': service_account_path
}



cred = credentials.Certificate(service_account_path)
try:
    app = firebase_admin.get_app()
except:
    firebase_admin.initialize_app(cred,options={
    'storageBucket': 'matchinghearts-44d68.appspot.com',
})
db = firestore.client()
bucket = storage.bucket() 


firebase=pyrebase.initialize_app(config)
authe = firebase.auth()
database=firebase.database()


def signIn(request):
    if request.method=='POST':
        email=request.POST.get('email')
        pasw=request.POST.get('pass')
        print(email)
        print(pasw)
        try:
            user=authe.sign_in_with_email_and_password(email,pasw)
        except:
            message="Invalid Credentials!!Please ChecK your Data"
            return render(request,"login.html",{"message":message})
        uid = user['localId'] 
        request.session['uid'] = uid 
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get().to_dict()
        return render(request,'index.html',{'user_data':user_data})
        # return render(request, "Home.html", {'user_data': user_data})    
    return render(request,"login.html")


def admin_login(request):
    if request.method=='POST':
        email=request.POST.get('email')
        pasw=request.POST.get('pass')
        try:
            user =authe.sign_in_with_email_and_password(email,pasw)
        except:
            message="Invalid Admin credentials"
            return render(request,"admin_login.html",{"message":message})
        if(email=="jritik@gmail.com"):
            uid = user['localId']
            request.session['uid'] = uid 
            users_ref = db.collection('users')
            users = users_ref.get()
            user_data = []
            for user in users:
                user_data.append(user.to_dict())
            print(user_data)
            return render(request, "admin_home.html", {'users': user_data, 'email':email})
        else:
            message="Invalid Admin credentials"
            return render(request,"admin_login.html",{"message":message})
    else:  
        return render(request, "admin_login.html")


def admin_home(request):
    if request.method == "POST":
        user_uid = request.POST.get('user_uid')
        order_id = request.POST.get('order_id')
        order_accept= request.POST.get('order_accept','')
        delivery_date = request.POST.get('delivery_date', '')
        order_deliver=request.POST.get('order_deliver', '')
        user_data = db.collection('users').document(user_uid)
        if user_data:
            if order_accept:
                user_data.update({
                        f'orders.{order_id}.order_accepted': True,
                    })
                user_data.update({
                        f'orders.{order_id}.order_accepted_date':datetime.datetime.now().strftime('%Y-%m-%d')
                    })
            if delivery_date:
                user_data.update({
                       f'orders.{order_id}.delivery_date': delivery_date,
                })
            if order_deliver:
                user_data.update({
                        f'orders.{order_id}.delivered': True,
                    })
        users_ref = db.collection('users')
        users = users_ref.get()
        user_data = []
        for user in users:
            user_data.append(user.to_dict())
        return render(request, "admin_home.html", {'users': user_data})

    else:
        if 'uid' in request.session and request.session['uid']=='yLWR0bmUj3e4KeGnQDDqGBFzjt92':
            users_ref = db.collection('users')
            users = users_ref.get()
            user_data = []
            for user in users:
                user_data.append(user.to_dict())
            return render(request, "admin_home.html", {'users': user_data})
        return redirect('/admin_login/')
    
def index(request):
    if 'uid' in request.session:
        uid = request.session['uid']
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get().to_dict()
        if user_data:
            return render(request, "index.html", {'user_data': user_data})
    return redirect('/')

def upload_pdf(request):
    if request.method == 'POST':
        print("1")
        if "pdf_file" in request.FILES:
            order_type=request.POST.get('order_type')
            pdf_file = request.FILES['pdf_file']
            cost=request.POST.get('cost')
            max_file_size = settings.MAX_FILE_SIZE
            if pdf_file.size > max_file_size:
                error_message = "File size exceeds the limit."
                return render(request, "upload_pdf.html", {'message': error_message}) 
            uid = request.session.get('uid')
            file_name = f"user_{uid}/{pdf_file.name}"
            blob = bucket.blob(file_name)
            blob.upload_from_file(pdf_file)
            file_url = blob.generate_signed_url(datetime.timedelta(days=7), method='GET')
            user_ref = db.collection('users').document(uid)
            user_data = user_ref.get().to_dict()
            current_orders = user_data.get('orders', {})
            order_id = str(uuid.uuid4())[:18]
            order_id = re.sub(r'[^a-zA-Z0-9]', '', order_id)
            order = {
                'order_type': order_type,
                'pdf_files': [],
                'order_placed': False,
                'order_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'cost': 0,
                'order_accepted': False,
                'delivery_date': "",
                'delivered': False
            }
            current_orders[order_id] = order
            current_files = order.get('pdf_files', [])
            current_files.append({'name': pdf_file.name, 'url': file_url})
            order['pdf_files'] = current_files
            order['order_placed'] = True
            order['cost']=cost
            user_ref.update({'orders': current_orders})
        return render(request, "index.html",{'user_data': user_data})
    else:    
        print("2")
        if 'uid' in request.session:
            uid = request.session['uid']
            user_ref = db.collection('users').document(uid)
            user_data = user_ref.get().to_dict()
            if user_data:
                return render(request, "upload_pdf.html", {'user_data': user_data})
        return redirect('/')


def services(request):
    print(request.session)
    if 'uid' in request.session:
        uid = request.session['uid']
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get().to_dict()
        if user_data:
            return render(request, "printout.html", {'user_data': user_data})
    return redirect('/')


def home(request):
        if request.method == 'POST':
            if 'pdf_file' in request.FILES:
                order_type=request.POST.get('order_type')
                pdf_file = request.FILES['pdf_file']
                max_file_size = settings.MAX_FILE_SIZE
                if pdf_file.size > max_file_size:
                    error_message = "File size exceeds the limit."
                    return render(request, "upload_pdf.html", {'message': error_message}) 
                uid = request.session.get('uid')
                file_name = f"user_{uid}/{pdf_file.name}"
                blob = bucket.blob(file_name)
                blob.upload_from_file(pdf_file)
                file_url = blob.generate_signed_url(datetime.timedelta(days=7), method='GET')
                reader = PyPDF2.PdfReader(pdf_file)
                number_of_pages = len(reader.pages)
                if(not request.POST.get('cost')):
                    user_ref = db.collection('users').document(uid)
                    user_data = user_ref.get().to_dict()
                    current_orders = user_data.get('orders', {})
                    order_id = str(uuid.uuid4())
                    order = {
                        'order_type': order_type,
                        'pdf_files': [],
                        'order_placed': False,
                        'order_accepted_date':"",
                        'cost': 0,
                        'order_accepted': False,
                        'delivery_date': "",
                        'delivered': False
                    }
                    current_orders[order_id] = order

                    current_files = order.get('pdf_files', [])
                    current_files.append({'name': pdf_file.name, 'url': file_url})
                    order['pdf_files'] = current_files
                    order['order_placed'] = True

                    if order_type == 'spiral':
                        order['cost'] = (number_of_pages * 1.5) + 30
                    else:
                        order['cost'] = (number_of_pages * 1.5) + 80

                    user_ref.update({'orders': current_orders})

                    return render(request, "Home.html", {'user_data': user_data})
                else:
                    if order_type == 'spiral':
                       cost = (number_of_pages * 1.5) + 30
                    else:
                       cost = (number_of_pages * 1.5) + 80
                    
                    return render(request, "Home.html", {'cost': cost})
                    
            else:
                error_message = "No file selected. Please choose a PDF file to upload."
                return render(request, "Home.html", {'error_message': error_message})
        else:
            if 'uid' in request.session:
                uid = request.session['uid']
                user_ref = db.collection('users').document(uid)
                user_data = user_ref.get().to_dict()
                if user_data:
                    return render(request, "Home.html", {'user_data': user_data})
            return redirect('/')

def orders(request):
    print(request.session)
    if 'uid' in request.session:
        uid = request.session.get('uid')
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get().to_dict()
        if user_data:
            current_orders = user_data.get('orders', {})
            current_orders = dict(sorted(current_orders.items(), key=lambda x: x[1]['order_date'], reverse=True))
            return render(request,"orders.html",{'orders':current_orders})
           
        else:
            return redirect('/')
    return redirect('/')

def faqs(request):
    if 'uid' in request.session:
        return render(request,"faqs.html")
    return redirect('/')
 
def logout(request):
    try:
        del request.session['uid']
        print("yes")
        return redirect('/')  
    except:
        pass
    return redirect('/')


def order_detail(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        uid = request.session.get('uid')
        user_ref = db.collection('users').document(uid)
        user_data = user_ref.get().to_dict()
        order= user_data.get('orders', {})
        current_order=order[order_id]
        print(current_order)
        return JsonResponse(current_order, safe=False)
        # return render(request,"index.html", {'order_data': current_order})
    else:
        return render(request, 'order_details.html')


def signUp(request):
    if request.method=='POST':
        email = request.POST.get('email')
        pasw = request.POST.get('pass')
        name = request.POST.get('name')
        phone_number= request.POST.get('phone_number')
        try:
            user=authe.create_user_with_email_and_password(email,pasw)
            print(user)
            uid = user['localId']
            user_data = {
                'uid': uid,
                'username': name,
                'email': email,
                'phone_number':phone_number,
                'orders': {
                    
                }
            }
            db.collection('users').document(uid).set(user_data)
            return redirect('/')
        except:
            return render(request, "Registration.html")
    return render(request,"Registration.html")
 

def reset(request):
    if request.method=='POST':
        email = request.POST.get('email')
        try:
            authe.send_password_reset_email(email)
            message = "A email to reset password is successfully sent"
            return render(request, "reset.html", {"msg":message})
        except:
            message = "Something went wrong, Please check the email you provided is registered or not"
            return render(request, "reset.html", {"msg":message})
    return render(request, "reset.html")


def contact(request):
    if 'uid' in request.session:
        return render(request,"contact.html") 
    return redirect('/') 































# def postReset(request):
# 	email = request.POST.get('email')
# 	try:
# 		authe.send_password_reset_email(email)
# 		message = "A email to reset password is successfully sent"
# 		return render(request, "reset.html", {"msg":message})
# 	except:
# 		message = "Something went wrong, Please check the email you provided is registered or not"
# 		return render(request, "reset.html", {"msg":message})
# def postsignUp(request):
#      email = request.POST.get('email')
#      passs = request.POST.get('pass')
#      name = request.POST.get('name')
#      try:
#         user=authe.create_user_with_email_and_password(email,passs)
#         uid = user['localId']
#         idtoken = request.session['uid']
#         print(uid)
#         return redirect('/')
#      except:
#         return render(request, "Registration.html")
#      return redirect('/')
# def postsignIn(request):
#     email=request.POST.get('email')
#     pasw=request.POST.get('pass')
#     try:
#         user=authe.sign_in_with_email_and_password(email,pasw)
#     except:
#         message="Invalid Credentials!!Please ChecK your Data"
#         return render(request,"login.html",{"message":message})
#     session_id=user['idToken']
#     request.session['uid']=str(session_id)
#     return render(request,"Home.html",{"email":email})
