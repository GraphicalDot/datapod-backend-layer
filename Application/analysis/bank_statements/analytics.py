


import copy
from dateutil import parser


class Analytics(object):
    def __init__(self):
        pass
    

    @staticmethod
    def data_consolidation(data):
        """
        So all the data parsed from bank statements hdfc might have duplicate months data 
        and wwe will have data in the format of lists of lists with each list being 
        a transaction detail, the keys of a each list in this list will be 
        [month, year, trans_hash,  narration, 
            'Chq. / Ref No.', 'Value Date', 'Withdrawal Amount', 
            'Deposit Amount', 'Closing Balance*']

        Now we have to create a dictionary with keys being the year, and it will have twleve keys 
        for each month and then each month will have a list.
        The list shall be checked for duplicate transactions
        
        
        Note: Different accounts with same bank and different accounts will not 
        be checked, as it doesnt matter in the overall account financial history
        """    
        formatted_data = {}    
        for (month, year, trans_hash, narr, chq, date, withdrawl, deposit, balance) in data: 
            entry = (month, year, trans_hash, narr, chq, date, withdrawl, deposit, balance) 
            if not formatted_data.get(year): 
                formatted_data.update({year: {month: {trans_hash: entry}  } }) 
            else: 
                ##month is not present but year is present 
                if not formatted_data[year].get(month): 
                    formatted_data[year].update({month: {trans_hash: entry}}) 
                else: 
                    ##both year and month is present                   
                    ##if trans hash is already present 
                    if formatted_data[year][month].get(trans_hash): 
                        print (f"Dupplicate entry found {entry}") 
                    else: 
                        formatted_data[year][month].update({trans_hash: entry})                                                                      


        return formatted_data


    @staticmethod
    def total_num_n_amt_transc(formatted_data, column_number):
        """
        Generally column number is 7
        Column number is the column which is the deposit amount transactions
        Return:
            Number of credit transactions
            {'2018': {'12': (9, 30092.16)},
            '2019': {'01': (24, 100036.7),
            '02': (10, 60243.0),
            '03': (32, 22954.829999999994),
            '04': (20, 33434.6)}}

        """
        def calculate(month_data, column_number):
            """
            Transaction dict for a particular month of particular year, 
            each key of dict is the hash of the transaction (all keys combined)
            """
            data = []
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            for e in month_data_arr:
                try:
                    if float(e[column_number].replace(',',''))  != 0.0:
                        data.append(float(e[column_number].replace(',','')))
                except:
                    pass
            
            return len(data), sum(data)

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)


        return result





    @staticmethod
    def total_num_cash_deposit():
        pass

    @staticmethod
    def total_amount_cash_deposit():
        pass
    

    @staticmethod
    def total_num_n_amt_cash_withdrawl(formatted_data, column_number):
        def calculate(month_data, column_number):
            """
            Generally column number is 6
            Transaction dict for a particular month of particular year, 
            each key of dict is the hash of the transaction (all keys combined)
            {'2018': {'10': (5, 4000.0),
            '11': (8, 11000.0),
            '12': (6, 5500.0),
            '09': (2, 2000.0)},
            '2019': {'01': (5, 10000.0),
            '02': (3, 7000.0),
            '03': (4, 6000.0),
            '04': (1, 1000.0)},
            '2017\n20': {'08': (0, 0)}}

            """
            data = []
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            for e in month_data_arr:
                try:
                 if e[3].find("ATW") ==0 or e[3].find("EAW") == 0: 
                        data.append(float(e[column_number].replace(',','')))
                except:
                    pass
            
            return len(data), sum(data)

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)


        return result


    
    
    @staticmethod
    def total_num_bounced():
        pass

    @staticmethod
    def total_amount_bounced():
        pass
    
    @staticmethod
    def balance_on_date(day, formatted_data, column_number):

        def nearest(items, pivot):
            return min(items, key=lambda x: abs(x - pivot))

        def calculate(month_data, column_number):
            """
            Generally column number is 6
            Transaction dict for a particular month of particular year, 
            each key of dict is the hash of the transaction (all keys combined)
            {'2018': {'10': (5, 4000.0),
            '11': (8, 11000.0),
            '12': (6, 5500.0),
            '09': (2, 2000.0)},
            '2019': {'01': (5, 10000.0),
            '02': (3, 7000.0),
            '03': (4, 6000.0),
            '04': (1, 1000.0)},
            '2017\n20': {'08': (0, 0)}}

            """
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            pivot = parser.parse(f"{day}/{month_data_arr[0][0]}/{month_data_arr[0][1]}")

            items = []
            for item in month_data_arr:
                try:
                    items.append(parser.parse(item[5]))
                except :
                    continue

            if items:

                r_day = nearest(items, pivot).day

                if r_day == int(day):
                    return [e for e in month_data_arr if int(e[5].split("/")[0]) == int(day)][-1][-1]
                else:
                    return [e for e in month_data_arr if int(e[5].split("/")[0]) ==int(day)][0][-1]

            return 0

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)

        return result



    @staticmethod
    def balance_on_tenth(formatted_data, column_number):
        return Analytics.balance_on_date("10", formatted_data, column_number)

    @staticmethod
    def balance_on_twentieth(formatted_data, column_number):
        return Analytics.balance_on_date("20", formatted_data, column_number)
        
    
    @staticmethod
    def total_inward_cheque_bounces():
        pass
    
    @staticmethod
    def total_outward_cheque_bounces():
        pass
    
    @staticmethod
    def acc_balance(formatted_data, column_number, max_or_min):
        def calculate(month_data, column_number):
            """
            Generally column number is 6
            Transaction dict for a particular month of particular year, 
            each key of dict is the hash of the transaction (all keys combined)
           {'2018': {'10': 95402.78, '11': 94585.08, '12': 110822.92, '09': 29133.9},
            '2019': {'01': 94268.76, '02': 51635.0, '03': 107194.06, '04': 30231.23},
            '2017\n20': {'08': 15461.05}}



            """
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            data = []

            for item in month_data_arr:
                try:
                    balance = float(item[column_number].replace(',',''))
                except:
                    try:
                        ##to hanle last balaces like '6578.46\nRequesting Branch code : SYSTEM'
                        ##generally at the end of PDF
                        balance = item[column_number].split("\n")[0]
                        balance = float(balance.replace(',',''))
                    except:
                        balance = 0
                data.append(balance)
            if max_or_min == "max":
                return max(data)
            elif max_or_min== "min":
                return min(data)
            else:
                ##return average
                return float(sum(data))/len(data)

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)

        return result


    @staticmethod
    def min_eod_balance(formatted_data, column_number):
        return Analytics.acc_balance(formatted_data, column_number, "min")

    @staticmethod
    def max_eod_balance(formatted_data, column_number):
        return Analytics.acc_balance(formatted_data, column_number, "max")

    
    @staticmethod
    def average_eod_balance(formatted_data, column_number):
        return Analytics.acc_balance(formatted_data, column_number, None)
        
    
    @staticmethod
    def opening_balance(formatted_data, column_number):
        def calculate(month_data, column_number):
           
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            sorted(month_data_arr, key=lambda x: x[5])
            return month_data_arr[0][column_number]           

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)

        return result


    
    @staticmethod
    def closing_balance(formatted_data, column_number):
        def calculate(month_data, column_number):
           
            month_data_arr = list(month_data.values())
            #data = [float(e[column_number].replace(',','')) for e in month_data_arr if float(e[column_number].replace(',',''))  != 0.0]
            sorted(month_data_arr, key=lambda x: x[5])
            return month_data_arr[-1][column_number]           

        result  = copy.deepcopy(formatted_data) 
        for year in formatted_data.keys(): 
            for month in formatted_data[year].keys(): 
                month_data = result[year].pop(month)
                result[year][month] = calculate(month_data, column_number)

        return result
    
    @staticmethod
    def total_loans():
        pass
    

    @staticmethod
    def total_loan_amount():
        pass



