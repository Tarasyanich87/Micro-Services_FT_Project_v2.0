# Dashboard UI

This is the main dashboard for the Freqtrade Multi-Bot System.

## Running FreqUI for individual bots

To view the full FreqUI for an individual bot, you need to run it as a separate service. The dashboard will then link to it.

1.  **Clone the official FreqUI repository:**
    ```bash
    git clone https://github.com/freqtrade/frequi.git
    ```

2.  **Install dependencies:**
    ```bash
    cd frequi
    npm install
    ```

3.  **Run FreqUI, pointing to the bot's API:**
    Each bot running in the `trading_gateway` exposes its API on a specific port (e.g., 8080, 8081). You need to start a FreqUI instance for each bot you want to monitor.

    ```bash
    # For a bot running on port 8080
    VITE_API_URL=http://localhost:8080 npm run dev -- --port 9000

    # For a bot running on port 8081
    VITE_API_URL=http://localhost:8081 npm run dev -- --port 9001
    ```

    The dashboard will link to `http://localhost:9000`, `http://localhost:9001`, etc.
