# myapp/middleware.py
# from django.shortcuts import redirect

# class OTPMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if not request.user.is_authenticated and not request.path.startswith('/generate-verify-otp/'):
#             return redirect('generate-verify-otp')
#         response = self.get_response(request)
#         return response

from anusha.forms import BasicDetailForm,goldBasicDetailForm,OtherBasicDetailForm
from django.shortcuts import render



class LapAuthMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"Request path: {request.path}")
        print(f"Full URL: {request.build_absolute_uri()}")
        
        if request.path.startswith('/lapapply/') and not request.session.get('lap_id'):
            print("Handling lapapply case")
            form = BasicDetailForm()
            request.session['lap_return_url'] = request.build_absolute_uri()
            return render(request, 'customer/basicdetailform.html', {'form': form})
        
        elif request.path.startswith('/goldloan/') and not request.session.get('gold_id'):
            print("Handling goldloan case")
            form = goldBasicDetailForm()
            request.session['gold_return_url'] = request.build_absolute_uri()
            return render(request, 'customer/goldbasicdetail.html', {'form': form})
        
        elif request.path.startswith('/otherloan/') and not request.session.get('other_id'):
            print("Handling otherloan case")
            form = OtherBasicDetailForm()
            request.session['other_return_url'] = request.build_absolute_uri()
            return render(request, 'customer/otherbasicdetail.html', {'form': form})
            
        else:
    
            print("Request passed through middleware without modification.")
            return self.get_response(request)
