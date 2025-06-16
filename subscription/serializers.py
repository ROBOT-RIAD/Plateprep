from rest_framework import serializers
from .models import Package

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'
        read_only_fields = ['price_id', 'product_id']
    
    # def to_representation(self, instance):
    #     rep = super().to_representation(instance)
    #     rep['amount'] = instance.amount / 100 if instance.amount else 0.0  # cents → dollars
    #     return rep

    # def to_internal_value(self, data):
    #     internal = super().to_internal_value(data)
    #     if 'amount' in data:
    #         internal['amount'] = int(float(data['amount']) * 100)  # dollars → cents
    #     return internal