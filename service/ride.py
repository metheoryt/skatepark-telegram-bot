from itertools import chain, repeat

from . import ServiceProvider


class HourlyRideProvider(ServiceProvider):

    service_id = 1
    hours = 0

    def set_conditions(self, hours: int):
        self.hours = hours

    def calculate_price(self):
        """Первые 3 часа - по полной стоимости, остальные - по половине"""
        total = 0
        for i in range(1, self.hours + 1):
            if i <= 3:
                total += self.s.base_price
            elif 3 < i:
                total += self.s.base_price / 2
        return total


class HourlyHangoutProvider(HourlyRideProvider):

    service_id = 2


class DailyRideProvider(ServiceProvider):

    service_id = 3
    step_discount = 40
    days = 0

    def set_conditions(self, days: int):
        self.days = days

    def calculate_price(self):
        """Ничто иное, как паки. Если один день - то это, видимо, на сегодня.
        Скидываем фиксу на каждый последующий день, вплоть до фиксы*10
        """
        total = 0
        for i, multiplier in zip(range(self.days), chain(range(0, 10), repeat(10))):
            total += self.s.base_price - self.step_discount * multiplier
        return total

    def __when_paid(self):
        """На самом деле не когда оплачен,
        а когда инвойс выставлен и стал ожидать оплаты.
        Добавить зарезервированных дней,
        если понятно что это будет использоваться сейчас - добавить
        в базу что такой-то клиент сегодня на весь день.
        """
        pass

class DailyHangoutProvider(DailyRideProvider):

    service_id = 4
    step_discount = 20
