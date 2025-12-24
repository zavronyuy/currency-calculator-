# currency_calculator.py - Advanced Currency Calculator SaaS with Charts, Sounds, and Backend

from flask import Flask, request, render_template_string, jsonify
import requests
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('conversions.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY,
        amount REAL,
        from_currency TEXT,
        to_currency TEXT,
        result REAL,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# Function to get exchange rates
def get_rates():
    try:
        # Fiat currencies
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        rates = data['rates']
        # Add cryptos from CoinGecko
        crypto_ids = "bitcoin,ethereum,solana,ripple"  # BTC, ETH, SOL, XRP
        crypto_response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=usd")
        crypto_data = crypto_response.json()
        rates['BTC'] = 1 / crypto_data['bitcoin']['usd']
        rates['ETH'] = 1 / crypto_data['ethereum']['usd']
        rates['SOL'] = 1 / crypto_data['solana']['usd']
        rates['XRP'] = 1 / crypto_data['ripple']['usd']
        # Add metals from metals.live
        metals_response = requests.get("https://api.metals.live/v1/spot")
        metals_data = metals_response.json()
        for metal in metals_data:
            if metal['metal'] == 'gold':
                rates['GOLD'] = metal['price']
            elif metal['metal'] == 'silver':
                rates['SILVER'] = metal['price']
        return rates
    except:
        # Fallback rates (approximate current as of Dec 2025)
        return {
            'USD': 1,
            'EUR': 0.92,
            'PKR': 285,
            'BTC': 0.0000105,  # 1 / 95000
            'ETH': 0.000312,   # 1 / 3200
            'SOL': 0.00556,    # 1 / 180
            'XRP': 1.25,       # 1 / 0.8
            'GOLD': 2100,
            'SILVER': 28
        }

def save_conversion(amount, from_currency, to_currency, result):
    conn = sqlite3.connect('conversions.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO history (amount, from_currency, to_currency, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                (amount, from_currency, to_currency, result, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('conversions.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    return rows

# HTML/CSS/JS template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
    <title>Currency Calculator SaaS</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 400% 400%;
            animation: gradientShift 10s ease infinite;
            color: white;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .container {
            background: rgba(255, 255, 255, 0.15);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            max-width: 600px;
            width: 100%;
            animation: fadeIn 1s ease-in;
        }
        h1 {
            margin-bottom: 20px;
            font-size: 2.8em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        form {
            margin-bottom: 20px;
        }
        input, select, button {
            padding: 12px;
            margin: 8px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            font-size: 1.1em;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        select {
            background: linear-gradient(45deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.2));
            cursor: pointer;
            position: relative;
        }
        select:hover {
            border-color: #ffeb3b;
            box-shadow: 0 0 15px rgba(255, 235, 59, 0.5);
            transform: scale(1.05);
        }
        select:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 20px rgba(76, 175, 80, 0.7);
            animation: rainbowBorder 2s infinite;
        }
        @keyframes rainbowBorder {
            0% { border-color: red; }
            16% { border-color: orange; }
            33% { border-color: yellow; }
            50% { border-color: green; }
            66% { border-color: blue; }
            83% { border-color: indigo; }
            100% { border-color: violet; }
        }
        option {
            background: #333;
            color: white;
            padding: 10px;
        }
        input:focus, select:focus {
            outline: none;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }
        button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: linear-gradient(45deg, #45a049, #4CAF50);
            transform: scale(1.1);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        #loading {
            font-size: 1.2em;
            color: yellow;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .result {
            font-size: 1.8em;
            margin-top: 20px;
            animation: slideIn 0.6s ease-out, glow 2s infinite alternate;
        }
        @keyframes slideIn {
            from { transform: translateY(30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .link {
            color: #fff;
            text-decoration: none;
            font-weight: bold;
            transition: color 0.3s;
        }
        .link:hover {
            color: #ffeb3b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Advanced Currency Calculator</h1>
        <p>Convert fiat, crypto, and precious metals with real-time rates!</p>
        <form method="POST" id="convertForm">
            <input type="number" step="0.01" name="amount" placeholder="Amount" required>
            <select name="from_currency">
                <option value="USD">USD (Dollar)</option>
                <option value="EUR">EUR (Euro)</option>
                <option value="PKR">PKR (Pakistani Rupee)</option>
                <option value="BTC">BTC (Bitcoin)</option>
                <option value="ETH">ETH (Ethereum)</option>
                <option value="SOL">SOL (Solana)</option>
                <option value="XRP">XRP (Ripple)</option>
                <option value="GOLD">GOLD (Gold oz)</option>
                <option value="SILVER">SILVER (Silver oz)</option>
            </select>
            to
            <select name="to_currency">
                <option value="USD">USD (Dollar)</option>
                <option value="EUR">EUR (Euro)</option>
                <option value="PKR">PKR (Pakistani Rupee)</option>
                <option value="BTC">BTC (Bitcoin)</option>
                <option value="ETH">ETH (Ethereum)</option>
                <option value="SOL">SOL (Solana)</option>
                <option value="XRP">XRP (Ripple)</option>
                <option value="GOLD">GOLD (Gold oz)</option>
                <option value="SILVER">SILVER (Silver oz)</option>
            </select>
            <br>
            <button type="submit" id="convertBtn">Convert 🚀</button>
        </form>
        <div id="loading" style="display: none;">Loading... ⏳</div>
        {% if result %}
        <div class="result">
            <strong>{{ amount }} {{ from_currency }} = {{ result }} {{ to_currency }}</strong>
        </div>
        <script>document.getElementById('successSound').play();</script>
        {% endif %}
        <br>
        <a href="/history" class="link">View Conversion History 📊</a>
        <button onclick="location.reload()" class="link">Refresh Rates 🔄</button>
    </div>
    <!-- Sound effect -->
    <audio id="successSound" src="https://www.soundjay.com/misc/sounds/bell-ringing-05.wav" preload="auto"></audio>
    <script src="/service-worker.js"></script>
    <script>
        document.getElementById('convertForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('convertBtn').disabled = true;
            document.getElementById('convertBtn').textContent = 'Converting...';
        });

        // Enhanced animations and dynamic colors
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('.container');
            container.style.transform = 'scale(0.9) rotate(-2deg)';
            setTimeout(() => {
                container.style.transition = 'transform 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
                container.style.transform = 'scale(1) rotate(0deg)';
            }, 200);

            // Add sparkle effect to button
            const btn = document.getElementById('convertBtn');
            btn.addEventListener('mouseenter', function() {
                this.style.boxShadow = '0 0 20px rgba(255, 255, 255, 0.8)';
            });
            btn.addEventListener('mouseleave', function() {
                this.style.boxShadow = '';
            });

            // Dynamic background change based on currency selection
            const selects = document.querySelectorAll('select');
            const body = document.body;
            const currencyColors = {
                'USD': '#667eea',
                'EUR': '#764ba2',
                'PKR': '#f093fb',
                'BTC': '#ffeb3b',
                'ETH': '#4CAF50',
                'SOL': '#2196F3',
                'XRP': '#FF9800',
                'GOLD': '#FFD700',
                'SILVER': '#C0C0C0'
            };

            selects.forEach(select => {
                select.addEventListener('change', function() {
                    const selected = this.value;
                    if (currencyColors[selected]) {
                        body.style.background = `linear-gradient(135deg, ${currencyColors[selected]} 0%, #764ba2 100%)`;
                        body.style.animation = 'gradientShift 5s ease infinite';
                    }
                });
            });

            // Add floating particles effect
            for (let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 10 + 's';
                document.body.appendChild(particle);
            }
        });
    </script>
    <style>
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            animation: float 10s linear infinite;
            top: 100vh;
        }
        @keyframes float {
            to { transform: translateY(-100vh); }
        }
    </style>
</body>
</html>
"""

history_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversion History</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f2f2f2; }
        .chart-container { margin-top: 20px; }
        a { display: block; text-align: center; margin-top: 20px; color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Conversion History 📈</h1>
        <table>
            <tr><th>ID</th><th>Amount</th><th>From</th><th>To</th><th>Result</th><th>Time</th></tr>
            {% for row in history %}
            <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td><td>{{ row[4] }}</td><td>{{ row[5] }}</td></tr>
            {% endfor %}
        </table>
        <div class="chart-container">
            <canvas id="historyChart"></canvas>
        </div>
        <a href="/">Back to Calculator</a>
    </div>
    <script>
        const ctx = document.getElementById('historyChart').getContext('2d');
        const history = {{ history|tojson }};
        const labels = history.map(row => row[5]);
        const data = history.map(row => row[4]);
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Conversion Results',
                    data: data,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: { responsive: true }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    amount = None
    from_currency = None
    to_currency = None
    if request.method == 'POST':
        amount = float(request.form['amount'])
        from_currency = request.form['from_currency']
        to_currency = request.form['to_currency']
        rates = get_rates()
        if from_currency in rates and to_currency in rates:
            # Convert to USD first, then to target
            usd_amount = amount / rates[from_currency]
            result = usd_amount * rates[to_currency]
            result = round(result, 4)
            # Save to database
            save_conversion(amount, from_currency, to_currency, result)
    return render_template_string(html_template, result=result, amount=amount, from_currency=from_currency, to_currency=to_currency)

@app.route('/history')
def history():
    history_data = get_history()
    return render_template_string(history_template, history=history_data)

@app.route('/api/rates')
def api_rates():
    rates = get_rates()
    return jsonify(rates)

@app.route('/rates')
def rates_page():
    rates = get_rates()
    return render_template_string(rates_template, rates=rates)

rates_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Current Rates</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; }
        ul { list-style: none; padding: 0; }
        li { padding: 10px; border-bottom: 1px solid #ddd; }
        a { display: block; text-align: center; margin-top: 20px; color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Current Exchange Rates 💱</h1>
        <p>Rates relative to USD (1 USD = ?)</p>
        <ul>
            {% for currency, rate in rates.items() %}
            <li><strong>{{ currency }}</strong>: {{ "%.4f"|format(rate) }}</li>
            {% endfor %}
        </ul>
        <a href="/">Back to Calculator</a>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)