from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
import talib

class PriceHistoryProvider:
    def __init__(self, window_days: int = 120, symbol: str = "AAPL"):
        self.window_days = window_days
        self.end_date = datetime.today()-timedelta(days=-1) # Start yesterday
        self.begin_date = self.end_date-timedelta(days=self.window_days)
        self.init_df = yf.download(symbol, start=self.begin_date, end=self.end_date, progress=False, multi_level_index=False)
        self.df = self.prices()

    def ta_calculator(self):
        try:
            # Overlap Studies
            self.df['MA'] = talib.MA(self.df['Close'], timeperiod=10) #windowed TAs produce lots of null values in demo...
            self.df['EMA'] = talib.EMA(self.df['Close'], timeperiod=10)
            self.df['KAMA'] = talib.KAMA(self.df['Close'], timeperiod=10)
            self.df['WMA'] = talib.WMA(self.df['Close'], timeperiod=10)
            self.df['MidPrice'] = talib.MIDPRICE(self.df['High'], self.df['Low'], timeperiod=10)

            # Momentum Indicator
            self.df['ADX'] = talib.ADX(self.df['High'], self.df['Low'], self.df['Close'],timeperiod=10)
            self.df['BOP'] = talib.BOP(self.df['Open'], self.df['High'], self.df['Low'],self.df['Close'])
            self.df['CMO'] = talib.CMO(self.df['Close'], timeperiod=10)
            self.df['MFI'] = talib.MFI(self.df['High'], self.df['Low'], self.df['Close'],self.df['Volume'])
            self.df['ROC'] = talib.ROC(self.df['Close'], timeperiod=10)
            self.df['WILLR'] = talib.WILLR(self.df['High'], self.df['Low'], self.df['Close'],timeperiod=14)

            # Volume
            self.df['AD'] = talib.AD(self.df['High'], self.df['Low'], self.df['Close'],self.df['Volume'])
            self.df['OBV'] = talib.OBV(self.df['Close'], self.df['Volume'])

            # Volatility
            self.df['NATR'] = talib.NATR(self.df['High'], self.df['Low'], self.df['Close'],timeperiod=14)
            self.df['ATR'] = talib.ATR(self.df['High'], self.df['Low'], self.df['Close'],timeperiod=14)
            self.df['TRANGE'] = talib.TRANGE(self.df['High'], self.df['Low'], self.df['Close'])

            # Misc.
            self.df['RSI'] = talib.HT_TRENDMODE(self.df['Close'])
            self.df['TSF'] = talib.TSF(self.df['Close'], timeperiod=14)
        except Exception as e:
            print("[PriceHistoryProvider] TA computing error.", repr(e))

    def prices(self) -> pd.DataFrame | None:
        print(f"[PriceHistoryProvider] prices() called for.")
        try:
            self.df = self.init_df.copy()
            #self.df = self.df.drop("Volume", axis=1)
            self.ta_calculator()
            #self.df = self.df.dropna()

            if isinstance(self.df, pd.DataFrame) and not self.df.empty:
                # optional timezone normalize
                if hasattr(self.df.index, "tz_localize"):
                    try:
                        self.df.index = self.df.index.tz_localize(None)
                    except Exception:
                        pass
            return self.df
        except Exception as e:
            print("[PriceHistoryProvider] yfinance download error.", repr(e))

hist_price = PriceHistoryProvider(window_days=30, symbol="AAPL")
print("\nReturned DF preview:")
print(hist_price.df)

# missing visualization renderings