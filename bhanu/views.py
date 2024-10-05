from django.shortcuts import get_object_or_404, render,redirect
from django.urls import reverse
from .models import *
from .forms import *
from django.http import HttpResponse
from django.conf import settings
# DSA
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import *
import requests
from datetime import datetime
from django.contrib import messages
# Create your views here.



import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"


@csrf_exempt

def edubasicdetails(request,instance_id=None):
    instance = get_object_or_404(edubasicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        print("EdubasicPost")
        form = eduBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            
            destinationUrl=reverse('createEducationloan')
            request.session['Eduafterurl']=destinationUrl
            request.session['eduAppliId']=True
            
            print("afetre sessions")
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
            print("after response")
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                otp = data["data"].split(":")[1]
                user_details.otp = otp  
                user_details.orderid = orderid
                user_details.save()
                print(f'otp is:{otp}')
                request.session['otp']=otp
                return redirect('edufetchcreditreport')
            else:
                return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
        else:
             print(form.errors)
             print("else part")
    else:
        form = eduBasicDetailForm()

    return render(request, 'ebasicdetail.html', {'form': form})
def edu_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = edubasicdetailform.objects.get(id=user_id)
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
                    loan_application = Educationalloan.objects.filter(basicdetailform=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'ecibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'ebasicdetail.html',{'otp':otp})



@csrf_exempt
def create_EducationLoan(request):
    refCode=None
    francrefCode=None
    if request.GET.get('refCode'):
        print(request.GET.get('refCode'))
        refCode=request.GET.get('refCode')
    if request.GET.get('franrefCode'):
       francrefCode=request.GET.get('franrefCode')

    if request.method == 'POST':
        form = EducationalLoanForm(request.POST, request.FILES)
        if form.is_valid():
            loan=form.save(commit=False)


            if refCode:
              if refCode.startswith('SLNDSA'):
                 loan.dsaref_code=refCode
                 loan.franrefCode=francrefCode
              elif refCode.startswith('SLNEMP'):
                 loan.empref_code=refCode
                 loan.franrefCode=francrefCode
            else:
                 loan.franrefCode=francrefCode

# EduvationLoanBasic
            eduObj=edubasicdetailform.objects.get(phone_number=loan.mobile_number)
            if eduObj:
             loan.basicdetailform=eduObj
             loan.application_id=eduObj.application_id
             loan.save()
            else:
                return redirect('edubasicdetail')
# EduvationLoanBasic

            request.session['loanid']=loan.id
# DSA LoGIC
            # if loan.dsaref_code is not None:
            #     refCode=loan.dsaref_code

            if refCode:
              if refCode.startswith('SLNDSA'):
                EducommonDsaLogic(request,refCode,loan)
                 
              elif refCode.startswith('SLNEMP'):
                # print("RefCode......................"+refCode)
                # print(f"{settings.SALES_URL}dsa/api/getDsa/{refCode}")
                eduSalesLogic(request,refCode,loan)
                
            else:
               print("Franchise Logic or super admin")
# DSA LoGIC 

            destinationUrl=reverse('create-doc')
            request.session['Eduafterurl']=destinationUrl
            
            return redirect('create-doc')
       
    else:
        form = EducationalLoanForm()
    
    return render(request, 'Apply_EducationLoan.html', {'form': form})

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

def loan_records(request):
    edu_loans = Educationalloan.objects.prefetch_related('applicationverification','personal_details').all()
    applicationid=None
    cuurentStage=eduListDemo(request,edu_loans)
    print("Method Executed...")
    

    if request.method=='POST':
        if request.POST.get('field'):
        #    print("uyyu99")
           print(request.POST.get('field'))
           fieldnme=request.POST.get('field')
           edu_loans=Educationalloan.objects.filter(
            models.Q(student_name__icontains=fieldnme) |
            models.Q(mobile_number__icontains=fieldnme) |
            models.Q(application_id__icontains=fieldnme) |
            models.Q(mail_id__icontains=fieldnme)
               
               )
        if request.POST.get('date'):
            # print("jhghuji")
            filterrecords=[]
            date= request.POST.get('date')
            date_format = "%Y-%m-%d"
            # print(date)
            date1=date.split(' to ')[0]
            date2=date.split(' to ')[1]
            date1 = datetime.strptime(date1, date_format).date()
            date2 = datetime.strptime(date2, date_format).date()
            for filter in edu_loans:
                if filter.created_at >= date1 and filter.created_at <= date2:
                    filterrecords.append(filter)
            edu_loans=filterrecords

            # print(date1,date2)
           


    # print(business_loans)
    # print(business_loans)
    paginator = Paginator(list(zip(edu_loans,cuurentStage)), 1)  
    page = request.GET.get('page')

    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)

    start_index = (objects.number - 1) * paginator.per_page + 1

    # if applicationid:
    #     return render(request, 'EduDataTable.html', {'objects': objects, 'start_index': start_index})

    # If the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET" and request.GET.get('applicationid'):
        print("AJAX method is activated...")
        return render(request, 'loan_records.html', {'objects': objects, 'start_index': start_index})

    return render(request, 'loan_records.html', {'objects': objects, 'start_index': start_index})



def eduListDemo(request,obj):
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


    # for k in currentStage:
    #     print(k)
    return currentStage

def eduDemo(request):
    return render(request,"Edudemo.html")

def update_record(request, id):
    record = Educationalloan.objects.get(id=id)
    if request.method == 'POST':
        form = EducationalLoanForm(request.POST,request.FILES,instance=record,instance_id=id)
        if form.is_valid():
            form.save()
            return HttpResponse("Updated")
        else:
            print(form.errors)
    else:
        form = EducationalLoanForm(instance=record)
    return render(request, 'EducationLoanUpdate.html', {'form': form})


def viewEducationLoan(request,id):
    record = Educationalloan.objects.get(id=id)
    form = EducationalLoanForm(instance=record)
    return render(request, 'EducationLoanView.html', {'form': form})


@csrf_exempt
def createDocuments(request):

    loanid=None
    if request.session.get('loanid'):
        loanid= request.session.get('loanid')
        
    if request.GET.get('id'):
        loanid=request.GET.get('id')

    
    if request.method=='GET':
       
        form= DocumentsForm()
        return render(request,'CreateDocuments.html',{'form':form})
    else:
       if loanid:
            print(loanid)
            loanObj = get_object_or_404(Educationalloan, id=loanid)

            form = DocumentsForm(request.POST, request.FILES)

            if form.is_valid():
                docObj = form.save(commit=False)
                docObj.loan = loanObj
                docObj.save()
                return HttpResponse('Created Document')
            else:
                # If the form is not valid, re-render the form with errors
                return render(request, 'CreateDocuments.html', {'form': form})
       else:
            # Handle the case where loanid is not in the session
            return HttpResponse('No loan ID exist')
           
      
       
def document_list(request):
      documents = Educationloan_document_upload.objects.all()
      return render(request, 'document_list.html', {'documents': documents})




def updateDocument(request,application_id,loan=None):
    try:
      loan = get_object_or_404(Educationalloan.objects.prefetch_related('personal_details'), application_id=application_id)
      document = loan.personal_details

    except:
        return HttpResponse("No Documents Found...")
    if request.method=='GET':
     form=DocumentsForm(instance=document)
     return render(request,'DocumentUpdate.html',{'form':form})
    
    form = DocumentsForm(request.POST, request.FILES, instance=document)
    if form.is_valid():
        #    docObj = form.save(commit=False)
        #    docObj.loan = loan
        #    docObj.save()
           form.save()
           return HttpResponse('Document Updated')
    else:
        print(form.errors)
        return render(request,'DocumentUpdate.html',{'form':form})
    


def viewDocuments(request,application_id,loan=None):
    try:
      loan = get_object_or_404(Educationalloan.objects.prefetch_related('personal_details'), application_id=application_id)
      document = loan.personal_details
    except:
        return HttpResponse("No Documents Found...")
    
    form=DocumentsForm(instance=document)
    return render(request,'ViewDocument.html',{'form':form})
    


def applicationVerification(request,application_id,loan=None):

    try:
     print("first")
     loan=Educationalloan.objects.get(application_id=application_id)
    except:
        return HttpResponse("No Records Found..")
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
        return render(request, 'ApplicationVerification.html', {'form': form})
    


# def update_verification(request,application_id,loan=None):

#     try:
#         loan=get_object_or_404(Educationalloan.objects.prefetch_related('applicationverification'),application_id=application_id)
#         verifObj=loan.applicationverification

#     except Exception as e:
#         return HttpResponse("No Verification details found...")
    
#     if request.method=='GET':
#         form=ApplicationVerifyForm(instance=verifObj)
#         return render(request,"UpdateVerification.html",{'form':form})
#     else:
#          form = ApplicationVerifyForm(request.POST,instance=verifObj)
#          if form.is_valid():
#            docObj = form.save(commit=False)
#            docObj.loan = loan
#            docObj.save()
#            return HttpResponse('Updated Verification..')
#          else:
#             print(form.errors)
#             return render(request,"UpdateVerification.html",{'form':form})
         

# Anusha Disbursed Form codde Mmixed.....
def update_verification(request, application_id):
    try:
        loan = get_object_or_404(Educationalloan.objects.prefetch_related('applicationverification'), application_id=application_id)
        verifObj = loan.applicationverification
    except Exception as e:
        return HttpResponse("No Verification details found...")

    if request.method == 'GET':
        form = ApplicationVerifyForm(instance=verifObj)
        return render(request, "UpdateVerification.html", {'form': form})
    elif request.method == 'POST':
        form = ApplicationVerifyForm(request.POST, instance=verifObj)
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
            print('Form errors:', form.errors)
            return render(request, "UpdateVerification.html", {'form': form})


# def disbursement_details(request, verification_id):
#     loan = get_object_or_404(Educationalloan, id=verification_id)
    
#     details, created = Edudisbursementdetails.objects.get_or_create(verification=loan)
#     form_status = 'not_submitted'

#     if request.method == 'POST':
#         form = EduDisbursementDetailsForm(request.POST, instance=details)
#         if form.is_valid():
#             form.save()
#             form_status = 'submitted'
#             return redirect('disbursement_summary')  # Redirect to a summary or success page
#         else:
#             print(f"Form errors: {form.errors}")
#     else:
#         form = EduDisbursementDetailsForm(instance=details)

#     return render(request,'disbursement_details.html',{'details_form': form,'form_status': form_status})
         

def Edudisbursement_summary(request):
    details_list = Edudisbursementdetails.objects.all()

    # Optionally, print out the details to verify
    for details in details_list:
        print(f"Details: {details}, Verification ID: {details.verification.id if details.verification else 'No Verification'}")

    return render(request, 'customer/disbursementview.html', {
        'details_list': details_list
    })

        
def customerProfile(request,application_id,loan=None):
     try:
      loan=get_object_or_404(Educationalloan.objects.prefetch_related('applicationverification'),application_id=application_id)
      try:
       verfyObj=loan.applicationverification
      except:
          verfyObj=None
         
     except Exception as e:
         verfyObj=None
         return HttpResponse("No records Found..")
     
     if request.method=='GET':
         email=request.session.get('email')
         if email and email==loan.mail_id:
        #   del request.session['email']
          return render(request,"EduCustomerProfile.html",{'loan':loan,'verfyObj':verfyObj})
         else:
             return HttpResponse("Please login..Login Page")


