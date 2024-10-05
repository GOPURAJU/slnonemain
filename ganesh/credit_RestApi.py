from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .credit_serializers import credbasicdetailformserializers, creditDetailserializers
from .models import credbasicdetailform, CreditDetail
from django.db.models import Q


class credbasicdetailformviewsets(viewsets.ModelViewSet):
    queryset = credbasicdetailform.objects.all()
    serializer_class = credbasicdetailformserializers

    @action(detail=False,methods=['get'],url_path='application-id/(?P<mobileNumber>\d+)')
    def get_application_id(self, request, mobileNumber=None):
        try:
            queryset = credbasicdetailform.objects.filter(mobile_number=mobileNumber)
            if queryset.exists():
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No records found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class creditDetailviewsets(viewsets.ModelViewSet):
#     queryset = CreditDetail.objects.all()
#     serializer_class = credbasicdetailformserializers


#     @action(detail=False,methods=['get'],url_path='by-ref-code/(?P<refCode>[^/]+)')
#     def get_by_ref_code(self, request, refCode=None):
#         try:
#             queryset = CreditDetail.objects.filter(
#                 Q(dsaref_code__icontains=refCode) |
#                 Q(franrefCode__icontains=refCode) |
#                 Q(empref_code=refCode)
#             ).prefetch_related('creditDocumentUpload')
#             if queryset.exists():
#                 serializer = self.get_serializer(queryset, many=True)
#                 return Response(serializer.data, status=status.HTTP_200_OK)
#             else:
#                 return Response({"message": "No records found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class creditDetailviewsets(viewsets.ModelViewSet):
    queryset = CreditDetail.objects.all()
    serializer_class = credbasicdetailformserializers
    
    @action(detail=True, methods=['get'])
    def business_loan_refCode_LoansCount(self, request, pk=None):
        countValue=CreditDetail.objects.filter(Q(dsaref_code=pk)|Q(franrefCode=pk)|Q(empref_code=pk)).count()
        return Response({'count': countValue},status=200)