from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.urls import reverse
from rest_framework.response import Response
import requests
from django.conf import settings
from business.Busi_serializers import BusiSerializer
from .forms import *
from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import *
from datetime import datetime

from django.contrib import messages
# Create your views here.



def demo(request):
    return HttpResponse("hi Your Project Working Fine")

def sucess(request):
    return render(request,"SuccessPage.html")

@csrf_exempt
def apply_for_business_loan(request):
    print("Zip2...........................")
    refCode=None
    francrefCode=None
    if request.GET.get('refCode'):
        print(request.GET.get('refCode'))
        refCode=request.GET.get('refCode')
    if request.GET.get('franrefCode'):
       francrefCode=request.GET.get('franrefCode')

    if request.method == 'POST':
        form = BusinessLoanForm(request.POST)
        if form.is_valid():
            businessObj = form.save(commit=False)

            if refCode:
              if refCode.startswith('SLNDSA'):
                 businessObj.dsaref_code=refCode
                 businessObj.franrefCode=francrefCode
              elif refCode.startswith('SLNEMP'):
                 businessObj.empref_code=refCode
                 businessObj.franrefCode=francrefCode
            else:
                 businessObj.franrefCode=francrefCode

# BasicdetailGettingRecordLogic
            busObj=busbasicdetailform.objects.get(phone_number=businessObj.mobile_number)
            if busObj:
              businessObj.basicdetailform=busObj
              businessObj.application_id=busObj.application_id
              businessObj.save()
            else:
                return redirect('busbasicdetail')
            request.session['business_id'] = businessObj.id
# BasicdetailGettingRecordLogic



# DSA LoGIC
            # if businessObj.dsaref_code is not None:
            #     refCode=businessObj.dsaref_code

            if refCode:
              if refCode.startswith('SLNDSA'):
                print("RefCode......................"+refCode)
                commonDsaLogic(request,refCode,businessObj)
               
              elif refCode.startswith('SLNEMP'):
                print("RefCode......................"+refCode)
                salesLogic(request,refCode,businessObj)
               
            else:
               print("Franchise Logic")
                 
            
# DSA LoGIC 

                # if Ref Code is empty
            destinationUrl=reverse('upload-documents')
            request.session['Busafterurl']=destinationUrl
            
            return redirect('upload-documents')
        else:
            print(form.errors)
            return render(request, 'apply_for_business_loan.html', {'form': form})

    # if request method is GET
    else:
        form = BusinessLoanForm()
    return render(request, 'apply_for_business_loan.html', {'form': form})


def commonDsaLogic(request,refCode,businessObj):
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
                        'cust_applicationId': businessObj.application_id
                    }
                    response = requests.post(f"{settings.DSA_URL}dsa/api/DSA_Appli_Viewsets/", json=context)
                    # print(f"{settings.DSA_URL}")
                    if response.status_code == 200 or response.status_code == 201:
                        return redirect('upload-documents')
                    else:
                        return HttpResponse(f"Invalid Data..{response.status_code}---{response.text}")
                else:
                    return HttpResponse(f"No DSA Found with Id: {businessObj.dsaref_code}")
             
   
def salesLogic(request,refCode,businessObj):
                print(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}")
                getDsa1 = requests.get(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}") #http://127.0.0.1:8004/dsa/getDsa/SLN1001
                print(getDsa1.text)
                if getDsa1.status_code == 200:
                    dsaid_list1 = getDsa1.json()
                    if dsaid_list1:
                        dsaidd = dsaid_list1[0]  # ExtrAct the first dictionary
                    else:
                        return HttpResponse(f"No Sales data found with Id: {refCode}")
                    # print(businessObj.ref_code)
                    context = {
                        'dsa': dsaidd.get('id'),
                        'cust_applicationId': businessObj.application_id
                    }
                    response = requests.post(f"{settings.SALES_URL}dsa/api/DSA_Appli_Viewsets/", json=context)
                    # print(f"{settings.DSA_URL}")
                    if response.status_code == 200 or response.status_code == 201:
                        return redirect('upload-documents')
                    else:
                        return HttpResponse(f"Invalid Data..{response.status_code}---{response.text}")
                else:
                    return HttpResponse(f"No Sales Found with Id: {refCode}")
            

def upload_documents(request):
    
    loanid=None
    if request.session.get('business_id'):
        loanid= request.session.get('business_id')
        
    if request.GET.get('id'):
        loanid=request.GET.get('id')

    if request.method == 'POST':
        if loanid:
            try:
             loanObj = get_object_or_404(BusinessLoan, application_id=loanid)
            except:
               return HttpResponse(f"No Record Found with ID of : {loanid}")

            form = BusinessLoanDocumentForm(request.POST, request.FILES)

            if form.is_valid():
                docObj = form.save(commit=False)
                docObj.loan = loanObj
                try:
                 docObj.save()
                except:
                   return HttpResponse("Documents Already Uploaded..")
                
                if request.session.get('business_id'):
                 del request.session['business_id']
                return HttpResponse('Created Document with Application Id of - {}'.format(loanObj.application_id))
            else:
                # If the form is not valid, re-render the form with errors
                print(form.errors)
                return render(request, 'Bussiness_upload_documents.html', {'form': form})
        else:
            return redirect('demo')
    else:
        form = BusinessLoanDocumentForm()
    
    return render(request, 'BussinessUploadDocuments.html', {'form': form})


# def insuranceForm(request):
#     if request.method=='POST':
#         form=InsuranceForm(request.POST)
#         form.save()
#         return HttpResponse("data saved")
#     else:
#         return render(request,'Insurance.html')
@csrf_exempt
def business_loan_list(request):
    business_loans = BusinessLoan.objects.all()
    applicationid=None
    cuurentStage=businesslistDemo(request)
    print("Method Executed...")
    

    if request.method=='POST':

        if request.POST.get('field'):
           print(request.POST.get('field'))
           fieldnme=request.POST.get('field')
           business_loans=BusinessLoan.objects.filter(
            models.Q(first_name__icontains=fieldnme) |
            models.Q(mobile_number__icontains=fieldnme) |
            models.Q(application_id__icontains=fieldnme) |
            models.Q(email_id__icontains=fieldnme)
               )
           print(business_loans)
           
        if request.POST.get('date'):
            print("jhghuji")
            filterrecords=[]
            date= request.POST.get('date')
            date_format = "%Y-%m-%d"
            # print(date)
            date1=date.split(' to ')[0]
            date2=date.split(' to ')[1]
            date1 = datetime.strptime(date1, date_format).date()
            date2 = datetime.strptime(date2, date_format).date()
            for filter in business_loans:
                if filter.created_at >= date1 and filter.created_at <= date2:
                    filterrecords.append(filter)
            business_loans=filterrecords


    # print(business_loans)
    # print(business_loans)
    
    paginator = Paginator(list(zip(business_loans,cuurentStage)), 1)  
    page = request.GET.get('page')

    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)

    start_index = (objects.number - 1) * paginator.per_page + 1

    if applicationid:
        return render(request, 'DataTable.html', {'objects': objects, 'start_index': start_index})

    # If the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET" and request.GET.get('applicationid'):
        print("AJAX method is activated...")
        return render(request, 'business_loan_list.html', {'objects': objects, 'start_index': start_index})
    
    print(objects)


    return render(request, 'business_loan_list.html', {'objects': objects, 'start_index': start_index})
    


def businesslistDemo(request):
    obj=BusinessLoan.objects.prefetch_related('applicationverification','BussinessLoandocuments').all()
    currentStage=[]
    fieldName=None
    for i in obj:
       
        if  hasattr(i, 'applicationverification'):
          appli=i.applicationverification
          for index,field in enumerate(appli._meta.get_fields()):
                # print(index,field.name)
                field_value = getattr(appli, field.name)
                # if index==2 and field_value=="Rejected":
                #     fieldName= field.name+":Rejected"
                #     break
                if field_value=="Approved":
                    if field.name=="personal_detail_verifaction":
                      fieldName= "Personal Detail Approved"

                    elif field.name=="documents_upload_verification":
                      fieldName= "Document Upload Approved"
                    
                    elif field.name=="documents_verification":
                      fieldName= "Document Approved"

                    elif field.name=="eligibility_check_verification":
                      fieldName= "Eligibility Check Approved"

                    elif field.name=="bank_login_verification":
                      fieldName= "Bank Login Approved"

                    elif field.name=="loanverification":
                      fieldName= "Login Approved"

                    elif field.name=="kyc_and_document_verification":
                      fieldName= "KYC Approved"
                    
                    elif field.name=="enach_verification":
                      fieldName= "ENACH Approved"
                    
                    elif field.name=="fieldverification":
                      fieldName= "Field Approved"

                    elif field.name=="incomeverification":
                      fieldName= "Income Approved"

                    elif field.name=="disbursment_verification":
                      fieldName= "Disbursment Approved"

                    else:
                       fieldName= "Verification Approved"
                       
                elif field_value=="Rejected":
                    # fieldName= field.name+":Rejected"
                    # break
                    if field.name=="personal_detail_verifaction":
                      fieldName= "Personal Detail Rejected"
                      break

                    elif field.name=="documents_upload_verification":
                      fieldName= "Document Upload Rejected"
                      break
                    
                    elif field.name=="documents_verification":
                      fieldName= "Document Rejected"
                      break

                    elif field.name=="eligibility_check_verification":
                      fieldName= "Eligibility Check Rejected"
                      break

                    elif field.name=="bank_login_verification":
                      fieldName= "Bank Login Rejected"
                      break

                    elif field.name=="loanverification":
                      fieldName= "Login Rejected"
                      break

                    elif field.name=="kyc_and_document_verification":
                      fieldName= "KYC Rejected"
                      break
                    
                    elif field.name=="enach_verification":
                      fieldName= "ENACH Rejected"
                      break
                    
                    elif field.name=="fieldverification":
                      fieldName= "Field Rejected"
                      break

                    elif field.name=="incomeverification":
                      fieldName= "Income Rejected"
                      break

                    elif field.name=="disbursment_verification":
                      fieldName= "Disbursment Rejected"
                      break

                    else:
                       fieldName= "Verification Rejected"
                    

          currentStage.append(fieldName)
        else:
            # print("didnt exist")
            currentStage.append(None)


    for k in currentStage:
        print(k)
    return currentStage




def business_loan_update(request,application_id):
    loan = get_object_or_404(BusinessLoan, application_id=application_id)
    print(loan.id)
    if request.method == 'POST':
        form = BusinessLoanForm(request.POST, instance=loan,instance_id=loan.id)
        if form.is_valid():
            form.save()
            return HttpResponse('Updated')
        else:
            print(form.errors)
            return render(request, 'business_loan_update.html', {'form': form})

    else:
        form = BusinessLoanForm(instance=loan)
    return render(request, 'business_loan_update.html', {'form': form})

def business_loan_view(request,id):
    if BusinessLoan.objects.filter(id=id).exists():
        businessObj=BusinessLoan.objects.get(id=id)
        form=BusinessLoanForm(instance=businessObj)
        return render(request,'business_loan_view.html',{'form':form})
    

def documentsView(request,application_id,loan=None):
    try:
      loan = get_object_or_404(BusinessLoan.objects.prefetch_related('BussinessLoandocuments'),application_id=application_id)
      document = loan.BussinessLoandocuments 
    
    except Exception as e:
     return HttpResponse("No Documents Found...")


    if request.method=='GET':
         
         form = BusinessLoanDocumentForm(instance=document)
    
    return render(request, 'ViewBusDocument.html', {'form': form, 'loan': loan})





def update_business_loan_document(request,application_id,loan=None):
    
    try:
      loan = get_object_or_404(BusinessLoan.objects.prefetch_related('BussinessLoandocuments'),application_id=application_id)
      document = loan.BussinessLoandocuments 
    
    except Exception as e:
     return HttpResponse("No Documents Found...")
    
    if request.method == 'POST':
        form = BusinessLoanDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
        #    docObj = form.save(commit=False)
        #    docObj.loan = loan
        #    docObj.save()
           form.save()
           return HttpResponse('Document Updated')
        else:
            print(form.errors)
            return render(request, 'UpdateBusinessLoanDocument.html', {'form': form, 'loan': loan})

    else:
         print('hiiii')
         print(document.aadhar_card_front)
         form = BusinessLoanDocumentForm(instance=document)
    
    return render(request, 'UpdateBusinessLoanDocument.html', {'form': form, 'loan': loan})



def busapplicationVerification(request,application_id,loan=None):

    loan=BusinessLoan.objects.get(application_id=application_id)
    if request.method == 'POST':
        form = ApplicationVerifyForm(request.POST)
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
        form = ApplicationVerifyForm()
        return render(request, 'BusiApplicationVerification.html', {'form': form})
    

def busupdate_verification(request,application_id,loan=None):

    try:
        loan=get_object_or_404(BusinessLoan.objects.prefetch_related('applicationverification'),application_id=application_id)
        verifObj=loan.applicationverification

    except Exception as e:
        return HttpResponse("No Verification details found...")
    

    if request.method=='GET':
        form=ApplicationVerifyForm(instance=verifObj)
        return render(request,"BusiUpdateVerification.html",{'form':form})
    else:
         form = ApplicationVerifyForm(request.POST,instance=verifObj)
         if form.is_valid():
           docObj = form.save(commit=False)
           docObj.loan = loan
           docObj.save()
           
            # Check the verification_status and redirect accordingly
           if docObj.verification_status == 'Approved':
                return redirect('disbursement_details', verification_id=loan.application_id)
           else:
                return HttpResponse('Verification updated, but status is not approved.')
         else:
            print(form.errors)
            return render(request,"BusiUpdateVerification.html",{'form':form})
    
   
def busdisbursement_summary(request):
    details_list = Busdisbursementdetails.objects.select_related('verification').all()

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.id if details.verification else 'No Verification'}")

    return render(request, 'customer/disbursementview.html', {
        'details_list': details_list
    })




    
        


         
         
def customerProfile(request,application_id,loan=None):
     try:
      loan=get_object_or_404(BusinessLoan.objects.prefetch_related('applicationverification'),application_id=application_id)
      try:
       verfyObj=loan.applicationverification
      except:
          verfyObj=None
         
     except Exception as e:
         verfyObj=None
         return HttpResponse("No records Found..")
     
     if request.method=='GET':
      if not request.session.get('email') and request.session.get('email')!=loan.email_id:
        # del request.session['email']
        return render(request,"BusCustomerProfile.html",{'loan':loan,'verfyObj':verfyObj})

import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"


@csrf_exempt
def busbasicdetails(request,instance_id=None):
    instance = get_object_or_404(busbasicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = busBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            
            destinationUrl=reverse('demo')
            request.session['Busafterurl']=destinationUrl
            request.session['busiAppliId']=True
            
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
                return redirect('busfetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
    else:
        form = busBasicDetailForm()

    return render(request, 'busbasicdetail.html', {'form': form})
def bus_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = busbasicdetailform.objects.get(id=user_id)
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
                    loan_application = BusinessLoan.objects.filter(basicdetailform=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'buscibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'busbasicdetail.html',{'otp':otp})



#AnushaLogic..................................................

# def disbursement_details(request, verification_id):
#     verification = get_object_or_404(LoanApplication, id=verification_id)
#     details, created = disbursementdetails.objects.get_or_create(verification=verification)
#     form_status = 'not_submitted'

#     if request.method == 'POST':
#         form = DisbursementDetailsForm(request.POST, instance=details)
#         if form.is_valid():
#             form.save()
#             form_status = 'submitted'
#             return redirect('disbursement_summary')
        
            
#         else:
#             print(f"Form errors: {form.errors}")
#     else:
#         form = DisbursementDetailsForm(instance=details)

#     return render(request, 'customer/disbursement_details.html', {
#         'details_form': form,'form_status':form_status,
#     })



     
     
         
     

    
    


    