from django.http import JsonResponse
from rest_framework import generics,viewsets,status
from .Busi_serializers import BusiSerializer,BusiBasicDetailFormSrializer
from .models import *
from django.http import HttpResponse
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.decorators import action



class BusiBasicDetailviewset(viewsets.ModelViewSet):
    queryset=busbasicdetailform.objects.all()
    serializer_class=BusiBasicDetailFormSrializer


    def getApplicationId(self,request, mobileNumber):
        try:
            queryset = busbasicdetailform.objects.filter(mobile_number=mobileNumber)
            if queryset.exists():
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data, status=200)
            else:
                return Response({"message": "No records found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class BusiViewsets(viewsets.ModelViewSet):
    queryset=BusinessLoan.objects.all()
    serializer_class=BusiSerializer

    def getByRefCode(self, request, refCode):
        try:
            queryset = BusinessLoan.objects.filter(
                Q(dsaref_code__icontains=refCode) |
               Q(franrefCode__icontains=refCode)  |
               Q(empref_code=refCode)  
                 ).prefetch_related('BussinessLoandocuments', 'applicationverification')
            if queryset.exists():
               
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data, status=200)
            else:
                return Response({"message": "No records found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    def getApprovedRecords(self, request, refCode):
      try:
        queryset = BusinessLoan.objects.filter(
        Q(dsaref_code__icontains=refCode) |
        Q(franrefCode__icontains=refCode) |
        Q(empref_code=refCode),
        applicationverification__verification_status='Approved'  
       ).select_related('BussinessLoandocuments', 'applicationverification')
        
        if queryset.exists():
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response({"message": "No approved records found"}, status=404)

      except Exception as e:
        return Response({"error": str(e)}, status=500)
     
    def getRejectedRecords(self, request, refCode):
     try:
        queryset = BusinessLoan.objects.filter(
        Q(dsaref_code__icontains=refCode) |
        Q(franrefCode__icontains=refCode) |
        Q(empref_code=refCode),
        applicationverification__verification_status='Rejected'  
       ).select_related('BussinessLoandocuments', 'applicationverification')
        
        if queryset.exists():
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response({"message": "No approved records found"}, status=404)

     except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    
    
    
    @action(detail=True, methods=['get'])
    def business_loan_refCode_LoansCount(self, request, pk=None):
        countValue=BusinessLoan.objects.filter(Q(dsaref_code=pk)|Q(franrefCode=pk)|Q(empref_code=pk)).count()
        return Response({'count': countValue}, status=200)
    
    @action(detail=True, methods=['get'])
    def business_loan_refcode_ApprovedCount(self,request, pk=None):
        countValue=BusinessLoan.objects.filter(Q(dsaref_code=pk)|Q(franrefCode=pk)|Q(empref_code=pk),applicationverification__verification_status='Approved').count()
        return Response({'count': countValue}, status=200)
    
    @action(detail=True, methods=['get'])
    def business_loan_refcode_RejectedCount(self,request, pk=None):
        countValue=BusinessLoan.objects.filter(Q(dsaref_code=pk)|Q(franrefCode=pk)|Q(empref_code=pk),applicationverification__verification_status='Rejected').count()
        return Response({'count': countValue}, status=200)
    
        
    
    
    
    
        
        
        
    


