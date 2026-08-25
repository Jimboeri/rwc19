from django.contrib import admin

from .models import Competition, Game, Membership, PlayerRound, Prediction, Round, Team


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ["user", "role", "blocked", "fully_paid", "joined_at"]
    readonly_fields = ["joined_at"]


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "status", "visibility", "created_by", "created_at"]
    list_filter = ["kind", "status", "visibility"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "competition", "role", "blocked", "fully_paid"]
    list_filter = ["competition", "role", "blocked", "fully_paid"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "competition", "pool", "code"]
    list_filter = ["competition"]
    search_fields = ["name"]


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ["name", "competition", "order", "status", "entry_fee"]
    list_filter = ["competition", "status"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ["__str__", "round", "gamedate", "finished", "score1", "score2"]
    list_filter = ["round__competition", "round", "finished"]


@admin.register(PlayerRound)
class PlayerRoundAdmin(admin.ModelAdmin):
    list_display = ["membership", "round", "total_points", "paid", "paid_amount"]
    list_filter = ["round__competition", "round", "paid"]


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ["player_round", "game", "result", "spread", "points", "override"]
    list_filter = ["game__round__competition", "override"]
