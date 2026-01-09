# Import all models here so that Alembic can find them
from app.db.base_class import Base  # noqa
from app.domains.identity.models import User, UserProfile  # noqa
from app.domains.vibes.models import Video  # noqa
from app.domains.referrals.models import Referral  # noqa
from app.domains.payments.models import TransactionLedger  # noqa
