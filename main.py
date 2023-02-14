import time
from flask import Flask, render_template
from luno_python.client import Client
import pandas as pd
import moment

# credentials = {
#     "api_key_id": "hk9emgy8znzzn",
#     "api_key_secret": "3a-U5RKSp_yfoSxYQTSa95in-GKlDfW7cUeCbGv-8hY"
# }
app = Flask(__name__)
app.config['api_key_id'] = 'hk9emgy8znzzn'
app.config['api_key_secret'] = '3a-U5RKSp_yfoSxYQTSa95in-GKlDfW7cUeCbGv-8hY'

c = Client(api_key_id='hk9emgy8znzzn', api_key_secret='3a-U5RKSp_yfoSxYQTSa95in-GKlDfW7cUeCbGv-8hY')
since = int(time.time() * 1000) - 24 * 60 * 59 * 1000
duration = 300


def to_moment(timestamp):
    return moment.unix(timestamp).format("YYYY-M-D h:m A")


xbt_bal = c.get_balances()[1]
zar_bal = c.get_balances()[-1]

candles = c.get_candles(pair='XBTZAR', since=since, duration=duration)
candles = pd.DataFrame(candles['candles'])
candles = candles.set_index(pd.DatetimeIndex(candles['timestamp'].values))
candles = candles.astype(float)

candles['timestamp'] = candles['timestamp'].apply(to_moment)
candles['ema12'] = candles['close'].ewm(span=12).mean()
candles['ema26'] = candles['close'].ewm(span=26).mean()


def get_ticker():
    try:
        return c.get_ticker(pair='XBTZAR')
    except Exception as err:
        print(err)


def modes(ema12, ema26):
    return 'BUY' if ema12 > ema26 else 'SELL'


@app.route('/')
def index():
    if candles.shape[0] != 0:
        output = {
            'labels': candles['timestamp'].tolist(),
            'values': candles['close'].tolist(),
            'ema12': candles['ema12'].tolist(),
            'ema26': candles['ema26'].tolist(),
            'ema12_price': f'ZAR {candles["ema12"].tolist()[-1]:.0f}',
            'ema26_price': f'ZAR {candles["ema26"].tolist()[-1]:.0f}',
            'closing_price': f'ZAR {candles["close"].tolist()[-1]:.0f}',
            'mode': modes(
                candles["close"].ewm(span=12).mean().tolist()[-1], candles["close"].ewm(span=26).mean().tolist()[-1]
            ),
            'since': moment.unix(since).format("YYYY-M-D h:m A"),
            'duration': duration,
            'xbt_bal': xbt_bal,
            'zar_bal': zar_bal
        }

        return render_template('index.html', **output)


if __name__ == '__main__':
    app.run(debug=True)

    # See PyCharm help at https://www.jetbrains.com/help/pycharm/
