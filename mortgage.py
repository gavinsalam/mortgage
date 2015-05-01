#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import argparse
import decimal

MONTHS_IN_YEAR = 12
DOLLAR_QUANTIZE = decimal.Decimal('.01')

def dollar(f, round=decimal.ROUND_CEILING):
    """
    This function rounds the passed float to 2 decimal places.
    """
    if not isinstance(f, decimal.Decimal):
        f = decimal.Decimal(str(f))
    return f.quantize(DOLLAR_QUANTIZE, rounding=round)

class InputError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg
        print("Input error: {0:s}\n".format(msg))

class Mortgage:
    def __init__(self, interest, months = None, amount = 100000, years = None):
        self._interest = float(interest)
        self._months = self.__months(months,years)
        self._amount = dollar(amount)
        
    def rate(self):
        return self._interest

    def month_growth(self):
        return 1. + self._interest / MONTHS_IN_YEAR

    def apy(self):
        return self.month_growth() ** MONTHS_IN_YEAR - 1

    def loan_years(self):
        return float(self._months) / MONTHS_IN_YEAR

    def loan_months(self):
        return self._months

    def amount(self):
        return self._amount

    def monthly_payment(self):
        pre_amt = float(self.amount()) * self.rate() / (float(MONTHS_IN_YEAR) * (1.-(1./self.month_growth()) ** self.loan_months()))
        return dollar(pre_amt, round=decimal.ROUND_CEILING)

    def total_value(self, m_payment):
        "Returns the amount that you could borrow today, given a monthly payment of m_payment (taking duration and interest rate from class)"
        return m_payment / self.rate() * (float(MONTHS_IN_YEAR) * (1.-(1./self.month_growth()) ** self.loan_months()))

    def annual_payment(self):
        return self.monthly_payment() * MONTHS_IN_YEAR

    def total_payout(self):
        return self.monthly_payment() * self.loan_months()

    def total_cost(self, months=None, years=None):
        """
        Returns the total payout minus the initial amount. 

        By default to end of mortgage, or if months/years specified, then
        to the that point in time
        """
        if (months == None and years == None):
            m_months = self.loan_months()
        else:
            m_months = self.__months(months,years)

        return (self.monthly_payment() * m_months - (self.amount() - self.balance(m_months)))

    def balance(self, months=None, years=None):
        """
        Returns the balance after a given number of months (including last month's payment)
        Note that it doesn't take into account rounding, so can differ from exact
        calculation with rounding each month
        """
        m_months = self.__months(months,years)

        # approach to calculating this that doesn't account for rounding
        # work out total owed, assuming no monthly payment
        total_at_date = float(self.amount())*self.month_growth()**m_months 
        # work out total paid, inflating it by interest for each month that passes after payment
        total_paid    = float(self.monthly_payment())*(1-self.month_growth()**m_months)/(1-self.month_growth())
        # the difference is the balance
        return  dollar(total_at_date - total_paid)

    def monthly_payment_schedule(self):
        monthly = self.monthly_payment()
        balance = dollar(self.amount())
        rate = decimal.Decimal(str(self.rate())).quantize(decimal.Decimal('.000001'))
        while True:
            interest_unrounded = balance * rate * decimal.Decimal(1)/MONTHS_IN_YEAR
            interest = dollar(interest_unrounded, round=decimal.ROUND_HALF_UP)
            if monthly >= balance + interest:
                yield balance, interest
                break
            principle = monthly - interest
            yield principle, interest
            balance -= principle

    def __months(self, months = None, years = None):
        "Internal routine to parse arguments with months or years; returns an integer number of months"
        if (months != None):
            if (years != None): raise InputError("years cannot be specified together with months")
            return int(months)
        elif (years != None):
            return int(years*MONTHS_IN_YEAR)
        else:
            raise InputError("months or years must be specified")


            
def print_summary(m):
    print('{0:>25s}:  {1:>12.6f}'.format('Rate', m.rate()))
    print('{0:>25s}:  {1:>12.6f}'.format('Month Growth', m.month_growth()))
    print('{0:>25s}:  {1:>12.6f}'.format('APY', m.apy()))
    print('{0:>25s}:  {1:>12.0f}'.format('Payoff Years', m.loan_years()))
    print('{0:>25s}:  {1:>12.0f}'.format('Payoff Months', m.loan_months()))
    print('{0:>25s}:  {1:>12.2f}'.format('Amount', m.amount()))
    print('{0:>25s}:  {1:>12.2f}'.format('Monthly Payment', m.monthly_payment()))
    print('{0:>25s}:  {1:>12.2f}'.format('Annual Payment', m.annual_payment()))
    print('{0:>25s}:  {1:>12.2f}'.format('Total Payout', m.total_payout()))
    print('{0:>25s}:  {1:>12.2f}'.format('Total Cost', m.total_cost()))

def print_schedule_summary(m):
    output_format ='{0:>5d} {1:>12.2f} {2:>12.2f} {3:>12.2f}'
    header_format = output_format.replace('.2f','s').replace('d','s')

    print ("\n\nSummary of repayment schedule")
    print(header_format.format("year","balance","paid","net cost"))
    nyears = int(m.loan_years())
    for y in range(0, (nyears+1)):
        balance = m.balance(y*MONTHS_IN_YEAR)
        paid = m.monthly_payment()*y*MONTHS_IN_YEAR
        print (output_format.format(y, balance, paid, balance + paid - m.amount()))

    
def main():
    parser = argparse.ArgumentParser(description='Mortgage Amortization Tools')
    parser.add_argument('-i', '--interest', default=6, dest='interest')
    parser.add_argument('-y', '--loan-years', default=30, dest='years')
    parser.add_argument('-m', '--loan-months', default=None, dest='months')
    parser.add_argument('-a', '--amount', default=100000, dest='amount')
    parser.add_argument('-s', '--schedule-summary', action="store_true", dest='schedule_summary')
    args = parser.parse_args()

    interest = float(args.interest) / 100
    
    if args.months:
        m = Mortgage(interest, float(args.months), args.amount)
    else:
        m = Mortgage(interest, float(args.years) * MONTHS_IN_YEAR, args.amount)

    print_summary(m)

    if (args.schedule_summary):
        print_schedule_summary(m)
    
if __name__ == '__main__':
    main()
