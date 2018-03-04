from decimal import Decimal
from sqlalchemy.orm import relationship
import sqlalchemy as sa
import sqlalchemy_utils as su
import enum
from sqlalchemy.ext.hybrid import hybrid_property
from . import Base as _Base, Session


class Base(_Base):
    __abstract__ = True

    q = Session.query_property()


class Client(Base):

    __tablename__ = 'client'
    #  __table_args__ = {'sqlite_autoincrement': True}

    is_admin = sa.Column('is_admin', sa.Boolean, nullable=False, default=False)
    subscribed = sa.Column('subscribed', sa.Boolean, nullable=False, default=True)

    id = sa.Column('id', sa.Integer, primary_key=True)
    """ID клиента для парка"""

    tg_id = sa.Column('telegram_id', sa.Integer, nullable=True, unique=True)
    """ID пользователя в Telegram"""

    first_name = sa.Column('first_name', sa.Text, nullable=False)
    last_name = sa.Column('last_name', sa.Text, nullable=True)

    phone = sa.Column('phone', sa.Text, nullable=True, unique=True)

    parkings = relationship('Parking')
    inventory = relationship('Inventory')
    discounts = relationship('Discount')
    actual_discounts = relationship('Discount', primaryjoin='and_(Client.id==Discount.client_id, '
                                                                            'or_(Discount.date_end==None, '
                                                                            'Discount.date_end > func.now()))')


class Parking(Base):
    """Парковка. Что сейчас на парковке, когда поставлено, до какого числа оплачено"""
    __tablename__ = 'parking'

    id = sa.Column('id', sa.Integer, autoincrement=True, primary_key=True)

    client_id = sa.Column('client_id', sa.Integer, sa.ForeignKey('client.id'), nullable=False)

    inventory_id = sa.Column('inventory_id', sa.Integer, sa.ForeignKey('inventory.id'), nullable=False)

    parking_date = sa.Column('parking_date', su.ArrowType, default=sa.func.now(), nullable=False)
    """Когда был поставлен на парковку"""

    return_date = sa.Column('return_date', su.ArrowType, nullable=True)
    """Когда забрали. Выставляется только по факту возврата"""

    paid_until = sa.Column('paid_until', su.ArrowType, nullable=True)
    """До какого числа оплачено"""

    client = relationship('Client', lazy='joined', uselist=False, back_populates='parkings')
    inventory = relationship('Inventory', lazy='joined', uselist=False, back_populates='parking')

    # __table_args__ = (sa.UniqueConstraint('client_id', 'inventory_id'), )
    # TODO не самая лучшая идея - либо удалять историю, либо обрабатывать constraint программно


class Inventory(Base):
    """Инвентарь. Тип, описание, кому принадлежит"""

    class Type(enum.Enum):
        SKATEBOARD = 'skate'
        BMX = 'bmx'
        SCOOTER = 'scooter'
        OTHER = 'other'

    __tablename__ = 'inventory'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    description = sa.Column(sa.Text)

    type = sa.Column(su.ChoiceType(Type))

    client_id = sa.Column(sa.Integer, sa.ForeignKey('client.id'))

    client = relationship('Client', lazy='joined', uselist=False, back_populates='inventory')

    parking = relationship('Parking', lazy='joined', uselist=False, back_populates='inventory')


class Service(Base):
    """Предоставляемые парком услуги и продукты"""

    __tablename__ = 'service'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    name = sa.Column(sa.Text, nullable=False)

    base_price = sa.Column(sa.Numeric(8, 2))
    """Базовая цена услуги. За что эта цена, определяется непосредственно в ядре услуги"""

    discounts = relationship('Discount', primaryjoin="and_(Service.id==Discount.service_id, "
                                                     "Discount.client_id==None)")
    """Cкидки на этот сервис (без персональных), включая законченные"""
    actual_discounts = relationship(
        'Discount',
        primaryjoin="and_("
                    "Service.id==Discount.service_id, Discount.client_id==None, "
                    "or_("
                    "Discount.date_end==None, Discount.date_end > func.now()"
                    "))")
    """Актуальные скидки на этот сервис"""


class Invoice(Base):

    __tablename__ = 'invoice'

    class Status(enum.IntEnum):
        NEW = 0
        """Создан и ещё не одобрен"""
        AWAITING_PAYMENT = 1
        """Ещё не оплачен"""
        PARTIALLY_PAID = 2
        """Оплачен частично и ожидает доплаты"""
        PAID = 3
        """Оплачен полностью. Равенство суммы платежей и суммы инвойса 
        - не всегда показатель того что инвойс оплачен.
        """
        CANCELLED = 4

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    amount = sa.Column(sa.Numeric(8, 2), nullable=False)

    status = sa.Column(su.ChoiceType(Status, impl=sa.Integer()))

    @hybrid_property
    def paid(self):
        """Сколько уже оплачено"""
        return sum(t.amount for t in self.payments)

    @paid.expression
    def paid(cls):
        return sa.select([sa.func.sum(Payment.amount)]). \
            where(Payment.invoice_id == cls.id). \
            label('paid')

    @hybrid_property
    def debt(self):
        return self.amount - self.paid

    service_id = sa.Column(sa.Integer, sa.ForeignKey('service.id'), nullable=False)
    """Один инвойс может быть выставлен только по одному сервису"""

    payments = relationship('Payment', back_populates='invoice', uselist=True)
    """Платежи, совершённые по этому инвойсу"""


payment_discounts = sa.Table(
    'payment_discounts',
    Base.metadata,
    sa.Column('payment_id', sa.Integer, sa.ForeignKey('payment.id')),
    sa.Column('discount_id', sa.Integer, sa.ForeignKey('discount.id'))
)


class Discount(Base):
    """Скидки по сервисам в целом или персональные"""

    __tablename__ = 'discount'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    client_id = sa.Column(sa.Integer, sa.ForeignKey('client.id'))
    """Если клиент не указан - скидка распространяется на всех"""

    service_id = sa.Column(sa.Integer, sa.ForeignKey('service.id'), nullable=False)

    date_start = sa.Column(su.ArrowType, nullable=False)

    date_end = sa.Column(su.ArrowType, nullable=True)

    fixed_amount = sa.Column(sa.Numeric(10, 2), nullable=False, default=Decimal(0))
    """Фикса может сосуществовать с процентом. Может быть отрицательной"""

    percent = sa.Column(sa.Numeric(4, 2), nullable=False, default=Decimal(0))
    """Процент, выраженный числом. 1 = 100%
    может быть отрицательным, и сосуществовать наравне с фиксой"""

    service = relationship('Service', lazy='joined', uselist=False, back_populates='discounts')
    """Услуга, на которую распространяется скидка"""

    client = relationship('Client', lazy='joined', uselist=False, back_populates='discounts')
    """Если указан - скидка по сервису распространяется только на этого клиента"""

    payments = relationship('Payment', secondary=payment_discounts, back_populates='discounts')
    """Все платежи, совершённые с этой скидкой"""


class Payment(Base):
    """Платежи от клиентов по сервисам, снятия на нужды парка и зарплату"""

    __tablename__ = 'payment'

    class Currency(enum.IntEnum):
        KZT = 398

    class Status(enum.IntEnum):
        NEW = 0
        PAID = 10

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    amount = sa.Column(sa.Numeric(8, 2), nullable=False)
    """Сумма платежа"""

    invoice_id = sa.Column(sa.Integer, sa.ForeignKey('invoice.id'), nullable=False)
    """По какому инвойсу оплата"""

    status = sa.Column(su.ChoiceType(Status, impl=sa.Integer()))
    """Статус платежа. От нового до оплаченного"""

    client_id = sa.Column(sa.Integer, sa.ForeignKey('client.id'), nullable=True)
    """"""

    discounts = relationship('Discount', secondary=payment_discounts, back_populates='payments')

    invoice = relationship('Invoice', back_populates='payments', uselist=False)
