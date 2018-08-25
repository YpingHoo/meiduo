from django.db import models


# Create your models here.

class Area(models.Model):
    name = models.CharField(max_length=20, verbose_name="名称")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, related_name="subs", null=True, blank=True,
                               verbose_name="上级行政区域")

    class Meta:
        db_table = "tb_areas"
        verbose_name = "行政区域"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name