"""
Dispatch Serializers
"""
from rest_framework import serializers
from .models import Vehicle, Route, DispatchHeader, DispatchLine, SalespersonVisit


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'plate', 'capacity', 'driver_name', 'fuel_card',
                  'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class RouteSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Route
        fields = ('id', 'distributor', 'distributor_name', 'day_of_week',
                  'day_of_week_display', 'store_sequence', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class DispatchLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    lot_batch_no = serializers.CharField(source='lot.batch_no', read_only=True)
    dest_store_name = serializers.CharField(source='dest_store.name', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = DispatchLine
        fields = ('id', 'dispatch', 'product', 'product_code', 'product_name',
                  'lot', 'lot_batch_no', 'qty', 'unit_price', 'dest_store',
                  'dest_store_name', 'line_total')
        read_only_fields = ('id', 'dispatch', 'line_total')

    def get_line_total(self, obj):
        return str(obj.line_total)


class DispatchHeaderSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True, default='')
    lines_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    journal_no = serializers.CharField(source='journal.journal_no', read_only=True, default=None)

    class Meta:
        model = DispatchHeader
        fields = ('id', 'dispatch_no', 'distributor', 'distributor_name',
                  'dispatch_date', 'total_qty', 'total_amount', 'status',
                  'status_display', 'vehicle', 'vehicle_plate',
                  'lines_count', 'notes', 'journal', 'journal_no',
                  'created_at')
        read_only_fields = ('id', 'dispatch_no', 'total_qty', 'total_amount',
                          'created_at')

    def get_lines_count(self, obj):
        return obj.lines.count()


class DispatchDetailSerializer(DispatchHeaderSerializer):
    lines = DispatchLineSerializer(many=True, read_only=True)

    class Meta(DispatchHeaderSerializer.Meta):
        fields = DispatchHeaderSerializer.Meta.fields + ('lines',)


class CreateDispatchLineInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    lot_id = serializers.IntegerField(required=False, allow_null=True)
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=4)
    dest_store_id = serializers.IntegerField()


class CreateDispatchInputSerializer(serializers.Serializer):
    distributor_id = serializers.IntegerField()
    dispatch_date = serializers.DateField(required=False)
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = CreateDispatchLineInputSerializer(many=True)


class SalespersonVisitSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = SalespersonVisit
        fields = ('id', 'distributor', 'distributor_name', 'store', 'store_name',
                  'visit_date', 'check_in_time', 'check_out_time',
                  'sales_count', 'sales_amount', 'geo_lat_checkin',
                  'geo_lng_checkin', 'duration_minutes', 'notes', 'created_at')
        read_only_fields = ('id', 'duration_minutes', 'created_at')

    def get_duration_minutes(self, obj):
        return obj.duration_minutes
