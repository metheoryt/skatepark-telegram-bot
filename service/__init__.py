from abc import ABCMeta, abstractmethod
from decimal import Decimal
from itertools import chain

from ctx import x
from db.models import Service, Client


class MissingServiceError(Exception):
    pass


class ServiceProvider(metaclass=ABCMeta):

    service_id = 0

    def __init__(self):
        self.s = Service.q.get(self.service_id)
        """
        Каждый сервис провайдер популяризуется своим сервисом
        :type: Service
        """
        if not self.s:
            raise MissingServiceError(self.service_id)

    @abstractmethod
    def set_conditions(self, *args, **kwargs):
        """Устанавливает все необходимые условия
        чтобы посчитать цену (для катания например количество часов)
        """
        pass

    @abstractmethod
    def calculate_price(self) -> Decimal:
        """Основная логика рассчёта стоимости.
        Возвращает базовую стоимость услуги без учёта скидок"""
        pass

    @property
    def bill(self):
        """Окончательная цена с прмененем всех скидок"""
        base_price = self.calculate_price()
        actual_price = base_price

        for discount in chain(self.s.actual_discounts, x.client.actual_discounts):
            # рассчитываем процент с полной суммы
            fix_from_percent = base_price * discount.percent
            # отнимаем фиксу и фиксу, посчитанную с процента
            actual_price -= discount.fixed_amount
            actual_price -= fix_from_percent

        return actual_price

    @abstractmethod
    def __when_paid(self):
        """Выполняет действия по оказанию услуги"""
        pass

    def execute_order(self):
        """Выполняет услугу и не позволяет выполнить её ещё раз"""
        self.__when_paid()
        self.__when_paid = self.__already_executed

    @staticmethod
    def __already_executed():
        yield 'Эта услуга уже оказана'
