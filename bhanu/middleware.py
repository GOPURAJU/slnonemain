# yourapp/middleware.py

from django.shortcuts import render

from anusha.forms import BasicDetailForm, OtherBasicDetailForm, goldBasicDetailForm
from anusha.models import basicdetailform
from bhanu.forms import eduBasicDetailForm
from business.forms import busBasicDetailForm
from ganesh.forms import creditBasicDetailForm
from seetha.forms import CLBasicDetailForm
from ravi.forms import plBasicDetailForm,HomeBasicDetailForm



class XFrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        print("Custom X-Frame-Options Middleware executed")  # Debug print
        response['X-Frame-Options'] = 'SAMEORIGIN'  # or 'ALLOW-FROM http://example.com'
        return response



class AuthMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        # self.protected_paths = getattr(settings, 'PROTECTED_PATHS', [])

    def __call__(self, request):
        print(request.path) #dsa/allLoans
        print("Im Middleware1")
        # del request.session['Eduafterurl']
        # print(request.session.get('Eduafterurl'))
        
        if request.GET.get('refCode') or request.GET.get('franrefCode'):
            request.session['frmDSAFranch']="Access"
        
        if request.path.startswith('/el/apply-educationalLoan') and not request.session.get('eduAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = eduBasicDetailForm()
            request.session['eduUrl']=request.build_absolute_uri()
            return render(request,'ebasicdetail.html',{'form':form})
        
        elif request.path.startswith('/bl/demo') and not request.session.get('busiAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = busBasicDetailForm()
            request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'busbasicdetail.html',{'form':form})
       
        elif request.path.startswith('/lapapply/') and not request.session.get('lapAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = BasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'customer/basicdetailform.html',{'form':form})
        
        elif request.path.startswith('/goldloan/') and not request.session.get('goldAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = goldBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'customer/goldbasicdetail.html',{'form':form})
            
                
        elif request.path.startswith('/cl/car-loan-application/') and not request.session.get('carAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = CLBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'carbasicdetailform.html',{'form':form})
        
        # elif request.path.startswith('/cl/car-loan-application/') and not request.session.get('carAppliId') and not request.session.get('frmDSAFranch'):
        #     print(request.build_absolute_uri())
        #     form = CLBasicDetailForm()
        #     # request.session['busiUrl']=request.build_absolute_uri()
        #     return render(request,'carbasicdetailform.html',{'form':form})
        
        elif request.path.startswith('/cc/credit/') and not request.session.get('ccAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = creditBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'credbasicdetail.html',{'form':form})
        
        elif request.path.startswith('/otherloan/') and not request.session.get('otherAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = OtherBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'otherbasicdetail.html',{'form':form})
        elif request.path.startswith('/pl/personal/') and not request.session.get('plAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            print("kkPerso")
            form = plBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'admin/basic.html',{'form':form})
        elif request.path.startswith('/pl/home/') and not request.session.get('hmAppliId') and not request.session.get('frmDSAFranch'):
            print(request.build_absolute_uri())
            form = HomeBasicDetailForm()
            # request.session['busiUrl']=request.build_absolute_uri()
            return render(request,'admin/hlbasic.html',{'form':form})
        
        
       
        else:
            # del request.session['eduAppliId']
            
            # del request.session['busiAppliId']
            # del request.session['frmDSAFranch']
            # del request.session['Eduafterurl']
            # del request.session['lapAppliId']
            # del request.session['goldAppliId']
            # del request.session['carAppliId']
            # request.session.clear()
            
            return self.get_response(request)