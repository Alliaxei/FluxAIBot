from django.db import models


class AlembicVersion(models.Model):
    version_num = models.CharField(primary_key=True, max_length=32)

    class Meta:
        managed = False
        db_table = 'alembic_version'


class Gallery(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING)
    prompt = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField()
    image_path = models.CharField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    image_url = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gallery'


class Settings(models.Model):
    user = models.OneToOneField('Users', models.DO_NOTHING)
    selected_style = models.CharField(max_length=50, blank=True, null=True)
    image_size = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'settings'


class TokenTransactions(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING)
    amount = models.IntegerField()
    transaction_date = models.DateTimeField()
    transaction_type = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'token_transactions'


class Transactions(models.Model):
    user = models.ForeignKey('Users', models.DO_NOTHING)
    amount = models.IntegerField()
    # transaction_date = models.DateTimeField()
    transaction_type = models.CharField(max_length=15)
    order_id = models.CharField(unique=True, max_length=50)
    transaction_status = models.CharField(max_length=15)
    class Meta:
        managed = False
        db_table = 'transactions'


class Users(models.Model):
    telegram_id = models.BigIntegerField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    credits = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'users'
