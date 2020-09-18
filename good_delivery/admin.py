from django.contrib import admin

from . admin_inlines import *
from . models import *


@admin.register(DeliveryCampaign)
class DeliveryCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_start', 'date_end',
                    'require_agreement', 'is_active')
    list_filter = ('date_start', 'date_end',
                   'require_agreement', 'is_active')
    search_fields = ('name',)
    

@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ('campaign','name','location','notes','is_active')
    list_filter = ('campaign__name', 'is_active')
    search_fields = ('campaign__name','name','location')
    inlines = [OperatorDeliveryPointInline]


@admin.register(OperatorDeliveryPoint)
class OperatorDeliveryPointAdmin(admin.ModelAdmin):
    list_display = ('delivery_point','operator', 'create')
    list_filter = ('delivery_point__campaign','delivery_point__name', 'create')
    search_fields = ('operator__user__first_name','operator__user__last_name','delivery_point__name')


@admin.register(UserDeliveryPoint)
class UserDeliveryPointAdmin(admin.ModelAdmin):
    list_display = ('delivery_point','user')
    list_filter = ('delivery_point__campaign','delivery_point__name')
    search_fields = ('user__first_name','user__last_name','delivery_point__name')


@admin.register(GoodCategory)
class GoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name','description')
    inlines = [GoodInline,]


# @admin.register(Good)
class GoodAdmin(admin.ModelAdmin):
    list_display = ('name','category')
    list_filter = ('category__name',)
    search_fields = ('name','category__name')


@admin.register(DeliveryPointGoodStock)
class DeliveryPointGoodStockAdmin(admin.ModelAdmin):
    list_display = ('delivery_point','good','max_number')
    list_filter = ('delivery_point__campaign__name','delivery_point__name','good__name')
    search_fields = ('delivery_point__campaign__name','delivery_point__name','good__name')
    inlines = [DeliveryPointGoodStockIdentifierInline, ]

# @admin.register(DeliveryPointGoodStockIdentifier)
class DeliveryPointGoodStockIdentifierAdmin(admin.ModelAdmin):
    list_display = ('delivery_point_stock','good_identifier')
    list_filter = ('delivery_point_stock',)
    search_fields = ('delivery_point_stock','good_identifier')


@admin.register(GoodDelivery)
class GoodDeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivered_to', 'created_by', 'create', 'modified')
    list_filter = ('delivered_to',)
    search_fields = ('delivered_to',)
    inlines = [GoodDeliveryAgreementInline,]

# @admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('name', 'description', 'is_active')
    search_fields = ('name', 'description')
