from rest_framework import serializers

from .models import *



class EduDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model=Educationloan_document_upload
        fields=['adhar_card_front']

class EduApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model=ApplicationVerification
        fields=['verification_status']


class EduSerializer(serializers.ModelSerializer):
    personal_details =  EduDocumentSerializer()
    applicationverification = EduApplicationSerializer()

    class Meta:
        model=Educationalloan
        fields=['id','name','application_id','application_loan_type','required_loan_amount','created_at','applicationverification','personal_details']
        
    
    def to_representation(self, instance):
        # Get the original serialized data
        data = super().to_representation(instance)
        
        # Change the key name 'applicationverification' to 'appliverify'
        data['verification'] = data.pop('applicationverification')
        data['documents'] = data.pop('personal_details')
        
        # Similarly, you can rename other keys if needed
        return data