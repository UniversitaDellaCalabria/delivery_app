import json
import logging

from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _

from ckeditor.fields import RichTextField

from . jwts import *


logger = logging.getLogger(__name__)


def _attachment_upload(instance, filename):
    """
    this function has to return the location to upload the file
    """
    folder = instance.get_folder()
    return os.path.join('{}/{}'.format(folder, filename))


class TimeStampedModel(models.Model):
	create = models.DateTimeField(auto_now_add=True)
	modified =  models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class DeliveryCampaign(TimeStampedModel):
    """
    bando di consegna beni
    """
    name = models.CharField(max_length=255,
                            help_text=_('Campagna di consegne'),
                            unique=True)
    slug = models.SlugField(max_length=255,
                            blank=False, null=False, unique=True,
                            validators=[
                                RegexValidator(
                                    regex='^(?=.*[a-zA-Z])',
                                    message=_("Lo slug deve contenere "
                                              "almeno un carattere alfabetico"),
                                    code='invalid_slug'
                                ),
                            ])
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    require_agreement = models.BooleanField(default=True)
    operator_can_create = models.BooleanField(default=True)
    new_delivery_if_disabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    note_operator = models.TextField(help_text=_('Notes to operators'),
                                     blank=True, null=True)
    note_users = models.TextField(help_text=_('Notes to users'),
                                     blank=True, null=True)

    class Meta:
        verbose_name = _('Campagna di consegne')
        verbose_name_plural = _('Campagne di consegne')

    # @property
    def is_in_progress(self):
        # return self.date_start <= timezone.localtime() and
        return self.date_end > timezone.localtime()

    def __str__(self):
        return '{}'.format(self.name)


class DeliveryPoint(TimeStampedModel):
    """
    punto di consegna
    """
    campaign = models.ForeignKey(DeliveryCampaign, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text=_('Denominazione'))
    location = models.TextField(max_length=511)
    notes = models.TextField(max_length=511, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Punto di consegna')
        verbose_name_plural = _('Punti di consegna')

    def __str__(self):
        return '({}) {}'.format(self.campaign, self.name)


class OperatorDeliveryPoint(TimeStampedModel):
    """
    operatore di un punto di raccolta
    """
    operator = models.ForeignKey(get_user_model(),
                                 on_delete=models.CASCADE)
    delivery_point = models.ForeignKey(DeliveryPoint,
                                       on_delete=models.CASCADE)
    multi_tenant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Operatore')
        verbose_name_plural = _('Operatori')

    def __str__(self):
        return '{} - {}'.format(self.operator, self.delivery_point)


class GoodCategory(TimeStampedModel):
    """
    """
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('Categoria Bene/Servizio')
        verbose_name_plural = _('Categorie Beni/Servizi')

    def __str__(self):
        return '{}'.format(self.name)


class Good(TimeStampedModel):
    """
    qualsiasi tipo di prodotto da assegnare
    """
    category = models.ForeignKey(GoodCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = _('Bene/Servizio')
        verbose_name_plural = _('Beni/Servizi')

    def __str__(self):
        return '[{}] {}'.format(self.category, self.name)


class DeliveryPointGoodStock(TimeStampedModel):
    delivery_point = models.ForeignKey(DeliveryPoint,
                                       on_delete=models.CASCADE)
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    max_number = models.IntegerField(default=0,
                                     help_text=_("0 for unlimited"))

    class Meta:
        unique_together = ("good", "delivery_point")
        verbose_name = _('Stock beni centro di consegna')
        verbose_name_plural = _('Stock beni centri di consegna')

    def __str__(self):
        return '{} - {}'.format(self.delivery_point, self.good)


class DeliveryPointGoodStockIdentifier(TimeStampedModel):
    """
    identificativo bene presente in stock
    """
    delivery_point_stock = models.ForeignKey(DeliveryPointGoodStock,
                                             on_delete=models.CASCADE)
    good_identifier = models.CharField(max_length=255, blank=True, null=True,
                                       help_text=_('Identificativo del prodotto/servizio'))

    class Meta:
        verbose_name = _('Identificativo bene in stock')
        verbose_name_plural = _('Identificativi beni in stock')

    def __str__(self):
        return '{} - {}'.format(self.delivery_point_stock,
                                self.good_identifier)


class GoodDelivery(TimeStampedModel):
    """
    assegnazione di un prodotto a un utente, da parte di un operatore
    """
    # autofilled from delivery_point on save()
    campaign = models.ForeignKey(DeliveryCampaign,
                                 on_delete=models.CASCADE,
                                 blank=True, null=True)
    choosen_delivery_point = models.ForeignKey(DeliveryPoint,
                                               on_delete=models.PROTECT,
                                               related_name="choosen_delivered_point")
    delivered_to = models.ForeignKey(get_user_model(),
                                     on_delete=models.PROTECT)
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    good_stock_identifier = models.ForeignKey(DeliveryPointGoodStockIdentifier,
                                              blank=True, null=True,
                                              on_delete=models.CASCADE)
    # se non è presente un identificativo in stock
    # ma l'operatore deve specificarlo per check
    good_identifier = models.CharField(max_length=255, blank=True, null=True)
    delivery_point = models.ForeignKey(DeliveryPoint,
                                       on_delete=models.PROTECT,
                                       blank=True, null=True,
                                       related_name="delivered_point")
    delivery_date = models.DateTimeField(_('Data di consegna'),
                                         blank=True, null=True)
    delivered_by = models.ForeignKey(get_user_model(),
                                     on_delete=models.PROTECT,
                                     blank=True, null=True,
                                     related_name="delivered_by")
    disabled_point = models.ForeignKey(DeliveryPoint,
                                       on_delete=models.PROTECT,
                                       blank=True, null=True,
                                       related_name="disabled_point")
    disabled_date = models.DateTimeField(_('Data di disabilitazione'),
                                         blank=True, null=True)
    disabled_by = models.ForeignKey(get_user_model(),
                                    on_delete=models.PROTECT,
                                    blank=True, null=True,
                                    related_name="disabled_by")
    returned_point = models.ForeignKey(DeliveryPoint,
                                       on_delete=models.PROTECT,
                                       blank=True, null=True,
                                       related_name="returned_point")
    return_date = models.DateTimeField(_('Data di restituzione'),
                                       blank=True, null=True)
    returned_to = models.ForeignKey(get_user_model(),
                                    on_delete=models.PROTECT,
                                    blank=True, null=True,
                                    related_name="returned_to")
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('Consegna prodotto')
        verbose_name_plural = _('Consegne prodotti')

    def get_stock(self):
        stock = DeliveryPointGoodStock.objects.filter(delivery_point=self.delivery_point,
                                                      good=self.good).first()
        return stock

    def check_quantity(self):
        if self.quantity == 0:
            raise Exception(_("La quantità non può essere 0"))

    def check_stock_max(self):
        # only 1 good is identified by unique code
        if self.good_identifier and self.quantity>1:
            raise Exception(_("La quantità associata a un codice identificativo "
                              "non può essere maggiore di 1"))

        # stock max number check
        if not self.pk:
            stock = self.get_stock()
            actual_stock_deliveries = GoodDelivery.objects.filter(good=self.good).count()
            if stock.max_number > 0 and stock.max_number-actual_stock_deliveries<self.quantity:
                raise Exception(_("Raggiunto il numero max di consegne per questo stock: "
                                  "{}").format(stock.max_number))

    def check_identification_code(self):
        stock = self.get_stock()
        stock_identifiers = DeliveryPointGoodStockIdentifier.objects.filter(delivery_point_stock=stock)
        if stock_identifiers and not self.good_stock_identifier:
            raise Exception(_("Selezionare il codice identificativo dalla lista"))

    def validate_stock_identifier(self):
        # good identifiers
        stock_id = self.good_stock_identifier
        manual_id = self.good_identifier
        # only one identifier is permitted
        if stock_id:
            if not manual_id or manual_id != stock_id.good_identifier:
                raise Exception(_("Identificatori non coincidenti"))

    def check_collisions(self):
        """
            if operator is editing a delivery (self.pk exists)
            we can exclude it from deliveries list
        """
        # check if there is an existent delivery
        # (same good, same id, same campaign)
        existent_delivery = GoodDelivery.objects.filter(Q(good_stock_identifier=self.good_stock_identifier) &
                                                        Q(good_stock_identifier__isnull=False) |
                                                        Q(good_identifier=self.good_identifier) &
                                                        Q(good_identifier__isnull=False),
                                                        good=self.good,
                                                        campaign=self.campaign)
                                                        # return_date__isnull=True)
        if self.pk:
            existent_delivery = existent_delivery.exclude(pk=self.pk)
            # existent_delivery = existent_delivery.first()
            # if there is a delivery with same good code
            # (same good, same id, same campaign)
            # save operation is not permitted!

        if existent_delivery:
            raise Exception(_("Esiste già una consegna di questo prodotto, "
                              "per questa campagna, "
                              "con questo codice identificativo"))

    def save(self, *args, **kwargs):
        self.campaign = self.campaign or self.delivery_point.campaign
        self.check_quantity()
        if self.delivery_point:
            self.check_stock_max()
            self.check_identification_code()
            self.validate_stock_identifier()
        self.check_collisions()
        super(GoodDelivery, self).save(*args, **kwargs)


    def log_action(self, msg, action, user):
        LogEntry.objects.log_action(user_id         = user.pk,
                                    content_type_id = ContentType.objects.get_for_model(self).pk,
                                    object_id       = self.pk,
                                    object_repr     = self.__str__(),
                                    action_flag     = action,
                                    change_message  = msg)
        logger.info(msg)

    def get_year(self):
        return self.create.year

    def build_jwt(self):
        data = {'id': self.pk,
                'user': self.delivered_to.pk,
                'delivery_point': self.delivery_point.pk,
                'modified': self.modified}
        encrypted_data = encrypt_to_jwe(json.dumps(data).encode())
        return encrypted_data

    def is_waiting(self):
        if self.delivery_date: return False
        if self.return_date: return False
        if self.disabled_date: return False
        return True

    def can_be_returned(self):
        if not self.delivery_date: return False
        if self.return_date: return False
        return True

    def can_be_disabled(self):
        if self.disabled_date: return False
        return True

    def can_be_deleted(self):
        if self.delivery_date: return False
        if self.disabled_date: return False
        user_deliveries = GoodDelivery.objects.filter(campaign=self.campaign,
                                                      delivered_to=self.delivered_to,
                                                      good=self.good,
                                                      delivery_point=self.delivery_point).count()
        # if good_delivery has been prefilled
        # (not created by operator)
        # operators can't delete it
        if not self.campaign.operator_can_create and user_deliveries==1:
            return False
        return True

    def can_be_marked_by_operator(self):
        # marked as delivered by operator
        # without user confirmation
        return not self.campaign.require_agreement and self.delivered_by and self.is_waiting()

    def can_be_marked_by_user(self):
        """
        marked as delivered by user action
        """
        if not self.delivery_point: return False
        if not self.campaign.is_in_progress(): return False
        if not self.campaign.require_agreement: return False
        return self.is_waiting()

    @property
    def state(self):
        if self.disabled_date:
            return _('disabilitata')
        elif self.return_date:
            return _('restituito')
        elif self.delivery_date:
            return _('consegnato')
        elif not self.delivery_point:
            return _('da definire')
        elif self.is_waiting():
            return _('in attesa')
        else:
            return _('unknown')

    def __str__(self):
        return '{} - {}'.format(self.delivered_to, self.good)

    # TODO save()

    # check relazioni user e product con DeliveryPoint
    # ----------------------------------------------
    # per verificare la consistenza dei dati e l'effettiva
    # corrispondenza e validità dell'operazione


class Agreement(TimeStampedModel):
    """
    accettazione condizioni
    """
    name = models.CharField(max_length=255)
    # description = models.TextField(max_length=1023)
    description = RichTextField(max_length=1023)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Agreement')
        verbose_name_plural = _('Agreements')

    def __str__(self):
        return '{}'.format(self.name)


class DeliveryCampaignAgreement(TimeStampedModel):
    """
    agreement associato a una consegna
    """
    campaign = models.ForeignKey(DeliveryCampaign,
                                 on_delete=models.PROTECT)
    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Agreement consegna')
        verbose_name_plural = _('Agreement consegne')

    def __str__(self):
        return '{} - {}'.format(self.campaign, self.agreement)


class GoodDeliveryAttachment(TimeStampedModel):
    """
    documenti allegati a consegna bene
    """
    good_delivery = models.ForeignKey(GoodDelivery,
                                      on_delete=models.PROTECT)
    attachment = models.FileField(upload_to=_attachment_upload,
                                  null=True, blank=True,
                                  max_length=255)

    class Meta:
        verbose_name = _('Allegato consegna bene')
        verbose_name_plural = _('Allegati consegne beni')

    def get_folder(self):
        """
        returns GoodDelivery attachments folder
        """
        folder = '{}/{}/{}'.format('good_deliveries',
                                   self.good_delivery.get_year(),
                                   self.good_delivery.pk)
        return folder

    def __str__(self):
        return '{} - {}'.format(self.good_delivery, self.attachment)
