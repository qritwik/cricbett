from django.db import models
from .manager import UserManager
from django.contrib.auth.models import AbstractUser


class MatchType(models.TextChoices):
    """
    Enumeration of match types.
    """
    CRICKET = 'CRICKET'
    FOOTBALL = 'FOOTBALL'


class MatchStatus(models.TextChoices):
    """
    Enumeration of game status.
    """
    UPCOMING = 'UPCOMING'
    TOSS_DONE = 'TOSS_DONE'
    LIVE = 'LIVE'
    COMPLETED = 'COMPLETED'


class Match(models.Model):
    """
    Model representing a match.
    """
    match_id = models.AutoField(primary_key=True)
    match_search_id = models.CharField(max_length=255, null=True, blank=True)
    match_name = models.CharField(max_length=255, null=True)
    match_status = models.CharField(max_length=255, choices=MatchStatus.choices, null=True, blank=True)
    match_start_datetime = models.DateTimeField(null=True)
    match_end_datetime = models.DateTimeField(null=True, blank=True)
    match_venue = models.CharField(max_length=255, null=True)
    match_type = models.CharField(max_length=255, choices=MatchType.choices, null=True)
    first_team = models.CharField(max_length=255, null=True, blank=True)
    second_team = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.match_name


class GameType(models.TextChoices):
    """
    Enumeration of game types.
    """
    WIN_PREDICT = 'WIN_PREDICT'
    TOSS_PREDICT = 'TOSS_PREDICT'


class GameStatus(models.TextChoices):
    """
    Enumeration of game status.
    """
    LIVE = 'LIVE'
    COMPLETED = 'COMPLETED'
    UPCOMING = 'UPCOMING'


class Game(models.Model):
    """
    Model representing a game.
    """
    game_id = models.AutoField(primary_key=True)
    game_type = models.CharField(max_length=255, choices=GameType.choices, null=True)
    game_status = models.CharField(max_length=255, choices=GameStatus.choices, null=True)
    team_won = models.CharField(max_length=255, null=True, blank=True)
    first_team_bid_multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    second_team_bid_multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True)
    money_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    money_distributed = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    money_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)

    def __str__(self):
        return f'{self.game_id}'


class TokenStatus(models.TextChoices):
    """
    Enumeration of token status.
    """
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    BLOCKED = 'BLOCKED'


class Token(models.Model):
    """
    Model representing a token.
    """
    token_id = models.CharField(max_length=255, unique=True)
    token_creation_datetime = models.DateTimeField(null=True, blank=True)
    token_expiry_datetime = models.DateTimeField(null=True, blank=True)
    token_status = models.CharField(max_length=255, choices=TokenStatus.choices, null=True, blank=True)

    def __str__(self):
        return f'{self.token_id}'


class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pancard = models.CharField(max_length=255, unique=True, null=True, blank=True)
    pancard_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.wallet_id}'


class Player(AbstractUser):
    """
    Model representing a custom user.
    """
    username = None
    player_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=14, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True)
    objects = UserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone


class PaymentStatus(models.TextChoices):
    """
    Enumeration of game status.
    """
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'
    PENDING = 'PENDING'


class Payment(models.Model):
    """
    Model representing a payment.
    """
    id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=255, choices=PaymentStatus.choices, null=True, blank=True)
    payment_datetime = models.DateTimeField(null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.id}'


class Booking(models.Model):
    """
    Model representing a booking.
    """
    booking_id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    player_bid_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    player_bid_team = models.CharField(max_length=255, null=True, blank=True)
    player_bid_multiplier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    player_won_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_player_won = models.BooleanField(null=True, blank=True)
    booking_datetime = models.DateTimeField(null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.booking_id}'
