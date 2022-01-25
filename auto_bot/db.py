from tortoise import fields
from tortoise.models import Model


class Plate(Model):
    """"""

    id = fields.BigIntField(pk=True, unique=True)
    telegram_user = fields.BigIntField(null=True)
    phone_number = fields.CharField(max_length=12, null=True)
    plate_number = fields.CharField(max_length=9, unique=True, index=True)
