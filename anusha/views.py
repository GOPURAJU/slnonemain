from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from .forms import *
import logging
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate,logout
from django.http import HttpResponse,HttpResponseBadRequest,HttpResponseRedirect
from django.contrib import auth
from django.urls import reverse

from ravi.models import *
from business.models import *
from bhanu.models import *
from bhanu.forms import *
from business.forms import *
from seetha.models import CarLoan
from ganesh.models import CreditDetail

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def Login(request):
    if request.method == 'POST':#IF THE CONDITION IS TRUE IT SHOULD ENTER INTO THE IF CONDITION
       username = request.POST['username'] 
       password = request.POST['password']  

       user = auth.authenticate(username=username,password=password)
       if user is not None:
           auth.login(request, user)
           print('login is successfully')
           return redirect('dashboard')
       else:
           print('invalid credentials')
           return redirect('login')
    else:
        return render(request,'customer/login.html')


# =================================goldloan start===================================

import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"



def goldbasicdetails(request,instance_id=None):
    instance = get_object_or_404(goldbasicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = goldBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            destinationUrl=reverse('goldloan')
            request.session['Goldafterurl']=destinationUrl
            request.session['goldAppliId']=True
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            request.session['mobile_number']=user_details.phone_number
            
            payload = {
                "apiid": APIID,
                "token": TOKEN,
                "methodName": "UATCreditScoreOTP",
                "orderid": orderid,
                "phone_number": user_details.phone_number
            }

            response = requests.post("https://apimanage.websoftexpay.com/api/Uat_creditscore_OTP.aspx", json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('goldfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = BasicDetailForm()

    return render(request, 'customer/goldbasicdetail.html', {'form': form})
def gold_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = goldbasicdetailform.objects.get(id=user_id)
        otp = request.POST.get('otp').strip()  
        print(f'otp is:{otp}')
        payload = {
            "apiid": APIID,
            "token": TOKEN,
            "methodName": "UATcreditscore",
            "orderid": request.session.get('orderid'),  
            "fname": user_details.fname,
            "lname": user_details.lname,
            "Dob": user_details.Dob.isoformat() if isinstance(user_details.Dob, date) else user_details.Dob,
            "phone_number": user_details.phone_number,
            "pan_num": user_details.pan_num,
            "application_id":user_details.application_id,
            "otp": otp 
            
        }
        
        response = requests.post("https://apimanage.websoftexpay.com/api/Uat_credit_score.aspx", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                if 'Dob' in data["data"]:
                    dob = data["data"]['Dob']
                    if isinstance(dob, date):
                        data["data"]['Dob'] = dob.isoformat()
                credit_score = data["data"].get("ScoreValue")
                
                if credit_score:
                    loan_application = Goldloanapplication.objects.filter(goldbasicdetail=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'customer/goldcibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'customer/goldbasicdetail.html',{'otp':otp})



 
 
def goldloanapplication(request):
    mobile_number = request.session.get('mobile_number')  
    
     # Bhanu
    refCode=None
    francrefCode=None
    if request.GET.get('refCode'):
        print(request.GET.get('refCode'))
        refCode=request.GET.get('refCode')
    if request.GET.get('franrefCode'):
       francrefCode=request.GET.get('franrefCode')
    # Bhanu

    if request.method == 'POST':
        form = goldform(request.POST, request.FILES)
        if form.is_valid():
            loan = form.save(commit=False)
            
             # Bhanu
    
            if refCode:
              if refCode.startswith('SLNDSA'):
                 loan.dsaref_code=refCode
                 loan.franrefCode=francrefCode
              elif refCode.startswith('SLNEMP'):
                 loan.empref_code=refCode
                 loan.franrefCode=francrefCode
            else:
                 loan.franrefCode=francrefCode

            # Bhanu
            
            try:
                if mobile_number:
                    mobile_number_int = int(mobile_number)
                else:
                    print("Mobile number is not found in session.")  
                    return redirect('basicdetail')

                print("Attempting to find basic detail with mobile number:", mobile_number_int)  

                lap = goldbasicdetailform.objects.get(phone_number=mobile_number_int)
                print("Basic Detail Object Retrieved:", lap)  

                loan.goldbasicdetail = lap
                loan.mobile_number = str(lap.phone_number)  
                loan.application_id = lap.application_id  
                
                loan.save()  
                request.session['loanid'] = loan.id
                
                # Bhanu
                
                if refCode:
                      if refCode.startswith('SLNDSA'):
                        EducommonDsaLogic(request,refCode,loan)
                 
                      elif refCode.startswith('SLNEMP'):
                        # print("RefCode......................"+refCode)
                        # print(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}")
                        eduSalesLogic(request,refCode,loan)
                
                else:
                     print("Franchise Logic or super admin")
                
                destinationUrl=reverse('goldsuccess', kwargs={'application_id': lap.application_id})
                request.session['goldafterurl']=destinationUrl
                
                # Bhanu
                    
                return redirect('goldsuccess', application_id=lap.application_id)
            except basicdetailform.DoesNotExist:
                print("No matching basic detail found for this phone number.")  
                return redirect('basicdetail')
            except ValueError:
                print("Invalid mobile number format.")  
                return redirect('basicdetail')

    else:
        form = goldform()

    return render(request, 'customer/goldloan.html', {'form': form, 'mobile_number':mobile_number})

def goldsuccess(request, application_id):
    
    goldapp=get_object_or_404(Goldloanapplication,goldbasicdetail__application_id=application_id)
    context = {
        
        'application_id': application_id,
        'goldapp':goldapp,
        
    }
    return render(request, 'customer/goldsuccess.html', context)



# ========================================goldloan end ===============================

# ===========================otherloan start================================

import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"



def otherbasicdetails(request,instance_id=None):
    instance = get_object_or_404(otherbasicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = OtherBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            request.session['mobile_number']=user_details.phone_number
            
            payload = {
                "apiid": APIID,
                "token": TOKEN,
                "methodName": "UATCreditScoreOTP",
                "orderid": orderid,
                "phone_number": user_details.phone_number
            }

            response = requests.post("https://apimanage.websoftexpay.com/api/Uat_creditscore_OTP.aspx", json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('otherfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = OtherBasicDetailForm()

    return render(request, 'customer/otherbasicdetail.html', {'form': form})
def other_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = otherbasicdetailform.objects.get(id=user_id)
        otp = request.POST.get('otp').strip()  
        print(f'otp is:{otp}')
        payload = {
            "apiid": APIID,
            "token": TOKEN,
            "methodName": "UATcreditscore",
            "orderid": request.session.get('orderid'),  
            "fname": user_details.fname,
            "lname": user_details.lname,
            "Dob": user_details.Dob.isoformat() if isinstance(user_details.Dob, date) else user_details.Dob,
            "phone_number": user_details.phone_number,
            "pan_num": user_details.pan_num,
            "application_id":user_details.application_id,
            "otp": otp 
            
        }
        
        response = requests.post("https://apimanage.websoftexpay.com/api/Uat_credit_score.aspx", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                if 'Dob' in data["data"]:
                    dob = data["data"]['Dob']
                    if isinstance(dob, date):
                        data["data"]['Dob'] = dob.isoformat()
                credit_score = data["data"].get("ScoreValue")
                
                if credit_score:
                    loan_application = otherloans.objects.filter(otherbasicdetail=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'customer/othercibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'customer/otherbasicdetail.html',{'otp':otp})



 
 
def otherloanapplication(request):
    mobile_number = request.session.get('mobile_number')  

    if request.method == 'POST':
        form = otherloansform(request.POST, request.FILES)
        if form.is_valid():
            loan = form.save(commit=False)  
            
            try:
                if mobile_number:
                    mobile_number_int = int(mobile_number)
                else:
                    print("Mobile number is not found in session.")  
                    return redirect('otherbasicdetail')

                print("Attempting to find basic detail with mobile number:", mobile_number_int)  

                lap = otherbasicdetailform.objects.get(phone_number=mobile_number_int)
                print("Basic Detail Object Retrieved:", lap)  

                loan.otherbasicdetail = lap
                loan.mobile_number = str(lap.phone_number)  
                loan.application_id = lap.application_id  
                
                loan.save()  
                request.session['loanid'] = loan.id
                return redirect('othersuccess', application_id=lap.application_id)
            except otherbasicdetailform.DoesNotExist:
                print("No matching basic detail found for this phone number.")  
                return redirect('otherbasicdetail')
            except ValueError:
                print("Invalid mobile number format.")  
                return redirect('otherbasicdetail')

    else:
        form = otherloansform()

    return render(request, 'customer/otherloan.html', {'form': form, 'mobile_number': mobile_number})


def othersuccess(request, application_id):
    
    goldapp=get_object_or_404(otherloans,otherbasicdetail__application_id=application_id)
    context = {
        
        'application_id': application_id,
        'goldapp':goldapp,
        
    }
    return render(request, 'customer/othersuccess.html', context)

# def otherapply(request):
#     step = request.session.get('application_step', 'otherbasicdetail')

#     if step == 'otherbasicdetail':
#         return redirect('otherbasicdetail')
#     elif step == 'otherloan':
#         application_id = request.session.get('application_id')
#         if not application_id:
#             return HttpResponseBadRequest("application_id is missing.")
#         return redirect('otherloan')
#     elif step == 'othersuccess':
#         application_id = request.session.get('application_id')
#         if not application_id:
#             return HttpResponseBadRequest("application_id is missing.")
#         return redirect('othersuccess', application_id=application_id)
#     else:
#         return redirect('otherbasicdetail')




def otherview(request):
    customer_profiles = otherloans.objects.all()
    return render(request, 'customer/viewotherloan.html', {'customer_profiles': customer_profiles})
# ============================================================otherloan  end======================




import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"



def basicdetails(request,instance_id=None):
    instance = get_object_or_404(basicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = BasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            destinationUrl=reverse('lapapply')
            request.session['Lapafterurl']=destinationUrl
            request.session['lapAppliId']=True
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            request.session['mobile_number'] = user_details.phone_number

            
            payload = {
                "apiid": APIID,
                "token": TOKEN,
                "methodName": "UATCreditScoreOTP",
                "orderid": orderid,
                "phone_number": user_details.phone_number
            }

            response = requests.post("https://apimanage.websoftexpay.com/api/Uat_creditscore_OTP.aspx", json=payload)
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('fetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = BasicDetailForm()

    return render(request, 'customer/basicdetailform.html', {'form': form})
def fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = basicdetailform.objects.get(id=user_id)
        otp = request.POST.get('otp').strip()  
        print(f'otp is:{otp}')
        payload = {
            "apiid": APIID,
            "token": TOKEN,
            "methodName": "UATcreditscore",
            "orderid": request.session.get('orderid'),  
            "fname": user_details.fname,
            "lname": user_details.lname,
            "Dob": user_details.Dob.isoformat() if isinstance(user_details.Dob, date) else user_details.Dob,
            "phone_number": user_details.phone_number,
            "pan_num": user_details.pan_num,
            "application_id":user_details.application_id,
            "otp": otp 
            
        }
        
        response = requests.post("https://apimanage.websoftexpay.com/api/Uat_credit_score.aspx", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                if 'Dob' in data["data"]:
                    dob = data["data"]['Dob']
                    if isinstance(dob, date):
                        data["data"]['Dob'] = dob.isoformat()
                credit_score = data["data"].get("ScoreValue")
                
                if credit_score:
                    # Save the credit score to the corresponding LoanApplication
                    loan_application = LoanApplication.objects.filter(basic_detail=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'customer/cibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'customer/basicdetailform.html',{'otp':otp})



 
 
def lap_add(request):
    mobile_number = request.session.get('mobile_number')  
    
    # Bhanu
    refCode=None
    francrefCode=None
    if request.GET.get('refCode'):
        print(request.GET.get('refCode'))
        refCode=request.GET.get('refCode')
    if request.GET.get('franrefCode'):
       francrefCode=request.GET.get('franrefCode')
    # Bhanu

    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            loan = form.save(commit=False)  
      
            # Bhanu
    
            if refCode:
              if refCode.startswith('SLNDSA'):
                 print(refCode,"oooooo")
                 loan.dsaref_code=refCode
                 loan.franrefCode=francrefCode
              elif refCode.startswith('SLNEMP'):
                 loan.empref_code=refCode
                 loan.franrefCode=francrefCode
            else:
                 print("Frm Franchise...")
                 loan.franrefCode=francrefCode

            # Bhanu

            try:
                mobile_number_int = int(mobile_number) if mobile_number else None
                if mobile_number_int is None:
                    print("Mobile number is not found in session.")  
                    return redirect('basicdetail')

                print("Attempting to find basic detail with mobile number:", mobile_number_int)  

                lap = basicdetailform.objects.filter(phone_number=mobile_number_int).first()
                
                if lap:
                    print("Basic Detail Object Retrieved:", lap)

                    if LoanApplication.objects.filter(basic_detail=lap).exists():
                        print("This BasicDetail already has a LoanApplication.")
                        return redirect('error_page', message="This DEtails already has an associated Loan Application.")
                    
                    loan.basic_detail = lap
                    loan.mobile_number = str(lap.phone_number)
                    loan.application_id = lap.application_id
                    loan.save()  
                    request.session['loanid'] = loan.id
                    
                    # Bhanu
                    if refCode:
                      if refCode.startswith('SLNDSA'):
                        EducommonDsaLogic(request,refCode,loan)
                 
                      elif refCode.startswith('SLNEMP'):
                        # print("RefCode......................"+refCode)
                        # print(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}")
                        eduSalesLogic(request,refCode,loan)
                
                    else:
                     print("Franchise Logic or super admin")
                    
                    
                    destinationUrl = reverse('lapdoc', kwargs={'application_id': lap.application_id})
                    request.session['lapafterurl'] = destinationUrl

                    # Bhanu
                    
                    return redirect('lapdoc', application_id=lap.application_id)
                else:
                    print("No matching basic detail found for this phone number.")  
                    return redirect('basicdetail')

            except ValueError:
                print("Invalid mobile number format.")  
                return redirect('basicdetail')

    else:
        form = LoanApplicationForm()

    return render(request, 'customer/LAPform.html', {'form': form, 'mobile_number': mobile_number})
from django.shortcuts import render

# Bhanu
def EducommonDsaLogic(request,refCode,loan):
                getDsa = requests.get(f"{settings.DSA_URL}dsa/api/getDsa/{refCode}") #http://127.0.0.1:8001/dsa/getDsa/SLN1001
                if getDsa.status_code == 200:
                    dsaid_list = getDsa.json()
                    if dsaid_list:
                        dsaid = dsaid_list[0]  # ExtrAct the first dictionary
                    else:
                        return HttpResponse(f"No DSA data found with Id: {refCode}")
                    # print(businessObj.ref_code)
                    context = {
                        'dsa': dsaid.get('id'),
                        'cust_applicationId': loan.application_id
                    }
                    response = requests.post(f"{settings.DSA_URL}dsa/api/DSA_Appli_Viewsets/", json=context)
                    # print(f"{settings.DSA_URL}")
                    if response.status_code == 200 or response.status_code == 201:
                        return redirect('upload-documents')
                    else:
                        return HttpResponse(f"Invalid Data..{response.status_code}---{response.text}")
                else:
                    return HttpResponse(f"No DSA Found with Id: {loan.dsaref_code}")
             
def eduSalesLogic(request,refCode,loan):
                getDsa1 = requests.get(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}") #http://127.0.0.1:8004/dsa/getDsa/SLN1001
                # print(getDsa1.text)
                if getDsa1.status_code == 200:
                    dsaid_list1 = getDsa1.json()
                    if dsaid_list1:
                        dsaidd = dsaid_list1[0]  # ExtrAct the first dictionary
                    else:
                        return HttpResponse(f"No Sales data found with Id: {refCode}")
                    # print(businessObj.ref_code)
                    context = {
                        'dsa': dsaidd.get('id'),
                        'cust_applicationId': loan.application_id
                    }
                    response = requests.post(f"{settings.SALES_URL}dsa/api/DSA_Appli_Viewsets/", json=context)
                    # print(f"{settings.DSA_URL}")
                    if response.status_code == 200 or response.status_code == 201:
                        return redirect('upload-documents')
                    else:
                        return HttpResponse(f"Invalid Data..{response.status_code}---{response.text}")
                else:
                    return HttpResponse(f"No Sales Found with Id: {refCode}")

# Bhanu





def lap_document_add(request, application_id): 
       
    basic_detail = get_object_or_404(basicdetailform, application_id=application_id)
    personal_details = get_object_or_404(LoanApplication, basic_detail=basic_detail)
    
    if request.method == 'POST':
        form = LapDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)  
            print(f"Personal Details ID: {personal_details.id}")
            instance.personal_details = personal_details
            instance.save()

            return redirect('success', application_id=application_id)  
        else:
            print(f"Form errors: {form.errors}") 
    else:
        form = LapDocumentUploadForm()

    return render(request, 'customer/lapdoc.html', {
        'form': form,
        'incomesource': personal_details.income_source,
        'loan_type': personal_details.loan_type,
    })


# ====================================================================================================

    
def success(request, application_id):
       
   
    application = get_object_or_404(LoanApplication, basic_detail__application_id=application_id)
    context = {
        'application': application,
        'application_id': application_id,
        
        
    }
    return render(request, 'customer/success.html', context)








def rejected_msg(request,status):
    return render(request,'customer/reject.html',{'status':status})


# ====================================================================================================


from django.http import QueryDict

from django.db.models import Prefetch
from django.shortcuts import render

def lapview(request):
    customer_profiles = LoanApplication.objects.prefetch_related(
        Prefetch('basic_detail__cibil_checks')  # Using the related_name defined in goldCibilCheck
    )

    verification_status = {}
    form_valid_status = {}
    credit_scores = {}

    # Get the status query parameter
    status_query = request.GET.get('status', None)

    for profile in customer_profiles:
        # Check if there is a verification record for the current profile
        verification_exists = lapApplicationVerification.objects.filter(loan=profile).exists()
        verification_status[profile.id] = verification_exists
        
        # Fetch disbursement details and initialize the form
        details = disbursementdetails.objects.filter(verification=profile).first()
        form = DisbursementDetailsForm(instance=details)
        form_valid_status[profile.id] = form.is_valid()

        # If the status query parameter matches 'submitted', mark form as valid
        if status_query == 'submitted':
            form_valid_status[profile.id] = True

        # Fetch the credit score from the first associated goldCibilCheck
        cibil_check = profile.basic_detail.cibil_checks.first()  # Access using related_name
        credit_scores[profile.id] = cibil_check.cibil_score if cibil_check else None

    return render(request, 'customer/lap_view.html', {
        'customer_profiles': customer_profiles,
        'verification_status': verification_status,
        'form_valid_status': form_valid_status,
        'credit_scores': credit_scores,  # Pass credit scores to the template
    })








#views and updates==================================================




def update_lap(request, pk):
    customer_profile = get_object_or_404(LoanApplication, pk=pk)
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, instance=customer_profile)
        if form.is_valid():
            form.save()
            # Redirect to update_lapdoc with the instance_id of the updated loan application
            return redirect('update_doc', instance_id=customer_profile.id)
    else:
        form = LoanApplicationForm(instance=customer_profile)

    return render(request, 'customer/LAPform.html', {'form': form,})

def update_lapdoc(request, instance_id):
    personal_details = get_object_or_404(LoanApplication, id=instance_id)
    applicant_document, created = lapDocumentUpload.objects.get_or_create(personal_details=personal_details)

    if request.method == 'POST':
        form = LapDocumentUploadForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
        
            return redirect('success')
        else:
            print('Form errors:', form.errors)
    else:
        form = LapDocumentUploadForm(instance=applicant_document)

    return render(request, 'customer/lapdoc.html', {
        'form': form,
        
        'incomesource': personal_details.income_source,
        'loan_type': personal_details.loan_type,
    })


def lapdocview(request):
    applicant_documents = lapDocumentUpload.objects.select_related('personal_details').all()
    return render(request, 'customer/docview.html', {'applicant_documents': applicant_documents})

def lapbuttview(request, pk):
    customer_profile = get_object_or_404(LoanApplication, pk=pk)
    return render(request, 'customer/lap_viewbutton.html', {'customer_profile': customer_profile})


def lapdocbutt(request, pk):
    applicant_document = get_object_or_404(lapDocumentUpload, pk=pk)
    return render(request, 'customer/view_docbutt.html', {'applicant_document': applicant_document})







def goldview(request):
    customer_profiles = Goldloanapplication.objects.all()
    return render(request, 'customer/viewgoldloan.html', {'customer_profiles': customer_profiles})

# def goldbuttview(request, pk):
#     applicant_document = get_object_or_404(Goldloanapplication, pk=pk)
#     return render(request, 'customer/view_lapdoc.html', {'applicant_document': applicant_document})
from django.conf import settings


def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp(email, otp_code):
    """Send OTP code to the provided email."""
    subject = 'Your OTP Code'
    message = f'Your OTP code is: {otp_code}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

def generate_verify_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email') 
        otp = request.POST.get('otp')
        
        if otp:
            try:
                otp_entry = OTP.objects.get(otp=otp, expires_at__gte=timezone.now())
                request.session['email'] = otp_entry.email
                return redirect('index')
            except OTP.DoesNotExist:
                return render(request, 'customer/generate_verify_otp.html', {
                    'form': OTPForm(), 
                    'error': 'Invalid or expired OTP',
                    'email': email
                })    
        if email:
            otp_code = generate_otp()
            OTP.objects.create(email=email, otp=otp_code, expires_at=timezone.now() + timezone.timedelta(minutes=5))
            send_otp(email, otp_code)
            return render(request, 'customer/generate_verify_otp.html', {
                'form': OTPForm(),
                'email': email
            })
    
    return render(request, 'customer/generate_verify_otp.html', {
        'form': OTPForm()
    })

def index(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)

    
    return render(request, 'index.html', {
        'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,
        'email': email,'cc':cc,
    })



def lap_verification_add(request, instance_id):
    loan = get_object_or_404(LoanApplication, id=instance_id)
    
    applicant_documents = lapApplicationVerification.objects.filter(loan=loan)
    if applicant_documents.exists():
        applicant_document = applicant_documents.first()  
    else:
        applicant_document = lapApplicationVerification(loan=loan)
    
    if request.method == 'POST':
        form = lapApplicationVerifyForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
            return redirect('success') 
        else:
            print('Form errors:', form.errors)
    else:
        form = lapApplicationVerifyForm(instance=applicant_document)
    
    return render(request, 'customer/lapappliverify.html', {
        'form': form,
    })


def update_lapverify(request, instance_id):
    loan = get_object_or_404(LoanApplication, id=instance_id)
    
    applicant_document, created = lapApplicationVerification.objects.get_or_create(loan=loan)

    if request.method == 'POST':
        form = lapApplicationVerifyForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            verification = form.save()

            if verification.verification_status == 'Approved':
                return redirect('disbursement_details', verification_id=loan.application_id)  
            
            other_fields_approved = any(
                getattr(verification, field.name) == 'Approved'
                for field in verification._meta.get_fields()
                if field.name != 'verification_status'
            )
            
            if other_fields_approved:
                return redirect('page', status='success')
            else:
                return redirect('page', status='rejected')
        else:
            print('Form errors:', form.errors)
    else:
        form = lapApplicationVerifyForm(instance=applicant_document)

    return render(request, 'customer/updateverify.html', {
        'form': form,
    })


def disbursement_details(request, verification_id):
    modelClass=LoanApplication
    relationModelClass=disbursementdetails
    formClass=DisbursementDetailsForm
    reDirectUrl='disbursement_summary'
    
    if verification_id.startswith('SLNEL'):
        modelClass=Educationalloan
        relationModelClass=Edudisbursementdetails
        formClass=EduDisbursementDetailsForm
        reDirectUrl='Edudisbursement_summary'
    elif verification_id.startswith('SLNBL'):
        modelClass=BusinessLoan
        relationModelClass=Busdisbursementdetails
        formClass=BusDisbursementDetailsForm
        reDirectUrl='Busdisbursement_summary'
        
        
    verification = get_object_or_404(modelClass, application_id=verification_id)
   
    
    details, created = relationModelClass.objects.get_or_create(verification=verification)
    form_status = 'not_submitted'

    if request.method == 'POST':
        form = formClass(request.POST, instance=details)
        if form.is_valid():
            form.save()
            form_status = 'submitted'
            
            return redirect(reDirectUrl)
        
            
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = DisbursementDetailsForm(instance=details)

    return render(request, 'customer/disbursement_details.html', {
        'details_form': form,'form_status':form_status,})







def disbursement_summary(request):
    details_list = disbursementdetails.objects.select_related('verification').all()

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.application_id if details.verification else 'No Verification'}")

    return render(request, 'customer/disbursementview.html', {
        'details_list': details_list,
    })



def lapcustomerverify(request, instance_id):
    loan = get_object_or_404(LoanApplication, id=instance_id)
    
    verfyObj = lapApplicationVerification.objects.filter(loan=loan).first()
    
    session_email = request.session.get('email')
    application_id = None
    if session_email and session_email == loan.email_id:
        application_id = loan.application_id
    
    return render(request, 'customer/customerverify.html', {
        'loan': loan,
        'verfyObj': verfyObj,
        'application_id': application_id,  
    })


def custom_logout(request):
    logout(request)
    return redirect('send_otp') 

from rest_framework.response import Response
from django.db.models import Q
from django.apps import apps

def commonInsuranceGet(request,refCode):
    
    allInsurance=AllInsurance.objects.filter(Q(dsaref_code__icontains=refCode) |
               Q(franrefCode__icontains=refCode)  |
               Q(empref_code=refCode)).count()
    
    lifeInsurance=LifeInsurance.objects.filter(Q(dsaref_code__icontains=refCode) |
               Q(franrefCode__icontains=refCode)  |
               Q(empref_code=refCode)).count()
    
    generalInsurance=GeneralInsurance.objects.filter(Q(dsaref_code__icontains=refCode) |
               Q(franrefCode__icontains=refCode)  |
               Q(empref_code=refCode)).count()
    
    healthInsuranc=healthInsurance.objects.filter(Q(dsaref_code__icontains=refCode) |
               Q(franrefCode__icontains=refCode)  |
               Q(empref_code=refCode)).count()
    
    totalInsurance=allInsurance+lifeInsurance+generalInsurance+healthInsuranc
    
    return JsonResponse({'allInsurance':allInsurance,'lifeInsurance':lifeInsurance,'generalInsurance':generalInsurance,'healthInsurance':healthInsuranc,'totalInsurance':totalInsurance},status=200)


# bhanu





def LoanAgainstProperty(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'LoanAgainstProperty.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})



from django.shortcuts import render

# Create your views here.

def About(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'About.html', {'email': email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})



def Allinsurance(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)
  
    form=InsuranceForm()
    if request.method=='POST':
        form=InsuranceForm(request.POST)
        form.save()
        return HttpResponse("data saved")
    return render(request,'AllInsurance.html',{'form':form,'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def allinsurance_view(request):
    all=AllInsurance.objects.all()
    return render(request,'customer/view_insurance.html',{'all':all})
def lifeinsurance_view(request):
    life=LifeInsurance.objects.all()
    return render(request,'customer/view_lifeinsurance.html',{'life':life})

def generalinsurance_view(request):
    general=GeneralInsurance.objects.all()
    return render(request,'customer/view_generalinsurance.html',{'general':general})
    

def healthinsurance_view(request):
    health=healthInsurance.objects.all()
    return render(request,'customer/view_healthinsurance.html',{'health':health})
    

    

def Generalinsurance(request):
    
    
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    
    form=genInsuranceForm()
    if request.method=='POST':
        form=genInsuranceForm(request.POST)
        form.save()
        return HttpResponse("data saved")

    return render(request, 'GeneralInsurance.html',{'form':form,'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})



def Healthinsurance(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    email = request.session.get('email')
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    form=healthInsuranceForm()
    if request.method=='POST':
        form=healthInsuranceForm(request.POST)
        form.save()
        return HttpResponse("data saved")
    else:
       return render(request, 'HealthInsurance.html',{'form':'form','email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def Lifeinsurance(request):
    
    email = request.session.get('email')
    
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    form=lifeInsuranceForm()
    if request.method=='POST':
        form=lifeInsuranceForm(request.POST)
        form.save()
        return HttpResponse("data saved")
    else:
       
       return render(request, 'LifeInsurance.html',{'form':form,'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})
    

def BussinessLoan(request):

    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'BussinessLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def Carloan(request):
    
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'CarLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def contact(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'contact.html',{'email': email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def creditpage(request):
  
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'creditpage.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})
@csrf_exempt
def dsa(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)
    if request.method == 'POST':
        form = dsaform(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<h1>succesfully registered</h1>')  # Change to your actual success URL
        else:
            print('Form errors:', form.errors)  # Check what validation fails
    else:
        form = dsaform()

    return render(request, 'dsa.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc,'form':form})

def educationalloan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'Educationalloan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})
@csrf_exempt
def franchise_add(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)
    form=franchiseform()
    if request.method == 'POST':
        form = franchiseform(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('<h1>succesfully registered</h1>')  # Change to your actual success URL
        else:
            print('Form errors:', form.errors)  # Check what validation fails
    else:
        form = franchiseform()


    return render(request, 'franchise.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc,'form':form})



def GoldLoan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'GoldLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})


def HomeLoan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'HomeLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def LoanAgainstProperty(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'LoanAgainstProperty.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def NewCarLoan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'NewCarLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def Personalloans(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'Personalloans.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})

def UsedCarLoan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)


    return render(request, 'UsedCarLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc})


def homeloan(request):
    email = request.session.get('email')
    loans = LoanApplication.objects.filter(email_id=email)
    edu = Educationalloan.objects.filter(mail_id=email)
    bus=BusinessLoan.objects.filter(email_id=email)
    pl = PersonalDetail.objects.filter(email=email)
    hl=CustomerProfile.objects.filter(email_id=email)
    cl=CarLoan.objects.filter(email_id=email)
    cc=CreditDetail.objects.filter(email=email)

    return render(request, 'HomeLoan.html',{'email':email,'loans': loans,'edu':edu,'bus':bus,'pl':pl,'hl':hl,'cl':cl,'cc':cc,'url':f"{settings.CUSTOMER_SUPPORT_URL}ticket_create/"})


# def customer_support(request):
#     return render(request,'customer/customer_support.html',{'url':f"{settings.CUSTOMER_SUPPORT_URL}ticket_create/"})






