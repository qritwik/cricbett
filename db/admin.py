from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Match, Game, Token, Booking, Player, Payment, Wallet

# Register your models here.

admin.site.unregister(Group)

admin.site.site_header = "Cricbett Administration"
admin.site.site_title = "Cricbett Administration"
admin.site.index_title = "Cricbett Administration"


class WalletAdmin(admin.ModelAdmin):
    model = Wallet
    list_display = ['wallet_id', 'wallet_amount', 'pancard', 'pancard_verified']
    list_editable = ['pancard', 'pancard_verified']
    search_fields = ['pancard_verified', 'pancard']

    class Meta:
        verbose_name_plural = "Wallet"


class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = ['id', 'amount', 'payment_status', 'payment_datetime', 'razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature']
    search_fields = ['id', 'payment_status']

    class Meta:
        verbose_name_plural = "Payment"


class GameAdmin(admin.ModelAdmin):
    model = Game
    list_display = ['game_id', 'match', 'game_type', 'game_status', 'team_won', 'first_team_bid_multiplier', 'second_team_bid_multiplier', 'money_saved']
    list_editable = ['game_status', 'team_won', 'first_team_bid_multiplier', 'second_team_bid_multiplier']
    search_fields = ['game_status']

    class Meta:
        verbose_name_plural = "Game"


class TokenAdmin(admin.ModelAdmin):
    model = Token
    list_display = ['token_status', 'token_id', 'token_creation_datetime']
    search_fields = ['token_id']

    class Meta:
        verbose_name_plural = "Token"


class BookingAdmin(admin.ModelAdmin):
    model = Booking
    list_display = ['booking_id', 'player', 'game', 'payment', 'player_bid_price', 'player_bid_team', 'player_bid_multiplier', 'player_won_price', 'is_player_won', 'booking_datetime']
    list_editable = ['is_player_won']
    search_fields = ['player__phone', 'game__game_id']

    class Meta:
        verbose_name_plural = "Booking"


class MatchAdmin(admin.ModelAdmin):
    model = Match
    list_display = ['match_id', 'match_name', 'match_status', 'match_start_datetime', 'match_venue', 'match_type', 'first_team', 'second_team']
    list_editable = ['match_status']
    search_fields = ['match_status', 'match_type']

    class Meta:
        verbose_name_plural = "Match"


class PlayerAdmin(admin.ModelAdmin):
    model = Player
    list_display = ['player_id', 'phone', 'is_phone_verified', 'otp', 'wallet', 'token']
    list_editable = ['is_phone_verified', 'otp']
    search_fields = ['phone']

    class Meta:
        verbose_name_plural = "Player"


admin.site.register(Game, GameAdmin)
admin.site.register(Token, TokenAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Wallet, WalletAdmin)
