# 📊 DCA Entry Discord Bot

Automated Discord bot for daily calculation of buying opportunity scores on ETFs using a DCA (Dollar-Cost Averaging) strategy.

## 📖 Description

This bot analyzes a list of ETF/tickers daily and calculates a composite score based on multiple technical indicators to identify the best entry points for a DCA strategy. Results are automatically sent to Discord via webhook.

### Analyzed Indicators

The composite score (0-100) is calculated from:

- **90-day Drawdown** (25%): Measures the decline from the 90-day high
- **14-day RSI** (25%): Relative Strength Index to identify oversold conditions
- **MA50 Distance** (20%): Gap from the 50-day moving average
- **30-day Momentum** (15%): Price variation over 30 days
- **MA200 Trend** (10%): Position relative to the 200-day moving average
- **20-day Volatility** (5%): Standard deviation of returns over 20 days

### Score Interpretation

- **✅ Score > 55**: Favorable buying opportunity
- **⚠️ Score 45-55**: Neutral zone
- **❌ Score < 45**: Unfavorable conditions

## 🚀 Installation

### Prerequisites

- Docker and Docker Compose
- A configured Discord webhook

### Quick Setup

1. **Clone the repository**

```bash
git clone https://github.com/lukyyy9/dca-entry-discord-bot.git
cd dca-entry-discord-bot
```

2. **Configure the `config.yaml` file**

```yaml
webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"

tickers:
  - "PSP5.PA"    # S&P 500 EUR
  - "SXRT.DE"    # STOXX 600
  - "DCAM.PA"    # MSCI World

data_period: "365d"
timezone: "UTC"

# Weight customization (optional)
weights:
  drawdown90: 0.25
  rsi14: 0.25
  dist_ma50: 0.20
  momentum30: 0.15
  trend_ma200: 0.10
  volatility20: 0.05
```

3. **Start the bot**

```bash
docker compose up -d
```

## 🐳 Docker Usage

### With Docker Compose (recommended)

```bash
# Start the bot
docker compose up -d

# View logs
docker compose logs -f

# Stop the bot
docker compose down
```

### With Docker directly

```bash
docker run -d \
  --name dca-entry-discord-bot \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/data \
  -e TZ=UTC \
  -e DEV=false \
  imluky/dca-entry-discord-bot:latest
```

## ⚙️ Configuration

### Environment Variables

- **`TZ`**: Timezone (default: `UTC`)
- **`DEV`**: Development mode
  - `false`: Daily execution at 22:10 UTC (Mon-Fri)
  - `true`: Execution every minute (testing)

### `config.yaml` Structure

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `webhook_url` | string | Discord webhook URL | **Required** |
| `tickers` | list | List of tickers to analyze | `[]` |
| `data_period` | string | Historical period to retrieve | `365d` |
| `drawdown_cap` | float | Cap to normalize drawdown | `0.25` |
| `volatility_cap` | float | Cap to normalize volatility | `0.10` |
| `output_csv` | string | Historical CSV path | `/data/scores_history.csv` |
| `log_file` | string | Log file path | `/data/bot_daily_score.log` |
| `timezone` | string | Scheduler timezone | `UTC` |
| `weights` | dict | Score component weights | See above |

### Ticker Examples

- **European ETFs**: `PSP5.PA`, `SXRT.DE`, `DCAM.PA`, `PANX.PA`
- **US ETFs**: `SPY`, `QQQ`, `VOO`, `VTI`
- **Crypto**: `BTC-USD`, `ETH-USD`
- **Stocks**: `AAPL`, `MSFT`, `GOOGL`

## 📊 Data and History

### Generated Files

The bot automatically creates in the `data/` folder:

- **`scores_history.csv`**: History of calculated scores
- **`bot_daily_score.log`**: Execution logs

### History CSV Format

```csv
timestamp,ticker,score,close,rsi14,ma50,ma200,drawdown90_pct,vol20_pct,momentum30_pct
2025-11-04T22:10:00+00:00,PSP5.PA,67.5,450.32,42.5,445.20,440.10,5.3,1.2,-2.1
```

## 🔧 Development

### Local Execution without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Modify config path in bot_daily_score.py
# CONFIG_PATH = "config.yaml"  # instead of "/app/config.yaml"

# Launch in DEV mode
export DEV=true
python bot_daily_score.py
```

### Docker Image Build

```bash
docker build -t dca-entry-discord-bot:latest .
```

### Project Structure

```text
dca-entry-discord-bot/
├── bot_daily_score.py      # Main script
├── config.yaml             # Configuration
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image
├── docker-compose.yml     # Orchestration
├── data/                  # Generated data (volumes)
│   ├── scores_history.csv
│   └── bot_daily_score.log
└── README.md
```

## 🔔 Discord Configuration

### Creating a Discord Webhook

1. Open Discord server settings
2. Go to **Integrations** > **Webhooks**
3. Click **New Webhook**
4. Name the webhook (e.g., "DCA Bot")
5. Choose the destination channel
6. Copy the webhook URL
7. Paste the URL in `config.yaml`

### Message Format

The bot sends a structured message with:

- Report date
- List of analyzed tickers
- Composite score with emoji (✅/⚠️/❌)
- Current price
- RSI
- Moving averages (MA50, MA200)

## 📝 Important Notes

⚠️ **Warning**: This bot is a decision support tool. The calculated scores do not constitute financial advice in any way.

### Limitations

- Data comes from Yahoo Finance (possible delay)
- Scores are based solely on technical analysis
- Past market performance does not predict future results
- Some tickers may have incomplete data