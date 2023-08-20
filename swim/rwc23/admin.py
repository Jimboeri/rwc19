from django.contrib import admin

# Register your models here.
#from rwc23.models import Profile, Team, Game, Prediction
import rwc23.models

admin.site.register(rwc23.models.Profile)
admin.site.register(rwc23.models.Team)
admin.site.register(rwc23.models.Game)
admin.site.register(rwc23.models.Prediction)
admin.site.register(rwc23.models.Round)
admin.site.register(rwc23.models.PlayerRound)