from rest_framework import viewsets
from .lapserializers import *
from .models import *
from django.http import JsonResponse
from rest_framework.response import Response



class LapViewSet(viewsets.ModelViewSet):
    queryset=LoanApplication.objects.all()
    serializer_class=LoanApplicationSerializer

    def get_disbursement_details(self,request):
        queryset=LoanApplication.objects.filter(disbursementdetail__isnull=False).distinct()
        serializer = LoanApplicationSerializer(queryset, many=True)
    
        return Response(serializer.data)
        
        


class goldviewset(viewsets.ModelViewSet):
    queryset=Goldloanapplication.objects.all()
    serializer_class=goldapplicationSerializer

class otherviewset(viewsets.ModelViewSet):
    queryset=otherloans.objects.all()
    serializer_class=otherloanSerializer

class dsaViewSet(viewsets.ModelViewSet):
    queryset=dsa.objects.all()
    serializer_class=dsaSerializer

class franchiseViewSet(viewsets.ModelViewSet):
    queryset=franchise.objects.all()
    serializer_class=franchiseSerializer