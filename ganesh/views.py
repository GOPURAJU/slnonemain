from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from ganesh.models import *
from ganesh.forms import *
from django.contrib import messages
from django.http import HttpResponse,HttpResponseBadRequest
from django.contrib import auth



import requests
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings

APIID = "AP100034"
TOKEN = "6b549eed-2af0-488c-a2e1-3d10f37f11c6"



def crebasicdetails(request,instance_id=None):
    instance = get_object_or_404(credbasicdetailform, id=instance_id) if instance_id else None
    application_id=None

    if request.method == 'POST':
        form = creditBasicDetailForm(request.POST,request.FILES,instance=instance)
        if form.is_valid():
            user_details = form.save()
            application_id=user_details.application_id
            orderid = str(uuid.uuid4())
            request.session['application_id']=application_id
            
            destinationUrl=reverse('credit')
            request.session['CCafterurl']=destinationUrl
            request.session['ccAppliId']=True
            
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
                return redirect('crefetchcreditreport')
            else:
               return JsonResponse({"status": "error", "message": data.get("mess", "Failed to generate OTP")})
        else:
            print(f'{form.errors}')
    else:
        form = creditBasicDetailForm()

    return render(request, 'credbasicdetail.html', {'form': form})
def cre_fetch_credit_report(request):
    otp=request.session.get('otp')
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_details = credbasicdetailform.objects.get(id=user_id)
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
                    loan_application = CreditDetail.objects.filter(basicdetailform=user_details).first()
                    if loan_application:
                        loan_application.credit_score = credit_score
                        loan_application.save()
                    return render(request, 'crecibil_score.html', {'credit_score': credit_score, 'application_id': user_details.application_id})
            else:
                return JsonResponse({"status": "error", "message": data["mess"]})
        else:
            return JsonResponse({"status": "error", "message": "Failed to fetch credit report"})

    return render(request, 'credbasicdetail.html',{'otp':otp})




   

# def credit_add(request):
#     if request.session.get('application_step')!='credit':
#         return redirect('crebasicdetail')
#     application_id=request.session.get('application_id')

#     basic_detail_instance = get_object_or_404(credbasicdetailform, application_id=application_id)

    
#     print(f"Basic detail instance: {basic_detail_instance}")
    
#     if application_id:
#         try:
#             customer_profile = creditDetail.objects.get(basicdetailform=basic_detail_instance)
#             print(f"Found customer_profile: {customer_profile}")
#         except creditDetail.DoesNotExist:
#             customer_profile = creditDetail(basicdetailform=basic_detail_instance)
#             print("Created new customer_profile")
#     else:
#         customer_profile = None

#     if request.method == 'POST':
#         form = CreditDetailForm(request.POST, request.FILES, instance=customer_profile)
#         if form.is_valid():
#             loan_application = form.save(commit=False)
#             if not loan_application.basicdetailform:
#                 return HttpResponseBadRequest("basic_detail_id cannot be null.")
#             if credbasicdetailform:
#                loan_application.mobile_number = basic_detail_instance.phone_number
            
#             loan_application.save()
#             request.session['application_step'] = 'document_detail'

#             return redirect('document_detail', application_id=application_id)
#         else:
#             print(f"Form errors: {form.errors}")  
#     else:
#         form = CreditDetailForm(instance=customer_profile)
        
#         if not customer_profile and basic_detail_instance:
#             form.initial['mobile_number'] = basic_detail_instance.phone_number

#     return render(request, 'credit_applia_form.html', {
#         'form': form,
#         'basic_mobile_number': basic_detail_instance.phone_number
#     })





# def credit_add(request):
#     mobile_number = request.session.get('mobile_number')  
    
#     refCode=None
#     francrefCode=None
#     if request.GET.get('refCode'):
#         print(request.GET.get('refCode'))
#         refCode=request.GET.get('refCode')
#     if request.GET.get('franrefCode'):
#        francrefCode=request.GET.get('franrefCode')

#     if request.method == 'POST':
#         form = CreditDetailForm(request.POST, request.FILES)
#         if form.is_valid():
#             loan = form.save(commit=False)  
            
        
#             if refCode:
#               if refCode.startswith('SLNDSA'):
#                  loan.dsaref_code=refCode
#                  loan.franrefCode=francrefCode
#               elif refCode.startswith('SLNEMP'):
#                  loan.empref_code=refCode
#                  loan.franrefCode=francrefCode
#             else:
#                  loan.franrefCode=francrefCode

#             try:
#                 mobile_number_int = int(mobile_number) if mobile_number else None
#                 if mobile_number_int is None:
#                     print("Mobile number is not found in session.")  
#                     return redirect('crebasicdetail')

#                 print("Attempting to find basic detail with mobile number:", mobile_number_int)  

#                 lap = credbasicdetailform.objects.filter(phone_number=mobile_number_int).first()
                
#                 if lap:
#                     print("Basic Detail Object Retrieved:", lap)

#                     if CreditDetail.objects.filter(basicdetailform=lap).exists():
#                         print("This BasicDetail already has a LoanApplication.")
#                         return redirect('error_page', message="This DEtails already has an associated Loan Application.")
                    
#                     loan.basicdetailform = lap
#                     loan.mobile_number = str(lap.phone_number)
#                     loan.application_id = lap.application_id
#                     loan.save()  
#                     request.session['loanid'] = loan.id
                    
                
#                     if refCode:
#                          if refCode.startswith('SLNDSA'):
#                              EducommonDsaLogic(request,refCode,loan)
                
#                          elif refCode.startswith('SLNEMP'):
#                             eduSalesLogic(request,refCode,loan)
                
#                     elif francrefCode:
#                        print("Franchise Logic")
                       
               
#                     destinationUrl=reverse('document_add', kwargs={'application_id': lap.application_id})
#                     request.session['CCafterurl']=destinationUrl
           

                    
#                     return redirect('document_add', application_id=lap.application_id)
#                 else:
#                     print("No matching basic detail found for this phone number.")  
#                     return redirect('crebasicdetail')

#             except ValueError:
#                 print("Invalid mobile number format.")  
#                 return redirect('crebasicdetail')

#     else:
#         form = CreditDetailForm()

#     return render(request, 'credit_applia_form.html', {'form': form, 'mobile_number':mobile_number})






def credit_add(request):
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
        form = CreditDetailForm(request.POST, request.FILES)
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
                mobile_number_int = int(mobile_number) if mobile_number else None
                if mobile_number_int is None:
                    print("Mobile number is not found in session.")  
                    return redirect('crebasicdetail')

                print("Attempting to find basic detail with mobile number:", mobile_number_int)  

                lap = credbasicdetailform.objects.filter(phone_number=mobile_number_int).first()
                
                if lap:
                    print("Basic Detail Object Retrieved:", lap)

                    if CreditDetail.objects.filter(basicdetailform=lap).exists():
                        print("This BasicDetail already has a LoanApplication.")
                        return redirect('error_page', message="This DEtails already has an associated Loan Application.")
                    
                    loan.basicdetailform = lap
                    loan.mobile_number = str(lap.phone_number)
                    loan.application_id = lap.application_id
                    loan.save()  
                    request.session['loanid'] = loan.id
                    
                    
 # Bhanu
                    if refCode:
                         if refCode.startswith('SLNDSA'):
                             EducommonDsaLogic(request,refCode,loan)
                
                         elif refCode.startswith('SLNEMP'):
                            eduSalesLogic(request,refCode,loan)
                
                    elif francrefCode:
                       print("Franchise Logic")
                       
               
                    destinationUrl=reverse('document_add', kwargs={'application_id': lap.application_id})
                    request.session['CCafterurl']=destinationUrl
           
#Bhanu

                    
                    return redirect('document_add', application_id=lap.application_id)
                else:
                    print("No matching basic detail found for this phone number.")  
                    return redirect('crebasicdetail')

            except ValueError:
                print("Invalid mobile number format.")  
                return redirect('crebasicdetail')

    else:
        form = CreditDetailForm()

    return render(request, 'credit_applia_form.html', {'form': form, 'mobile_number':mobile_number})


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
# Bhanu


















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






def credit_document_add(request, application_id):
    # Fetch the related instances
    basicdetailform = get_object_or_404(credbasicdetailform, application_id=application_id)
    personal_details = get_object_or_404(CreditDetail, basicdetailform=basicdetailform)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)  # Create a new record, but don't save yet
            print(f"Personal Details ID: {personal_details.id}")
            instance.personal_detail = personal_details
            instance.save()  # Save the instance with the related personal details

            return redirect('ccsuccess',application_id=application_id)  # Redirect after saving
        else:
            print(f"Form errors: {form.errors}")  # Print errors to console for debugging
    else:
        form = DocumentUploadForm()

    return render(request, 'cred_document_upload_form.html', {
        'form':form,
})










def update_cred_detail_view(request, pk):
    customer_profile = get_object_or_404(CreditDetail, pk=pk)
    if request.method == 'POST':
        form = CreditDetailForm(request.POST, instance=customer_profile)
        if form.is_valid():
            form.save()
            # Redirect to update_lapdoc with the instance_id of the updated loan application
            return redirect('update_document', instance_id=customer_profile.id)
    else:
        form = CreditDetailForm(instance=customer_profile)

    return render(request, 'credit_applia_form.html', {'form': form,})

def update_cred_document_detail_view(request, instance_id):
    personal_details = get_object_or_404(CreditDetail, id=instance_id)
    
    try:
        applicant_document = creditDocumentUpload.objects.get(id=instance_id)
    except creditDocumentUpload.DoesNotExist:
        applicant_document = None    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=applicant_document)
        if form.is_valid():
            form.save()
            return redirect('ccsuccess')
        else:
            print('Form errors:', form.errors)
    else:
        form = DocumentUploadForm(instance=applicant_document)

    return render(request, 'credit_update_doc.html', {
        'form': form,
       
    })



def credit_table_view(request):
    personal_details = CreditDetail.objects.all()
    return render(request, 'credit_table_view.html', {'personal_details': personal_details})

def view_credit_appli(request, pk):
    personal_detail = get_object_or_404(CreditDetail, pk=pk)
    return render(request, 'view_credit_aplli.html', {'personal_detail': personal_detail})


def view_credit_documents(request):
    document_upload = get_object_or_404(creditDocumentUpload)
    return render(request, 'view_documents.html', {'document_upload': document_upload})

def ccsuccess(request, application_id):
    application = get_object_or_404(CreditDetail, basicdetailform__application_id=application_id)
    context = {
        'application': application,
        'application_id': application_id,
        
        
    }
    return render(request, 'ok.html', context)
