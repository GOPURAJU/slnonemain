from django.conf import settings
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.urls import reverse
from .forms import *
from .models import *
# from django.conf import settings
from django.contrib import messages


def demo(request):
    return HttpResponse("hi Your Project is Working")
import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"
    

def carbasicdetail(request,instance_id=None):
    instance = get_object_or_404(CLBasicDetail, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = CLBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            
            destinationUrl=reverse('car-loan-application')
            request.session['clafterurl']=destinationUrl
            request.session['carAppliId']=True
            
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            request.session['orderid'] = orderid
            request.session['user_id'] = user_details.id
            
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
                return redirect('carfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
        else:
            print(form.errors)
    else:
        form = CLBasicDetailForm()

    return render(request, 'carbasicdetailform.html', {'form': form})
def car_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = CLBasicDetail.objects.get(id=user_id)
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
                    loan_application = CarLoan.objects.filter(carbasic_detail=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'carcibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'carbasicdetailform.html',{'otp':otp})

def success(request):
    return render(request,'success.html')


def apply_for_car_loan(request):
    print("View function")
    
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
        print('post')
        form = CarLoanForm(request.POST)
        if form.is_valid():
            carObj=form.save(commit=False)
            # return redirect("success")
            
            
              # Bhanu
            if refCode:
              if refCode.startswith('SLNDSA'):
                 carObj.dsaref_code=refCode
                 carObj.franrefCode=francrefCode
              elif refCode.startswith('SLNEMP'):
                 carObj.empref_code=refCode
                 carObj.franrefCode=francrefCode
            else:
                 carObj.franrefCode=francrefCode
            # Bhanu
            
            carbasic=CLBasicDetail.objects.get(phone_number=carObj.mobile_number)
            if carObj:
              carObj.carbasic_detail=carbasic
              carObj.application_id=carbasic.application_id
              carObj.save()
            else:
                return redirect('carbasicdetail')
            request.session['car_id'] = carObj.application_id
            
            
            
                               
 # Bhanu
            if refCode:
                    if refCode.startswith('SLNDSA'):
                             EducommonDsaLogic(request,refCode,carObj)
                
                    elif refCode.startswith('SLNEMP'):
                            eduSalesLogic(request,refCode,carObj)
                
            elif francrefCode:
                       print("Franchise Logic")
                       
               
            destinationUrl=reverse('cardoc')
            request.session['clafterurl']=destinationUrl
           
#Bhanu

            return redirect('cardoc')
        else:
            print(form.errors)
            return render(request,'apply_for_car_loan.html',{'form': form})
       
    else:
        form = CarLoanForm()
    
    return render(request, 'apply_for_car_loan.html', {'form': form})


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
                    if response.status_code != 200 or response.status_code != 201:
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
                    if response.status_code != 200 or response.status_code != 201:
                        return HttpResponse(f"Invalid Data..{response.status_code}---{response.text}")
                    
                else:
                    return HttpResponse(f"No Sales Found with Id: {refCode}")
# Bhanu

def upload_documents(request):
    loanid = None
    if request.session.get('car_id'):
        loanid = request.session.get('car_id')
        
    if request.GET.get('id'):
        loanid = request.GET.get('id')

    if loanid:
        try:
            loanObj = get_object_or_404(CarLoan, application_id=loanid)
        except:
            return HttpResponse(f"No Record Found with ID of: {loanid}")

    if request.method == 'POST':
        form = CarLoanDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            docObj = form.save(commit=False)
            docObj.loan = loanObj
            
            try:
                docObj.save()
            except:
                return HttpResponse("Documents Already Uploaded.")
            
            if request.session.get('car_id'):
                del request.session['car_id']
            return HttpResponse(f'Created Document with Application Id of - {loanObj.application_id}')
        else:
            print(form.errors)
            return render(request, 'Car_upload_documents.html', {'form': form, 'loanObj': loanObj})

    else:
        form = CarLoanDocumentForm()

    return render(request, 'Car_upload_documents.html', {'form': form, 'loanObj': loanObj})



def car_loan_list(request):
    car_loans = CarLoan.objects.all()
    return render(request, 'car_loan_list.html', {'car_loans': car_loans})


def car_loan_update(request,application_id):
    loan = get_object_or_404(CarLoan, application_id=application_id)
    print(loan)
    if request.method == 'POST':
        form = CarLoanForm(request.POST, instance=loan,instance_id=loan.id)
        if form.is_valid():
            form.save()
            return HttpResponse('Updated')
        else:
            print(form.errors)
            return render(request, 'car_loan_update.html', {'form': form})

    else:
        form = CarLoanForm(instance=loan)
    return render(request, 'car_loan_update.html', {'form': form})


def car_loan_view(request,id):
    if CarLoan.objects.filter(id=id).exists():
        carObj=CarLoan.objects.get(id=id)
        form=CarLoanForm(instance=carObj)
        return render(request,'car_loan_view.html',{'form':form})


def documentsView(request,application_id,loan=None):
    try:
      loan = get_object_or_404(CarLoan.objects.prefetch_related('CarLoandocuments'),application_id=application_id)
      document = loan.CarLoandocuments 
    
    except Exception as e:
     return HttpResponse("No Documents Found...")

    if request.method=='GET':
        form = CarLoanDocumentForm(instance=document)
    
    return render(request, 'ViewDocument.html', {'form': form, 'loan': loan})


def update_car_loan_document(request,application_id,loan=None):
    
    try:
      loan = get_object_or_404(CarLoan.objects.prefetch_related('CarLoandocuments'),application_id=application_id)
      document = loan.CarLoandocuments 
    
    except Exception as e:
     return HttpResponse("No Documents Found...")
    
    if request.method == 'POST':
        form = CarLoanDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
           docObj = form.save(commit=False)
           docObj.loan = loan
           docObj.save()
        
           return HttpResponse('Document Updated')
        else:
            print(form.errors)
            return render(request, 'update_car_loan_document.html', {'form': form, 'loan': loan})

    else:
         print('helloo')
         form = CarLoanDocumentForm(instance=document)
    return render(request, 'update_car_loan_document.html', {'form': form, 'loan': loan})



def carapplicationVerification(request,application_id,loan=None):
    
    loan=CarLoan.objects.get(application_id=application_id)
    if request.method == 'POST':
        form = CarApplicationVerifyForm(request.POST)
        if form.is_valid():
          try:
            verifiObj=form.save(commit=False)
            verifiObj.loan=loan
            verifiObj.save()
            return HttpResponse("success")
          except:
              return HttpResponse("Verification already applied...")
        else:
            print(form.errors)
            return HttpResponse("Invalid form data", status=400)  # Return a response for invalid form data
    else:
        form = CarApplicationVerifyForm()
        return render(request, 'CarApplicationVerification.html', {'form': form})
    

def update_car_verify(request,application_id,loan=None):
    
    try:
        loan=get_object_or_404(CarLoan.objects.prefetch_related('applicationverification'),application_id=application_id)
        verifObj=loan.applicationverification
        print(verifObj.valuation)


    except Exception as e:
        return HttpResponse("No Verification details found...")
    
    if request.method=='GET':
        form=CarApplicationVerifyForm(instance=verifObj)
        # print(form)
        return render(request,"UpdateCarVerification.html",{'form':form})
    else:
         form = CarApplicationVerifyForm(request.POST,instance=verifObj)
         if form.is_valid():
           docObj = form.save(commit=False)
           docObj.loan = loan
           docObj.save()

           if docObj.verification_status == 'Approved':
                return redirect('disbursement_cardetails', verification_id=loan.application_id)
                # return HttpResponse('Updated Verification successfully..')
           else:
                return HttpResponse('Verification updated, but status is not approved.')
           
         else:
            print(form.errors)
            return render(request,"UpdateCarVerification.html",{'form':form})



def carcustomerProfile(request,application_id,loan=None):
    try:
        loan=get_object_or_404(CarLoan.objects.prefetch_related('applicationverification'),application_id=application_id)
        try:
            verfyObj=loan.applicationverification
        except:
          verfyObj=None
         
    except Exception as e:
         verfyObj=None
         return HttpResponse("No records Found..")
     
    if request.method=='GET':
        if request.session.get('email') and request.session.get('email')==loan.email_id:
            del request.session['email']
       
        return render(request,"customerProfile.html",{'loan':loan,'verfyObj':verfyObj})
          


def disbursement_cardetails(request, verification_id):
    # Fetch the carApplication instance instead of CarLoan
    verification = get_object_or_404(CarLoan, application_id=verification_id)

    # Fetch or create the cardisbursementdetails using the correct verification instance
    details, created = CarDisbursementDetails.objects.get_or_create(verification=verification)
    form_status = 'not_submitted'

    if request.method == 'POST':
        form = CarDisbursementDetailsForm(request.POST, instance=details)
        if form.is_valid():
            form.save()
            form_status = 'submitted'
            return redirect('disbursement_carsummary')  # Pass verification_id here)
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = CarDisbursementDetailsForm(instance=details)

    return render(request, 'disbursement_cardetails.html', {
        'details_form': form,
        'form_status': form_status,
    })



def disbursement_carsummary(request):
    # Assuming CarDisbursementDetails has a foreign key to verification
    details_list = CarDisbursementDetails.objects.select_related('verification').all()
    #filter(verification_id=verification_id)

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.id if details.verification else 'No Verification'}")
        
    return render(request, 'disbursement_carview.html', {
        'details_list': details_list
    })


