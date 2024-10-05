from django.http import JsonResponse
from rest_framework import generics,viewsets,status


from anusha.InsuranceSerializers import AllInsuranceSerializer,LifeInsuranceSerializer,HealthInsuranceSerializer,GeneralInsuranceSerializer
from .models import *
from django.http import HttpResponse
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.decorators import action



class AllInsuViewsets(viewsets.ModelViewSet):
    queryset=AllInsurance.objects.all()
    serializer_class=AllInsuranceSerializer


class LifeInsuViewsets(viewsets.ModelViewSet):
    queryset=LifeInsurance.objects.all()
    serializer_class=LifeInsuranceSerializer
    
    
class GeneralInsuViewsets(viewsets.ModelViewSet):
    queryset=GeneralInsurance.objects.all()
    serializer_class=GeneralInsuranceSerializer
    

class HealthInsuViewsets(viewsets.ModelViewSet):
    queryset=healthInsurance.objects.all()
    serializer_class=HealthInsuranceSerializer

# bhanu

